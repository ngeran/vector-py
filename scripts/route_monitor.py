import os
from datetime import datetime
import logging
from typing import List, Dict
from jnpr.junos import Device
from jnpr.junos.exception import ConnectError # Import ConnectError

logger = logging.getLogger(__name__)

def monitor_routes(
    username: str,
    password: str,
    host_ips: List[str],
    hosts: List[Dict],
    connect_to_hosts: callable,
    disconnect_from_hosts: callable,
    connections: List[Device] = None
):
    """Monitor routing tables on devices and generate a summary report."""
    logger.info("Starting monitor_routes")
    report_dir = os.path.join(os.path.dirname(__file__), '../reports')
    os.makedirs(report_dir, exist_ok=True)

    local_connections = [] # Keep track of connections made here
    try:
        # Use provided connections
        if connections is None:
            logger.info("No connections provided, creating new connections")
            try:
                connections = connect_to_hosts(host_ips, username, password)  # Connect to all hosts
                local_connections = connections # Store connections made in this function
            except ConnectError as e:
                logger.error(f"Failed to connect to hosts: {e}")
                print(f"Failed to connect to hosts: {e}")
                return  # IMPORTANT: Exit if connection fails

        if not connections:
            logger.error("No devices connected for route monitoring")
            print("No devices connected for route monitoring.")
            return

        host_lookup = {h['ip_address']: h['host_name'] for h in hosts}
        summary = []

        for dev in connections:
            hostname = host_lookup.get(dev.hostname, dev.hostname)
            try:
                # Fetch routing tables (XML by default)
                inet0_routes = dev.rpc.get_route_information(table='inet.0')
                inet3_routes = dev.rpc.get_route_information(table='inet.3')
                mpls_routes = dev.rpc.get_route_information(table='mpls.0')

                # Parse route counts
                inet0_count = len(inet0_routes.xpath('.//rt'))
                inet3_count = len(inet3_routes.xpath('.//rt'))
                mpls_count = len(mpls_routes.xpath('.//rt'))

                # Fetch protocol-specific counts
                bgp_summary = dev.rpc.get_bgp_summary_information()
                ospf_neighbors = dev.rpc.get_ospf_neighbor_information()
                ldp_sessions = dev.rpc.get_ldp_session_information()

                bgp_count = len(bgp_summary.xpath('.//bgp-peer'))
                ospf_count = len(ospf_neighbors.xpath('.//ospf-neighbor'))
                ldp_count = len(ldp_sessions.xpath('.//ldp-session'))

                summary.append({
                    'host': hostname,
                    'bgp': bgp_count,
                    'ospf': ospf_count,
                    'ldp': ldp_count,
                    'mpls': mpls_count,
                    'added': 0,  # Placeholder, update with actual logic
                    'removed': 0,
                    'flapped': 0
                })

                print(f"Fetched {inet0_count} routes from {hostname} ({dev.hostname}) for table inet.0")
                print(f"Fetched {inet3_count} routes from {hostname} ({dev.hostname}) for table inet.3")
                print(f"Fetched {mpls_count} routes from {hostname} ({dev.hostname}) for table mpls.0")

            except Exception as e:
                logger.error(f"Failed to fetch routes from {hostname} ({dev.hostname}): {e}")
                print(f"Failed to fetch routes from {hostname} ({dev.hostname}): {e}")

        # Generate report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report = f"Routing Table Summary - {timestamp}\n{'-'*80}\n"
        report += "| Host            | BGP    | OSPF   | LDP    | MPLS   | Added | Removed | Flapped |\n"
        report += "|----------------|--------|--------|--------|--------|-------|---------|---------|\n"
        for entry in summary:
            report += f"| {entry['host']:<13} | {entry['bgp']:<6} | {entry['ospf']:<6} | {entry['ldp']:<6} | {entry['mpls']:<6} | {entry['added']:<5} | {entry['removed']:<7} | {entry['flapped']:<7} |\n"
        report += "-" * 80 + "\n"

        report_file = os.path.join(report_dir, f"route_monitor_{timestamp}.txt")
        with open(report_file, 'w') as f:
            f.write(report)
        logger.info(f"Route monitor report saved to {report_file}")
        print(f"Route monitor report saved to {report_file}")

    except Exception as e:
        logger.error(f"Error in monitor_routes: {e}")
        print(f"Error in monitor_routes: {e}")
        raise  # Re-raise the exception to be caught in actions.py
    finally:
        if local_connections: # Disconnect only connections made in this function
           disconnect_from_hosts(local_connections)
        logger.info("Finished monitor_routes")
