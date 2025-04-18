import os
import time
from datetime import datetime
from typing import Dict, List, Set, Tuple
from jnpr.junos import Device
from jnpr.junos.exception import RpcError
from scripts.utils import load_yaml_file
from scripts.connect_to_hosts import connect_to_hosts, disconnect_from_hosts

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def get_routes(dev: Device, table: str) -> List[Dict]:
    """Fetch routes from a specific routing table."""
    try:
        routes = dev.rpc.get_route_information(table=table, detail=True)
        route_list = []
        for route in routes.findall('.//rt'):
            prefix = route.findtext('rt-destination')
            protocol = route.findtext('rt-entry/protocol-name')
            if prefix and protocol in ['BGP', 'OSPF', 'LDP', 'MPLS']:
                route_list.append({
                    'prefix': prefix,
                    'protocol': protocol,
                    'next_hop': route.findtext('rt-entry/nh/to') or 'N/A'
                })
        return route_list
    except RpcError as error:
        print(f"Failed to fetch routes from {dev.hostname} for table {table}: {error}")
        return []

def compare_routes(old_routes: List[Dict], new_routes: List[Dict]) -> Tuple[Set[str], Set[str], Set[str]]:
    """Compare old and new routes, return added, removed, flapped prefixes."""
    old_prefixes = {(r['prefix'], r['protocol'], r['next_hop']) for r in old_routes}
    new_prefixes = {(r['prefix'], r['protocol'], r['next_hop']) for r in new_routes}

    added = {p[0] for p in new_prefixes - old_prefixes}
    removed = {p[0] for p in old_prefixes - new_prefixes}
    flapped = {p[0] for p in old_prefixes & new_prefixes if p in new_prefixes and p in old_prefixes and p[2] != [r for r in old_routes if r['prefix'] == p[0]][0]['next_hop']}

    return added, removed, flapped

def print_route_table(hosts: List[Dict], route_summary: Dict, changes: Dict):
    """Print route summary and changes in an ASCII table."""
    print("\nRouting Table Summary -", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("-" * 80)
    print("| Host          | BGP   | OSPF  | LDP   | MPLS  | Added | Removed | Flapped |")
    print("-" * 80)
    for host in hosts:
        ip = host['ip_address']
        name = host.get('host_name', ip)
        summary = route_summary.get(ip, {'BGP': 0, 'OSPF': 0, 'LDP': 0, 'MPLS': 0})
        change = changes.get(ip, {'added': set(), 'removed': set(), 'flapped': set()})
        print(f"| {name:<13} | {summary['BGP']:<5} | {summary['OSPF']:<5} | {summary['LDP']:<5} | {summary['MPLS']:<5} | {len(change['added']):<5} | {len(change['removed']):<5} | {len(change['flapped']):<5} |")
    print("-" * 80)

    # Print detailed changes
    for host in hosts:
        ip = host['ip_address']
        name = host.get('host_name', ip)
        change = changes.get(ip, {'added': set(), 'removed': set(), 'flapped': set()})
        if change['added'] or change['removed'] or change['flapped']:
            print(f"\nChanges for {name} ({ip}):")
            if change['added']:
                print("  Added prefixes:", ", ".join(sorted(change['added'])))
            if change['removed']:
                print("  Removed prefixes:", ", ".join(sorted(change['removed'])))
            if change['flapped']:
                print("  Flapped prefixes:", ", ".join(sorted(change['flapped'])))

def monitor_routes(username: str, password: str, host_ips: List[str], hosts: List[Dict], interval: int = 60, single_check: bool = False):
    """Monitor routing tables for changes."""
    tables = ['inet.0', 'inet.3', 'mpls.0']
    previous_routes: Dict[str, Dict[str, List[Dict]]] = {ip: {t: [] for t in tables} for ip in host_ips}

    def check_routes():
        connections = connect_to_hosts(username, password, host_ips)
        if not connections:
            print("No devices connected.")
            return

        route_summary: Dict[str, Dict[str, int]] = {}
        changes: Dict[str, Dict[str, Set[str]]] = {}

        for dev in connections:
            ip = dev.hostname
            route_summary[ip] = {'BGP': 0, 'OSPF': 0, 'LDP': 0, 'MPLS': 0}
            changes[ip] = {'added': set(), 'removed': set(), 'flapped': set()}

            for table in tables:
                current_routes = get_routes(dev, table)
                for route in current_routes:
                    route_summary[ip][route['protocol']] += 1

                # Compare with previous routes
                added, removed, flapped = compare_routes(previous_routes[ip][table], current_routes)
                changes[ip]['added'].update(added)
                changes[ip]['removed'].update(removed)
                changes[ip]['flapped'].update(flapped)
                previous_routes[ip][table] = current_routes

        # Print table and changes
        print_route_table(hosts, route_summary, changes)

        disconnect_from_hosts(connections)

    try:
        if single_check:
            check_routes()
        else:
            while True:
                check_routes()
                print(f"\nWaiting {interval} seconds for next check...")
                time.sleep(interval)

    except KeyboardInterrupt:
        print("Monitoring stopped by user.")
        if 'connections' in locals():
            disconnect_from_hosts(connections)

def main():
    """Main function to monitor routing tables."""
    try:
        hosts_data_file = os.path.join(SCRIPT_DIR, "../data/hosts_data.yml")
        hosts_data = load_yaml_file(hosts_data_file)

        if not hosts_data:
            print("Failed to load hosts_data.yml.")
            return

        username = hosts_data.get('username')
        password = hosts_data.get('password')
        hosts = hosts_data.get('hosts', [])
        host_ips = [host['ip_address'] for host in hosts]
        interval = hosts_data.get('interval', 60)

        if not host_ips:
            print("No hosts defined in hosts_data.yml.")
            return

        monitor_routes(username, password, host_ips, hosts, interval)

    except Exception as error:
        print(f"Error during execution: {error}")

if __name__ == "__main__":
    main()
