from jnpr.junos import Device
from jnpr.junos.exception import ConnectError
import logging

logger = logging.getLogger(__name__)

def connect_to_hosts(username: str, password: str, host_ips: list) -> list:
    """Connect to a list of hosts and return the connections."""
    logger.info(f"Connecting to hosts: {host_ips}")
    connections = []
    for ip in host_ips:
        try:
            dev = Device(host=ip, user=username, password=password)
            dev.open()
            connections.append(dev)
            logger.info(f"Connected to {ip}")
            print(f"Connected to {ip}")
        except ConnectError as e:
            logger.error(f"Failed to connect to {ip}: {e}")
            print(f"Failed to connect to {ip}: {e}")
    logger.info(f"Returning {len(connections)} connections")
    return connections

def disconnect_from_hosts(connections: list):
    """Disconnect from all hosts."""
    logger.info(f"Disconnecting from {len(connections)} connections")
    for dev in connections:
        try:
            ip = dev.hostname
            dev.close()
            logger.info(f"Disconnected from {ip}")
            print(f"Disconnected from {ip} ({ip})")
        except Exception as e:
            logger.error(f"Failed to disconnect from {ip}: {e}")
            print(f"Failed to disconnect from {ip}: {e}")
