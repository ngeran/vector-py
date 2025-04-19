from typing import List, Dict
from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from jnpr.junos.exception import CommitError
from jinja2 import Environment, FileSystemLoader
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def configure_interfaces(username: str, password: str, host_ips: List[str], hosts: List[Dict], single_check: bool = False):
    """Configure interfaces using Jinja2 template."""
    env = Environment(loader=FileSystemLoader(os.path.join(SCRIPT_DIR, '../templates')))
    template = env.get_template('interface_template.j2')

    # Filter host_ips to only those in hosts
    valid_ips = [host['ip_address'] for host in hosts]
    host_ips = [ip for ip in host_ips if ip in valid_ips]
    print(f"Configuring interfaces for IPs: {host_ips}")

    for host in hosts:
        host_name = host['host_name']
        ip = host['ip_address']
        if ip not in host_ips:
            continue
        interfaces = host.get('interfaces', [])  # Expect interfaces in hosts_data.yml

        try:
            with Device(host=ip, user=username, password=password) as dev:
                config_data = {'interfaces': interfaces}
                config_text = template.render(**config_data)
                print(f"Config for {host_name} ({ip}):\n{config_text}")

                with Config(dev, mode='exclusive') as cu:
                    cu.load(config_text, format='text')
                    cu.commit()
                print(f"Interface configured on {host_name} ({ip})")
        except CommitError as e:
            print(f"CommitError for {host_name} ({ip}): {e}")
            print(f"Full error details: {e.__dict__}")
        except Exception as e:
            print(f"Failed to configure {host_name} ({ip}): {e}")
