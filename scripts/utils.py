import yaml
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

def load_yaml_file(file_path):
    try:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"File not found at {file_path}")
        return None
    except Exception as e:
        logger.error(f"Error loading YAML file {file_path}: {e}")
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

def merge_host_data(inventory_file, hosts_data_file):
    inventory_data = load_yaml_file(inventory_file) or {}
    hosts_data = load_yaml_file(hosts_data_file) or {}

    merged_data = {
        'username': inventory_data.get('username', hosts_data.get('username')),
        'password': inventory_data.get('password', hosts_data.get('password')),
        'hosts': []
    }

    inventory_hosts = {host['host_name']: host for host in inventory_data.get('hosts', [])}
    hosts_data_hosts = {host['host_name']: host for host in hosts_data.get('hosts', [])}

    for host_name, inv_host in inventory_hosts.items():
        if host_name in hosts_data_hosts:
            merged_host = inv_host.copy()
            merged_host.update(hosts_data_hosts[host_name])
            merged_data['hosts'].append(merged_host)

    return merged_data
