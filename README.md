# What is this repository for?

Helpers to enable MITM proxy functionality for direct and transparent proxying on projects utilising the library

# How do I use it
1. MITM proxy is an alternative to browsermob. This is useful when request interception and response manipulation is required. To install please ensure you are running the latest version of python and then run `pip3 install mitmproxy`. See `https://docs.mitmproxy.org/stable/overview-installation/` for more information
2. Then install `mitm-proxy-helpers` either via pip using `pip install mitm-proxy-helpers` or add mitm proxy helpers to your Pipfile like this `mitm-proxy-helpers="*"`. To get the latest master version `mitm-proxy-helpers = {git = "git://github.com/ransom4real/mitm-proxy-helpers.git",editable = true}`
3. ```python
   from mitm_proxy_helpers.proxy import Proxy
   proxy_client = Proxy()
   ```

   To start the proxy
   ```python
   proxy_client.start_proxy()
   ```

   To set the proxy for Firefox
   ```python
   ff_profile = webdriver.FirefoxProfile()
   ff_profile.set_proxy(proxy_client.selenium_proxy())
   ```

   To set the proxy for Chrome
   ```python
   from selenium.webdriver.chrome.options import Options as ChromeOptions
   chrome_options = ChromeOptions()
   chrome_options.add_argument("--proxy-server={0}".format(proxy_client.proxy()))
   ```

   You can get the proxy host and port by accessing the proxy attributes
   ```python
   host = proxy_client.host
   port = proxy_client.proxy_port
   ```

   You can stop the proxy using (Stopping the proxy when in hardump mode writes the har log out)
   ```python
   proxy_client.stop_proxy
   ```

   To fetch the har log ensure you are running the `har_logging` script and call the `har()` method
   ```python
   proxy_client = Proxy(script='har_logging')
   proxy_client.har()
   ```

   Other scripts you can run include `blacklist`, `empty_response`, `har_and_blacklist`, `json_resp_field_rewriter`, `response_replace`, `request_throttle` and `har_logging_no_replace`. Just ensure you set the MITM related variables as explained below

During execution some environment variables will need to be set defaults are meant to be overriden. See list below

## Proxy
* proxy_host: This is the IP of the netork interface you want the proxy to be associated with. If this is not specified the framework is select the first active network interface when creating the proxy. Ensure you configure this especially when running via a VPN alongside your normal network.
* proxy_provider: This defaults to `browsermob`. Other options include `mitmproxy` which would use MITM proxy as an alternative.

## MITM Related Variables
* mitm_server_host: Default to `proxy_host` variable if set. This is required if the MITM proxy is remote and is the IP of the host machine
* mitm_server_ssh_port: If set, the framework will assume the MITM proxy is remote rather than local. Set to `22` unless SSH runs on a different port on the host machine
* mitm_server_ssh_user: This is required if MITM is on a remote machine. The username should have the appropriate permissions to run MITM proxy and associated scripts
* mitm_server_ssh_password: This is the associated password for the `mitm_server_ssh_user`
* mitm_server_interface: The network interface MITM is running on. On MacOS this should be `en0` for wireless connections, `eth0` for wired connections. You can find what it is by doing `ifconfig` on the MITM host
* mitm_proxy_listen_port: This defaults to `8081` and this indicates what port MITM Proxy will be listening on
* mitm_har_path: This default to `logs/har/dump.har` path of the project root. However you can set a path reflecting where you want this har outputted on the remote MITM host.
* mitm_python3_path: This defaults to the current python 3 path on the host machine where this framework resides. If running MITM proxy remotely then this should be the path to the python 3 version on that host
* fixtures_dir: Path to your json fixures for intercepting and rewriting proxy requests. Defaults to `mitm_proxy_helpers/server_scripts/fixtures` path of the framework root directory
* mitm_verbose: Set to true if you want to print the mitm_proxy library outputs to the terminal. Defaults to false

## MITM Proxy Scripts
* This defaults to `mitm_proxy_helpers/server_scripts/${script}.py`. If you have custom `${script}.py` scripts please set the path here. If path is remote, please set the path to the remote script location. Possible scripts include `har_dump`, `blacklister`, `empty_response`, `har_dump_and_blacklister`, `json_response_field_rewriter`, `response_replace` and `request_throttle`.


# How do i contribute to it
1. Install project dependencies by running `pip install --three`
2. Upon code changes run pylint_runner by executing `pipenv run pylint_runner` to lint your code and ensure nothing is broken
3. Bump library version in `setup.py`

# Deploying package to pypi

1. Delete old dist files from dist/
2. python3 setup.py sdist bdist_wheel
3. twine upload dist/*

Note twine may need to be configured to point to production pypi
