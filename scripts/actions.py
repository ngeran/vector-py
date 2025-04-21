import logging
from typing import List, Dict, Callable
from scripts.diagnostic_actions import ping_hosts
from scripts.interface_actions import configure_interfaces
from scripts.route_monitor import monitor_routes

logger = logging.getLogger(__name__)

ACTION_MAP = {
    'ping': ping_hosts,
    'interfaces': configure_interfaces,
    'route_monitor': monitor_routes
}

def execute_actions(
    actions: List[str],
    username: str,
    password: str,
    host_ips: List[str],
    hosts: List[Dict],
    connect_to_hosts: Callable,
    disconnect_from_hosts: Callable
):
    """Execute the specified actions."""
    logger.info(f"Starting execute_actions with actions: {actions}")
    connections = []
    try:
        connections = connect_to_hosts(username, password, host_ips)
        if not connections:
            logger.error("No devices connected for actions")
            return

        for action in actions:
            logger.info(f"Executing action: {action}")
            action_func = ACTION_MAP.get(action)
            if action_func:
                action_func(
                    username=username,
                    password=password,
                    host_ips=host_ips,
                    hosts=hosts,
                    connect_to_hosts=connect_to_hosts,
                    disconnect_from_hosts=disconnect_from_hosts,
                    connections=connections  # Pass connections to action
                )
                logger.info(f"Completed action: {action}")
            else:
                logger.error(f"Unknown action: {action}")

    except Exception as e:
        logger.error(f"Error during action execution: {e}")
    finally:
        if connections:
            disconnect_from_hosts(connections)
    logger.info("Finished execute_actions")
