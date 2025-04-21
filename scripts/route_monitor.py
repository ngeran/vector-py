import os
from datetime import datetime
import logging
from typing import List, Dict
from jnpr.junos import Device

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

    try:
        # Use provided connections if available; otherwise, connect
        if connections is None:
            logger.info("No connections provided, creating new connections")
            connections = connect_to_hosts(username, password, host_ips)
        if not connections:
            logger.error("No devices connected for route monitoring")
            print("No devices connected for route monitoring.")
            return

        host_lookup = {h['ip_address']: h['host_name'] for h in hosts}
        summary = []

        for dev in connections:
            hostname = host_lookup.get(dev.hostname, dev.hostname)
            try:
                # Fetch routing tables
                inet0_routes = dev.rpc.get_route_information(table='inet.0', format='text')
                inet3_routes = dev.rpc.get_route_information(table='inet.3', format='text')
                mpls_routes = dev.rpc.get_route_information(table='mpls.0', format='text')

                # Parse route counts (simplified, adjust based on actual output)
                inet0_count = len(inet0_routes.xpath('//route-table/rt'))
                inet3_count = len(inet3_routes.xpath('//route-table/rt'))
                mpls_count = len(mpls_routes.xpath('//route-table/rt'))

                # Fetch protocol-specific counts (example, adjust as needed)
                bgp_summary = dev.rpc.get_bgp_summary_information(format='text')
                ospf_neighbors = dev.rpc.get_ospf_neighbor_information(format='text')
                ldp_sessions = dev.rpc.get_ldp_session_information(format='text')

                bgp_count = len(bgp_summary.xpath('//bgp-peer'))
                ospf_count = len(ospf_neighbors.xpath('//ospf-neighbor'))
                ldp_count = len(ldp_sessions.xpath('//ldp-session'))

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

                print(f"Fetched routes from {dev.hostname} for tables inet.0, inet.3, mpls.0")

            except Exception as e:
                logger.error(f"Failed to fetch routes from {dev.hostname}: {e}")
                print(f"Failed to fetch routes from {dev.hostname}: {e}")

        # Generate report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report = f"Routing Table Summary - {timestamp}\n{'-'*80}\n"
        report += "| Host          | BGP   | OSPF  | LDP   | MPLS  | Added | Removed | Flapped |\n"
        report += "|---------------|-------|-------|-------|-------|-------|---------|---------|\n"
        for entry in summary:
            report += f"| {entry['host']:<13} | {entry['bgp']:<5} | {entry['ospf']:<5} | {entry['ldp']:<5} | {entry['mpls']:<5} | {entry['added']:<5} | {entry['removed']:<7} | {entry['flapped']:<7} |\n"
        report += "-" * 80 + "\n"

        report_file = os.path.join(report_dir, f"route_monitor_{timestamp}.txt")
        with open(report_file, 'w') as f:
            f.write(report)
        logger.info(f"Route monitor report saved to {report_file}")
        print(f"Route monitor report saved to {report_file}")

    except Exception as e:
        logger.error(f"Error in monitor_routes: {e}")
        print(f"Error in monitor_routes: {e}")
    finally:
        if connections and not disconnect_from_hosts.__name__ == 'noop':
            disconnect_from_hosts(connections)
    logger.info("Finished monitor_routes")
