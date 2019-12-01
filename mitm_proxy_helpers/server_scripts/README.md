## Requirement:

**To proxy the connection from any test device to proxy software like mitmproxy in order to intercept API calls, adserver and analytics HTTP calls**

## Option 1: The proxy server can be set within device Settings

TODO

## Option 1: The proxy server cannot be set within device Settings

One way to reliably proxy the connection is to point the devices to a router that is configured to redirect the connection to a machine running a transparent proxy. The proxy software needs to be configured in 'transparent' or 'invisible' mode.

### Hardware Requirements

-   Device under test.
-   A primary router that is provided by the ISP ('Router 1')
-   A second router ('Router 2') that can be used to install DD-WRT or ExpressVPN custom firmware onto.
-   A computer or local virtual machine that can be used to host a proxy server and web server
-   At least three ethernet cables (Note that if the computer is a macbook you need a USB to ETHERNET adapter)
-   VPN Subscription

### High Level Setup

![transparent proxy setup. smartphone is device under test](http://blog.scphillips.com/images/https-network.png)
1.  Custom router firmware is installed to Router 2.
2.  Ethernet cable set up to go from a LAN port on Router 1 to the WAN/Internet port on Router
3.  Proxy software set up on the computer with transparent mode enabled
4. Firewall rules set up on Router 2 to route specific http connections from the test device to a proxy server
5.  VPN software installed on the computer or router
6.  Depending on configuration: proxy software configured to point to an upstream proxy (the VPN)
7.  Depending on configuration: proxy software configured to re-write the user-agent so it is not blocked by the VPN

### Hardware/software configurations
Below is a table of tested working/non working configurations from best to worst in terms of stability and setup time. Please keep this table updated with known working configs
|No. | Router 2 | Router 2 Firmware  | Server OS | VPN Type | VPN | Firewall config | Setup Time | Working |
|--|--|--|--|--|--|--|--|--|
| **#1** | **Stock Linksys WRT3200ACM** | **ExpressVPN**  | **Linux** | **Router** | **ExpressVPN** | **Single device** | **Short**  | **Yes** |
| #2 | Stock Linksys WRT3200ACM | ExpressVPN  | Mac OS 10.13.6 | Router | ExpressVPN | Single device | Short  | Yes |
| #3 | Linksys E2500 v3 | DD-WRT  | Ubuntu 17.10 | Software | PIA VPN | Single device | Medium  | Yes |
| #4 | N/A | N/A  | Mac OS 10.13.6  | Router | PIA VPN | Internet Sharing | Medium  | Not tested |
All routers are UK models.

### Working  Setup
 - Config #1
 - Router 2: Stock Linksys WRT3200ACM 
 - Router 2 Firmware: ExpressVPN firmware for WRT3200ACM - expressvpn-linksys-wrt3200acm-v1.5.4.img
 - Server OS: Linux (Debian Stretch) 
 - VPN: Router level 
 - VPN: ExpressVPN default as per firmware, US New York 

### Step 1: Configure Router 2
#### WRT3200ACM with ExpressVPN firmware
 1. ExpressVPN account is required
 2. Install the ExpressVPN firmware to the router as per: https://www.expressvpn.com/support/vpn-setup/expressvpn-linksys-3200/
 3. Connect an ethernet cable to go from a LAN port on Router 1 to the WAN/Internet port on Router 2


### Step 2: Setup mitmproxy transparent proxy on a server
#### Mac OS
TODO

#### Linux
1. Setup port forwarding. **sudo set_ip_forwarding.sh** or run it directly in a terminal with root privileges: 
``` 
#!/bin/sh
echo "Setting ip forwarding... "
sysctl -w net.ipv4.ip_forward=1
sysctl -w net.ipv6.conf.all.forwarding=1
sysctl -w net.ipv4.conf.all.send_redirects=0
echo "Setting iptables HTTP redirection rules..."
iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 -j REDIRECT --to-port 8081
ip6tables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 -j REDIRECT --to-port 8081
echo "Done"
```
Ensure that `eth0` is replaced with the network interface which can be obtained with `ifconfig`. This ensures that all incoming traffic on port 80 is redirected to port 8081, which will be the port that the transparent proxy will run on.

2. Install Python 3 as per https://docs.python-guide.org/starting/install3/linux/
3. Install mitmproxy as per: https://docs.mitmproxy.org/stable/overview-installation/ which requires Python 3
4. **If HAR logging is required**, start **mitmdump** with:
``` /usr/local/bin/python3.7 /usr/local/bin/mitmdump -s /path/to/har_dump.py --set hardump=/path/to/dump.har --mode transparent --showhost --listen-port 8081 ```
	- Locate the path to python 3.7 or mitmdump with `which python` and `which mitmdump` as they may not be under /usr/local/bin
	- `har_dump.py` is our script that periodically creates a HAR object of network requests and dumps it to a HAR file. This must be the full path to this file.
	- `hardump=` defines where the HAR file will be output to, it will be periodically overwritten as new network requests occur.
	- `listen-port` should match the port set in step 1 (see: port forwarding above) 
5. **If HAR logging is NOT required**, start **mitmproxy** with:
``` mitmproxy --mode transparent --showhost --listen-port 8081 ```
7. Ensure SSH is running server which is by default on most Linux distros
8. If using in conjuction with stb-tester Crackle framework:
    - Take note of this linux machines **IP address**, **username,** **password**, **SSH port** (22 by default) and the **har path** set in `hardump=`. These will be set in stb-tester framework's config files

Notes
- To reverse the ip forwarding rules at the linux machine either restart the machine or run **flush_iptables_linux.sh**:
```
#!/bin/sh
echo "Flushing iptables rules..."
sleep 1
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X
iptables -t mangle -F
iptables -t mangle -X
iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT
iptables -P OUTPUT ACCEPT
```
- To start mitmdump on system startup, add to /etc/rc.local before the `exit 0` line:
``` /usr/local/bin/python3.7 /usr/local/bin/mitmdump -s /path/to/har_dump.py --set hardump=/path/to/dump.har --mode transparent --showhost --listen-port 8081 & ```
Ensuring that the & is present otherwise the system will not start
- the iptables rules that were previously set as per `set_ip_forwarding.sh` will be removed if the machine restarts.

### Step 3: Setup Device under Test

 1. Connect the device under test to Router 2 (either WiFi or Ethernet)
 2. In the device network settings or at Router 2 take note of the **IP address assigned to the test device** and ensure it is on the same subnet as the router, eg 192.168.x.x
 3. Ensure that there is an internet connection by using an app/browsing a website

### Step 4: Setup Firewall routing rules at Router 2
#### WRT3200ACM with ExpressVPN firmware

 1. Navigate to the Router admin area: https://expressvpnrouter.com/
 2. Navigate to Firewall > Custom Rules
 3. Enter the following:
```
#!/bin/sh
PROXY_MACHINE=192.168.42.246
MACHINE_TO_PROXIFY=192.168.42.102

iptables -I PREROUTING 1 -t mangle -s $MACHINE_TO_PROXIFY ! -d 192.168.42.1/255.255.255.0 -p tcp -m multiport --dports 80,443 -j MARK --set-mark 3
iptables -I PREROUTING 2 -t mangle -s $MACHINE_TO_PROXIFY ! -d 192.168.42.1/255.255.255.0 -p tcp -m multiport --dports 80,443 -j CONNMARK --save-mark
iptables -I PREROUTING 3 -t mangle -s $MACHINE_TO_PROXIFY ! -d 255.255.255.0 -p tcp -m multiport --dports 80,443 -j MARK --set-mark 3
iptables -I PREROUTING 4 -t mangle -s $MACHINE_TO_PROXIFY ! -d 255.255.255.0 -p tcp -m multiport --dports 80,443 -j CONNMARK --save-mark
ip rule add fwmark 3 table 13
ip route add default via $PROXY_MACHINE table 13
```
 1. PROXY_MACHINE must be set to the IP address of the linux machine (the proxy server running mitmdump)
 2. MACHINE_TO_PROXIFY must be set to the IP address of the device under test
 3. The ip address 192.168.42.1 in the iptables lines must be set to the IP address of the router
 4. Note: The current iptables configuration only allows proxying of a specific device, MACHINE_TO_PROXIFY. It could be improved in future to allow for all ip addresses to be routed.
 5. In order to ensure the devices always have the same IP address, assign static IP addresses at the router configuration page: Network > DHCP and DNS > then add entries to **Static Leases**
 6. Some changes to the Firewall custom config may require a reboot of the router in order to take effect
 7. **If using Charles or Burp proxy**: iptables rules set at the router usually need to use the MANGLE table not NAT because NAT alters packets and removes the hostname leading to the proxy server making a request to `http://<proxy_ip>/path/to/file` instead of `http://<domain>/path/to/file`. Proxy software like Charles and Burp can still work with NAT firewall rules, as they are able to reconstruct the request using 'host' value in the http request headers. If the proxy you intend to use is Charles or Burp proxy and not browsermob or mitmproxy, instead use the following iptables rules at the router. These rules route all devices that are connected to Router 2 to PROXY_MACHINE:
```
#!/bin/sh
PROXY_MACHINE=192.168.42.246
PROXY_PORT=8081
LAN_IP=192.168.42.1
LAN_NET=192.168.42.1/255.255.255.0
iptables -t nat -A PREROUTING -i br0 -s $LAN_NET -d $LAN_NET -p tcp --dport 80 -j ACCEPT
iptables -t nat -A PREROUTING -i br0 -s ! $PROXY_IP -p tcp --dport 80 -j DNAT --to $PROXY_IP:$PROXY_PORT
iptables -t nat -I POSTROUTING -o br0 -s $LAN_NET -d $PROXY_IP -p tcp -j SNAT --to $LAN_IP
iptables -I FORWARD -i br0 -o br0 -s $LAN_NET -d $PROXY_IP -p tcp --dport $PROXY_PORT -j ACCEPT
```

#### Notes for DD-WRT router firmware

The same router firewall rules can be used however where the router IP is required it is better to replace with
    `nvram get lan_ipaddr`
and replace the netmask (255.255.255.0 above) with:
    `nvram get lan_netmask`
including the backticks, rather than hardcode the values.

### Step 5: Test the setup end to end

 - Ensure that the device under test has an internet connection
 - Ensure that the device under test connection is being proxied to mitmdump / mitmproxy:
     - if using mitmdump the file `/path/to/dump.har`  will be present and non empty / increasing in size
     - if using mitmproxy http requests will appear in the terminal
