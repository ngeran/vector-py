from jinja2 import Environment, FileSystemLoader
import os
from scripts.junos_actions import configure_device

def configure_interfaces(username, password, host_ips, hosts, connect_to_hosts, disconnect_from_hosts):
    """Configure interfaces on devices based on hosts_data.yml."""
    template_dir = os.path.join(os.path.dirname(__file__), '../templates')
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('interface_template.j2')

    connections = []
    try:
        connections = connect_to_hosts(username, password, host_ips)
        if not connections:
            print("No devices connected for interface configuration.")
            return

        host_lookup = {h['ip_address']: h for h in hosts}
        for dev in connections:
            host_ip = dev.hostname
            host = host_lookup.get(host_ip)
            if not host or 'interfaces' not in host:
                print(f"No interfaces defined for {host.get('host_name', host_ip)} ({host_ip}), skipping.")
                continue

            config_data = {
                'interfaces': host['interfaces'],
                'host_name': host['host_name']
            }
            config_text = template.render(**config_data)
            configure_device(dev, config_text, host['host_name'], host_ip)

    except KeyboardInterrupt:
        print("Interface configuration interrupted by user.")
        raise
    finally:
        if connections:
            disconnect_from_hosts(connections)
