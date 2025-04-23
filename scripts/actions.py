import logging
import yaml
import os
from .connect_to_hosts import connect_to_hosts
from .diagnostic_actions import ping_hosts as ping_host
from .interface_actions import configure_interfaces as configure_interface
from .route_monitor import check_routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='network_automation.log'
)
logger = logging.getLogger(__name__)

def load_yaml_file(file_path):
    """Load and return the contents of a YAML file."""
    try:
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)
        logger.info(f"Loaded YAML file: {file_path}")
        return data
    except Exception as e:
        logger.error(f"Error loading YAML file {file_path}: {e}")
        raise

def get_hosts():
    """Load hosts from hosts_data.yml."""
    try:
        vector_py_dir = os.getenv("VECTOR_PY_DIR", "/home/nikos/github/ngeran/vector-py")
        hosts_file = os.path.join(vector_py_dir, 'data/hosts_data.yml')
        hosts_data = load_yaml_file(hosts_file)
        hosts = [host['ip'] for host in hosts_data.get('hosts', [])]
        logger.info(f"Loaded hosts: {hosts}")
        return hosts
    except Exception as e:
        logger.error(f"Error loading hosts: {e}")
        raise

def ping_hosts():
    """Execute ping action on all hosts."""
    try:
        logger.info("Starting ping action")
        hosts = get_hosts()
        for host in hosts:
            conn = connect_to_hosts(host)
            result = ping_host(conn)
            logger.info(f"Ping result for {host}: {result}")
            conn.disconnect()
        logger.info("Ping action completed")
    except Exception as e:
        logger.error(f"Error in ping_hosts: {e}")
        raise

def configure_interfaces():
    """Configure interfaces on all hosts."""
    try:
        logger.info("Starting interfaces action")
        hosts = get_hosts()
        for host in hosts:
            conn = connect_to_hosts(host)
            configure_interface(conn)
            logger.info(f"Interfaces configured for {host}")
            conn.disconnect()
        logger.info("Interfaces action completed")
    except Exception as e:
        logger.error(f"Error in configure_interfaces: {e}")
        raise

def monitor_routes():
    """Monitor routing tables on all hosts."""
    try:
        logger.info("Starting route_monitor action")
        hosts = get_hosts()
        for host in hosts:
            conn = connect_to_hosts(host)
            routes = check_routes(conn)
            logger.info(f"Routes for {host}: {routes}")
            conn.disconnect()
        logger.info("Route_monitor action completed")
    except Exception as e:
        logger.error(f"Error in monitor_routes: {e}")
        raise
