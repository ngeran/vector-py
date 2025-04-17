import os
from scripts.utils import merge_host_data, load_yaml_file
from scripts.connect_to_hosts import connect_to_hosts, disconnect_from_hosts
from scripts.actions import execute_actions

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    """Execute the action specified in hosts_data.yml."""
    try:
        inventory_file = os.path.join(SCRIPT_DIR, "data/inventory.yml")
        hosts_data_file = os.path.join(SCRIPT_DIR, "data/hosts_data.yml")

        merged_data = merge_host_data(inventory_file, hosts_data_file)
        if not merged_data:
            print("Failed to load or merge data. Exiting.")
            return

        hosts_data = load_yaml_file(hosts_data_file)
        template = hosts_data.get('template')
        valid_templates = [
            'interfaces', 'bgp', 'ospf', 'ldp', 'rsvp', 'mpls',
            'ping', 'bgp_verification', 'ospf_verification',
            'backup', 'baseline', 'route_monitor'
        ]

        if not template:
            print("No template specified in hosts_data.yml. Please set 'template' to one of:", valid_templates)
            return
        if template not in valid_templates:
            print(f"Invalid template '{template}' in hosts_data.yml. Valid templates are:", valid_templates)
            return

        username = merged_data['username']
        password = merged_data['password']
        hosts = merged_data['hosts']
        host_ips = [host['ip_address'] for host in hosts_data.get('hosts', [])]

        execute_actions(
            actions=[template],  # Single action from template
            username=username,
            password=password,
            host_ips=host_ips,
            hosts=hosts,
            connect_to_hosts=connect_to_hosts,
            disconnect_from_hosts=disconnect_from_hosts
        )

        print(f"Completed action: {template}")

    except KeyboardInterrupt:
        print("Script interrupted by user.")
        return

if __name__ == "__main__":
    main()
