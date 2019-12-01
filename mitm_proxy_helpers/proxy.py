''' MITM Proxy client module '''
from __future__ import print_function
import os
import time
import select
import shutil

import paramiko

from mitm_proxy_helpers import mitmutil


class InvalidPathException(Exception):
    ''' Continues if an invalid path is encountered in '''


class InvalidPlatformException(Exception):
    ''' Continues if an invalid platform is encountered '''


class Proxy:
    # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """
    The Proxy Handler can start and stop mitmproxy server locally or on a server
    and run the proxy server with different scripts (har logging,
    blacklisting)
    """
    ulimit_s = '1024'  # OS 'ulmit -s' value

    def __init__(self):
        self.har_log = None
        self.host = os.getenv('mitm_server_host', mitmutil.proxy_host())
        self.ssh_port = os.getenv('mitm_server_ssh_port', None)
        self.ssh_user = os.getenv('mitm_server_ssh_user', None)
        self.remote = None not in [self.ssh_port, self.ssh_user]
        self.ssh_password = os.getenv('mitm_server_ssh_password', None)
        self.interface = os.getenv('mitm_server_interface', 'eth0')
        self.proxy_port = int(os.getenv('mitm_proxy_listen_port', '8081'))
        self.har_path = os.getenv('mitm_har_path', 'logs/har/dump.har')
        self.python3_path = os.getenv('mitm_python3_path', shutil.which('python3'))
        self.path_to_scripts = 'server_scripts'
        if self.remote is True:
            self.path_to_scripts = "/home/{0}/mitm".format(self.ssh_user)
        self.fixtures_dir = os.getenv(
            'fixtures_dir',
            "{0}/fixtures".format(self.path_to_scripts))
        # Custom scripts
        self.har_dump_path = os.getenv('har_dump_script_path',
                                       "{0}/har_dump.py".format(
                                           self.path_to_scripts))
        self.blacklister_path = os.getenv('blacklister_script_path',
                                          "{0}/blacklister.py".format(
                                              self.path_to_scripts))
        self.empty_response_path = os.getenv('empty_response_script_path',
                                             "{0}/empty_response.py".format(
                                                 self.path_to_scripts))
        self.har_blacklist_path = os.getenv('har_blacklist_script_path',
                                            "{0}/har_dump_and_blacklister.py".format(
                                                self.path_to_scripts))
        self.json_resp_rewrite_path = os.getenv(
            'json_resp_rewrite_script_path',
            "{0}/json_response_field_rewriter.py".format(self.path_to_scripts))
        self.response_replace_path = os.getenv('response_replace_script_path',
                                               "{0}/response_replace.py".format(
                                                   self.path_to_scripts))
        self.request_throttle_path = os.getenv('request_throttle_script_path',
                                               "{0}/request_throttle.py".format(
                                                   self.path_to_scripts))
        self.har_dump_no_replace_path = os.getenv('har_dump_no_replace_path',
                                                  "{0}/har_dump_no_replace.py".format(
                                                      self.path_to_scripts))

        if not all([self.host, self.ssh_port, self.ssh_user,
                    self.ssh_password, self.har_path, self.python3_path,
                    self.har_dump_path, self.blacklister_path,
                    self.empty_response_path,
                    self.json_resp_rewrite_path,
                    self.response_replace_path,
                    self.request_throttle_path,
                    self.har_dump_no_replace_path]) and self.remote:
            raise Exception('Not all remote MITM proxy env variables were provided.')
        if not all([self.host, self.har_path, self.python3_path,
                    self.har_dump_path, self.blacklister_path,
                    self.empty_response_path,
                    self.json_resp_rewrite_path,
                    self.response_replace_path,
                    self.request_throttle_path,
                    self.har_dump_no_replace_path]):
            raise Exception('Not all local MITM proxy env variables were provided.')

        if not self.har_path.endswith('.har'):
            raise InvalidPathException(
                'har_path is not a valid path to a HAR file')

    def har(self):
        '''
        To retrieve the har file, we need to stop the proxy dump which writes out
        the har, fetch the har file, load it into the har_log attribute,
        then delete the har file once it is read and restart the proxy
        '''
        self.stop_proxy()
        self.har_log = self.fetch_har()
        self.delete_har()
        self.start_proxy()
        return self.har_log

    def ssh_command(self, command, max_attempts=1):
        """ Execute arbitrary SSH commmand on a remote host, use with caution """
        retry_wait = 2
        error_str = "SSHException. Could not SSH to {0} error: {1}"
        for i in range(max_attempts):
            print("Trying to connect to {0} (Attempt {1}/{2})".format(
                self.host, i + 1, max_attempts))
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(
                    self.host, port=int(self.ssh_port), username=self.ssh_user,
                    password=self.ssh_password)
                print("Connected to {}".format(self.host))
                break
            except paramiko.ssh_exception.SSHException as err:
                print(error_str.format(self.host, err))
                time.sleep(retry_wait)
            except paramiko.ssh_exception.NoValidConnectionsError as err:
                print(error_str.format(self.host, err))
                time.sleep(retry_wait)
        else:
            print("Could not connect to {0} after {1} attempts. "
                  "Giving up".format(self.host, i + 1))
            return

        # Send the command (non-blocking)
        print("Running command: {}".format(command))
        _, stdout, _ = ssh.exec_command(command)

        # Wait for the command to terminate
        while not stdout.channel.exit_status_ready():
            # Only print data if there is data to read in the channel
            if stdout.channel.recv_ready():
                rldc, _, _ = select.select([stdout.channel], [], [], 0.0)
                if len(rldc) > 0:
                    # Print data from stdout
                    print(stdout.channel.recv(1024))

    def run_command(self, command, max_attempts=1):
        """ Executes a command locally or remotely """
        if self.remote is True:
            self.ssh_command(command, max_attempts)
        else:
            os.system(command)

    def start_proxy(self, script=None, config=None):
        """ Start a proxy with optional script and script config """
        wait = 5
        if self.remote is True:
            wait = 20
        ignore_hostname = os.getenv('proxy_hostname_ignore', '')

        config = config or {}
        script_path = None
        status_code = ''
        if not script:
            script = 'har_logging'

        if script == 'har_logging':
            print('Starting mitmdump proxy server with har logging')
            script_path = self.har_dump_path
        elif script == 'blacklist':
            print('Starting mitmdump proxy server with blacklisting script')
            script_path = self.blacklister_path
            status_code = '403'
        elif script == 'empty_response':
            print('Starting mitmdump proxy server with empty response script')
            script_path = self.empty_response_path
        elif script == 'har_and_blacklist':
            print('Starting mitmdump proxy server with blacklisting and '
                  'har logging script')
            script_path = self.har_blacklist_path
            status_code = '403'
        elif script == 'json_resp_field_rewriter':
            print('Starting mitmdump proxy server with json response'
                  'field rewrite script enabled')
            script_path = self.json_resp_rewrite_path
        elif script == 'response_replace':
            print('Starting mitmdump proxy server with response'
                  'replace script enabled')
            script_path = self.response_replace_path
        elif script == 'request_throttle':
            print('Starting mitmdump proxy server with request throttle '
                  'enabled ')
            script_path = self.request_throttle_path
        elif script == 'har_logging_no_replace':
            print('Starting mitmdump proxy server with har logging, no replace')
            script_path = self.har_dump_no_replace_path
        else:
            raise Exception('Unknown proxy script provided.')

        fixture_path = self.fixtures_dir + config.get('fixture_file', '')
        fixture_path_two = self.fixtures_dir + config.get('fixture_file_two', '')
        command = ("python {0}/proxy_launcher.py "
                   "--ulimit={1} --python3_path={2} --har_dump_path={3} "
                   "--har_path={4} --proxy_port={5} --script_path={6} "
                   .format(
                       self.path_to_scripts, self.ulimit_s, self.python3_path,
                       self.har_dump_path, self.har_path, self.proxy_port, script_path))
        if self.remote is True:
            command = "{0} --mode=transparent".format(command)
        command = ("{0} "
                   "--status_code={1} "
                   "--field_name={2} --field_value='{3}' "
                   "--partial_url='{4}' --partial_url_2='{5}' "
                   "--fixture_path='{6}' --fixture_path_2='{7}' "
                   "--run_identifier='{8}' "
                   "--ignore_hostname={9} &"
                   .format(
                       command,
                       config.get('status_code', status_code),
                       config.get('field_name', ''),
                       config.get('field_value', ''),
                       config.get('partial_url', ''),
                       config.get('partial_url_2', ''),
                       fixture_path,
                       fixture_path_two,
                       config.get('run_identifier', ''),
                       ignore_hostname))
        self.run_command(command)
        print("Waiting for {0}s after proxy start".format(wait))
        time.sleep(wait)

    @staticmethod
    def pids():
        """ Returns pids of all mitm proxy instances running """
        stream = os.popen("ps aux | grep '[m]itm' | awk '{print $2}'")
        return stream.read()

    def stop_proxy(self):
        """ Stop the proxy server """
        print('Stopping MITM proxy server')
        if self.remote is True:
            command = "echo '{0}' | sudo killall {1}".format(
                self.ssh_password, os.path.basename(self.python3_path))
        else:
            mitm_pids = self.pids()
            if mitm_pids:
                command = "kill {0}".format(' '.join(mitm_pids.split("\n")))
        self.run_command(command)

    def set_ip_routing(self):
        """ Set IP routing on the host machine so that incoming http
        requests on port 80 get redirected to the proxy port
        Supports: Linux
        """
        os_type = os.getenv('server_os_type', None)
        if self.remote is not True and os_type not in ['Linux']:
            return

        print('Setting IP forwarding and iptables rules on {} host'.format(
            os_type))

        command = (
            "echo '{0}' | sudo -S sysctl -w net.ipv4.ip_forward=1 && "
            "echo '{0}' | sudo -S sysctl -w net.ipv6.conf.all.forwarding=1 && "
            "echo '{0}' | sudo -S sysctl -w net.ipv4.conf.all.send_redirects=0 "
            "&& echo '{0}' | sudo -S iptables -t nat -A PREROUTING -i {1} -p "
            "tcp --dport 80 -j REDIRECT --to-port {2} && "
            "echo '{0}' | sudo -S ip6tables -t nat -A PREROUTING -i {1} -p tcp "
            "--dport 80 -j REDIRECT --to-port {2}"
        )
        self.run_command(command.format(
            self.ssh_password, self.interface, self.proxy_port))

    def unset_ip_routing(self):
        """ Unset IP routing on the host machine so that incoming http
        requests on port 80 are NOT redirected to the proxy port
        Supports: Linux
        """
        os_type = os.getenv('server_os_type', None)
        if self.remote is not True and os_type not in ['Linux']:
            return
        print('Unsetting IP forwarding and iptables rules on {} host'.format(
            os_type))

        command = (
            "echo '{0}' | sudo -S iptables -F && "
            "echo '{0}' | sudo -S iptables -X && "
            "echo '{0}' | sudo -S iptables -t nat -F && "
            "echo '{0}' | sudo -S iptables -t nat -X && "
            "echo '{0}' | sudo -S iptables -t mangle -F && "
            "echo '{0}' | sudo -S iptables -t mangle -X && "
            "echo '{0}' | sudo -S iptables -P INPUT ACCEPT && "
            "echo '{0}' | sudo -S iptables -P FORWARD ACCEPT && "
            "echo '{0}' | sudo -S iptables -P OUTPUT ACCEPT && "
            "echo '{0}' | sudo -S sysctl -w net.ipv4.ip_forward=0 && "
            "echo '{0}' | sudo -S sysctl -w net.ipv6.conf.all.forwarding=0 && "
            "echo '{0}' | sudo -S sysctl -w net.ipv4.conf.all.send_redirects=1"
        )
        self.run_command(command.format(self.ssh_password))

    def _fetch_remote_har(self):
        """ SFTP Get a HAR file from a remote server """
        # pylint: disable=no-member
        try:
            print('Retrieving remote HAR file')
            transport = paramiko.Transport((self.host, int(self.ssh_port)))
            transport.connect(
                hostkey=None,
                username=self.ssh_user,
                password=self.ssh_password
            )
            sftp = paramiko.SFTPClient.from_transport(transport)
            with sftp.open(self.har_path, "r") as har_file:
                self.har_log = har_file.read()

            # Disconnect from the host
            print('Retrieved HAR file, closing SFTP connection')
            sftp.close()
            return self.har
        except paramiko.ssh_exception.SSHException as err:
            print("Could not SFTP to {0} error: {1}".format(self.host, err))
            return None
        except IOError as err:
            print("IOError: {}".format(err))
            return None

    def fetch_har(self):
        """ Tries to get the HAR file """
        har = ''
        retries = 30
        if self.remote is True:
            har = self._fetch_remote_har()
        else:
            print('Retrieving Local HAR file')
            for _ in range(retries):
                if os.path.exists(self.har_path):
                    break
                time.sleep(1)
            har = open(self.har_path, 'r').read()
        return har

    def delete_har(self):
        """ SSH Delete a HAR file from a remote server """
        print('Deleting remote HAR file')
        command = 'rm -f {0}'.format(self.har_path)
        self.run_command(command, 10)
