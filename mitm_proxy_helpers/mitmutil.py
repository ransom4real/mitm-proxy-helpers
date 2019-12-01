"""
    The proxy config module manages all default proxy configurations and related flags
    during execution
"""
import os
import socket


def proxy_host():
    """
    Returns the local hostname/ip that the library is running on
    or defaults to proxy_host environment variable if it is set
    """
    sckt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sckt.connect(("8.8.8.8", 80))
    hostname = sckt.getsockname()[0]
    return os.getenv('proxy_host', hostname)
