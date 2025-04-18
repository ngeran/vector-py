import yaml
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_yaml_file(file_path: str) -> Optional[Dict]:
    """Load a YAML file and return its contents as a Python dict or list."""
    try:
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        logger.error(f"File not found at {file_path}")
        return None
    except yaml.YAMLError as error:
        logger.error(f"Error parsing YAML file {file_path}: {error}")
        return None
    except Exception as error:
        logger.error(f"Unexpected error loading {file_path}: {error}")
        return None

def flatten_inventory(inventory: List[Dict]) -> List[Dict]:
    """Flatten inventory.yml into a list of hosts from switches, routers, and firewalls."""
    flat_hosts = []
    for location in inventory:
        for category in ['switches', 'routers', 'firewalls']:
            if category in location:
                for host in location[category]:
                    host['location'] = location['location']
                    flat_hosts.append(host)
    return flat_hosts

def merge_host_data(inventory_file: str, hosts_data_file: str) -> Optional[Dict]:
    """Merge data from inventory.yml and hosts_data.yml, matching hosts by IP or hostname."""
    inventory = load_yaml_file(inventory_file)
    hosts_data = load_yaml_file(hosts_data_file)

    if not inventory or not hosts_data:
        return None

    merged = {
        'username': hosts_data.get('username', 'admin'),
        'password': hosts_data.get('password', ''),
        'interval': hosts_data.get('interval', 300),
        'tables': hosts_data.get('tables', ['inet.0'])
    }

    inventory_hosts = flatten_inventory(inventory)
    inventory_lookup = {host['ip_address']: host for host in inventory_hosts}

    merged_hosts = []
    for host in hosts_data.get('hosts', []):
        ip = host.get('ip_address')
        if ip in inventory_lookup:
            merged_host = inventory_lookup[ip].copy()
            merged_host.update(host)
            merged_hosts.append(merged_host)
        else:
            logger.warning(f"Host '{host.get('host_name', ip)}' in hosts_data.yml not found in inventory.yml")
            merged_hosts.append(host)

    for ip, inv_host in inventory_lookup.items():
        if not any(h['ip_address'] == ip for h in merged_hosts):
            logger.warning(f"Host '{inv_host['host_name']}' in inventory.yml not found in hosts_data.yml")
            merged_hosts.append(inv_host)

    merged['hosts'] = merged_hosts
    return merged
