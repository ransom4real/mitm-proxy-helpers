from __future__ import print_function
import socket
import sys
import os
import getopt
from mitm_proxy_helpers.proxy_logger import ProxyLogger


class InvalidPathException(Exception):
    pass


class MitmProxy(ProxyLogger):
    """ Build a mitmproxy server command line string """

    def __init__(self, config):
        self.config = config
        if not self.config.get('har_path').endswith('.har'):
            raise InvalidPathException(
                "Config value 'har_path' is not a valid path to a HAR file")
        super(MitmProxy, self).__init__()

    # pylint: disable=useless-else-on-loop
    def build_ignore_hosts(self, hostname=None):
        """ Build a mitmproxyignore_hosts command string.
        Take a hostname and convert it to a list of IP addresses. Use this to
        build the mitmproxy ignore command line argument string """

        ignore_str = r""
        if not hostname:
            return ignore_str
        # Resolve hostname to a list of IP addresses
        self.log_output('proxy_launcher: Resolving hostname: {}'.format(hostname))
        ip_addresses = socket.gethostbyname_ex(hostname)[-1]

        # Construct the ignore hosts string
        if ip_addresses:
            ignore_str += r"--ignore-hosts '"
            if len(ip_addresses) == 1:
                ignore_str += ip_addresses[0].replace(r'.', r'\.') + r":80"
            else:
                ip_addresses = list(set(ip_addresses))
                for ip in ip_addresses[:-1]:
                    # All but the last IP address entry
                    ignore_str += ip.replace(r'.', r'\.') + r":80|"
                else:
                    # Last IP address entry
                    ignore_str += ip_addresses[-1].replace(r'.', r'\.') + r":80"
            ignore_str += r"'"
        self.log_output('ignore-hosts value: {}'.format(ignore_str))
        return ignore_str

    def build_command(self):
        """ Build the mitmproxy (mitmdump) command line string """
        ignore_str = MitmProxy.build_ignore_hosts(
            self.config.get('ignore_hostname', ''))
        mode_str = ''
        mode = self.config.get('mode', None)
        if mode:
            mode_str = "--mode {0} ".format(mode)
        cmd = ("ulimit -s {ulimit} & "
               "{python3_path} /usr/local/bin/mitmdump "
               "{mode_str}"
               "--listen-port={proxy_port} --showhost "
               "--set hardump='{har_path}' "
               "--set status_code='{status_code}' "
               "--set field_name='{field_name}' "
               "--set field_value='{field_value}' "
               "--set partial_url='{partial_url}' "
               "--set partial_url_2='{partial_url_2}' "
               "--set fixture_path='{fixture_path}' "
               "--set fixture_path_2='{fixture_path_2}' "
               "--set run_identifier='{run_identifier}' "
               "{ignore_str}").format(
                   ulimit=self.config.get('ulimit', ''),
                   python3_path=self.config.get('python3_path', ''),
                   mode_str=mode_str,
                   proxy_port=self.config.get('proxy_port', ''),
                   har_path=self.config.get('har_path', ''),
                   status_code=self.config.get('status_code', ''),
                   field_name=self.config.get('field_name', ''),
                   field_value=self.config.get('field_value', ''),
                   partial_url=self.config.get('partial_url', ''),
                   partial_url_2=self.config.get('partial_url_2', ''),
                   fixture_path=self.config.get('fixture_path', ''),
                   fixture_path_2=self.config.get('fixture_path_2', ''),
                   run_identifier=self.config.get('run_identifier', ''),
                   ignore_str=ignore_str)
        if self.config.get('script_path'):
            cmd += " -s {}".format(self.config.get('script_path'))
        cmd += " > /dev/null 2>&1 &"
        return cmd

    def run_command(self):
        """ Run the mitmproxy command """
        cmd = self.build_command()
        self.log_output('proxy_launcher: Running command: {}'.format(cmd))
        os.system(cmd)


if __name__ == '__main__':
    try:
        options, remainder = getopt.getopt(
            sys.argv[1:],
            '',
            ['ulimit=', 'python3_path=', 'har_dump_path=', 'har_path=',
             'proxy_port=', 'script_path=', 'mode=',
             'ignore_hostname=',
             'status_code=', 'field_name=', 'field_value=',
             'partial_url=', 'partial_url_2=',
             'fixture_path=', 'fixture_path_2=', 'run_identifier='])
    except getopt.GetoptError as err:
        print('proxy_launcher: {}'.format(err))
        sys.exit(1)
    conf = {}
    for opt, arg in options:
        conf[opt.strip('--')] = arg
    MitmProxy(conf).run_command()
