import os
import argparse
from scripts.utils import merge_host_data, load_yaml_file
from scripts.connect_to_hosts import connect_to_hosts, disconnect_from_hosts
from scripts.actions import execute_actions

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    """Parse command-line arguments and execute specified actions."""
    try:
        parser = argparse.ArgumentParser(description="Network device automation tool")
        parser.add_argument('--actions', nargs='+',
                            choices=['interfaces', 'bgp', 'ospf', 'ldp', 'rsvp', 'mpls',
                                     'ping', 'bgp_verification', 'ospf_verification',
                                     'backup', 'baseline', 'route_monitor'],
                            help="Actions to perform (e.g., 'ping', 'backup')")
        args = parser.parse_args()
        inventory_file = os.path.join(SCRIPT_DIR, "data/inventory.yml")
        hosts_data_file = os.path.join(SCRIPT_DIR, "data/hosts_data.yml")

        merged_data = merge_host_data(inventory_file,  hosts_data_file)
        if not merged_data:
            print("Failed to load or merge data. Exiting.")
            return

        username = merged_data['username']
        password = merged_data['password']
        hosts = merged_data['hosts']
        hosts_data = load_yaml_file(hosts_data_file)
        host_ips = [host['ip_address'] for host in hosts_data.get('hosts', [])]
        #interval = merged_data['interval']

        if not args.actions:
                print("No actions specified. Use --actions with one or more of:", parser.parse_args(['--help']).actions)
                return

        execute_actions(
            actions=args.actions,
            username=username,
            password=password,
            host_ips=host_ips,
            hosts=hosts,
            connect_to_hosts=connect_to_hosts,
            disconnect_from_hosts=disconnect_from_hosts
        )

        print(f"Completed actions: {args.actions}")

    except KeyboardInterrupt:
        print("Script interrupted by user.")
        return


if __name__ == "__main__":
    main()
