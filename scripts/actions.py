import logging
import os
from scripts.connect_to_hosts import connect_to_hosts
# Note: We don't need to import disconnect_from_hosts here anymore
from scripts.diagnostic_actions import ping_hosts as ping_host  # Renamed to avoid conflict
from scripts.interface_actions import configure_interfaces as configure_interface
from scripts.route_monitor import monitor_routes
from scripts.utils import load_yaml_file
from jnpr.junos import Device
from typing import List, Dict, Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='network_automation.log'
)
logger = logging.getLogger(__name__)

def get_hosts():
    """Load hosts from hosts_data.yml."""
    try:
        vector_py_dir = os.getenv("VECTOR_PY_DIR", "/home/nikos/github/ngeran/vector-py")
        hosts_file = os.path.join(vector_py_dir, 'data/hosts_data.yml')
        hosts_data = load_yaml_file(hosts_file)
        hosts = hosts_data.get('hosts', [])
        host_ips = [host['ip_address'] for host in hosts]
        username = hosts_data.get('username', 'admin')
        password = hosts_data.get('password', 'password')
        logger.info(f"Loaded hosts: {host_ips}, username: {username}")
        return host_ips, hosts, username, password
    except Exception as e:
        logger.error(f"Error loading hosts: {e}")
        raise

def disconnect_from_hosts(connections: List[Device]):
    """Disconnect from all provided connections."""
    for conn in connections:
        try:
            conn.disconnect()
            logger.info(f"Disconnected from {conn.host}")
        except Exception as e:
            logger.error(f"Error disconnecting from {conn.host}: {e}")

def ping_hosts(username: str, password: str, host_ips: List[str], hosts: List[Dict],
               connect_to_hosts: Callable, disconnect_from_hosts: Callable):
    """Execute ping action on all hosts."""
    try:
        logger.info("Starting ping action")
        connections = []
        for host in host_ips:
            conn_list = connect_to_hosts(host, username, password)
            if conn_list:
                conn = conn_list[0]
                connections.append(conn)
                result = ping_host(conn) # Using the imported ping_host function
                logger.info(f"Ping result for {host}: {result}")
        disconnect_from_hosts(connections)
        logger.info("Ping action completed")
    except Exception as e:
        logger.error(f"Error in ping_hosts: {e}")
        raise

def configure_interfaces(username: str, password: str, host_ips: List[str], hosts: List[Dict], template_file: str = None):
    """Configure interfaces on all hosts."""
    try:
        logger.info("Starting interfaces action")
        connections = []
        for host in host_ips:
            conn_list = connect_to_hosts(host, username, password)
            if conn_list:
                conn = conn_list[0]
                connections.append(conn)
                host_data = next(h for h in hosts if h['ip_address'] == host)
                configure_interface(conn, host_data.get('interfaces', []), template_file)
                logger.info(f"Interfaces configured for {host}")
        disconnect_from_hosts(connections)
        logger.info("Interfaces action completed")
    except Exception as e:
        logger.error(f"Error in configure_interfaces: {e}")
        raise

def monitor_routes(username: str, password: str, host_ips: List[str], hosts: List[Dict],
                   connect_to_hosts: Callable, disconnect_from_hosts: Callable, connections: List[Device]):
    """Monitor routing tables on all hosts."""
    try:
        logger.info("Starting route_monitor action")
        # The connect_to_hosts is likely called within the monitor_routes function
        monitor_routes(
            username=username,
            password=password,
            host_ips=host_ips,
            hosts=hosts,
            connect_to_hosts=connect_to_hosts,
            disconnect_from_hosts=disconnect_from_hosts,
            connections=connections
        )
        disconnect_from_hosts(connections)
        logger.info("Route_monitor action completed")
    except Exception as e:
        logger.error(f"Error in monitor_routes: {e}")
        raise
