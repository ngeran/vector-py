from typing import Callable, List, Dict
from scripts.diagnostic_actions import ping_hosts
from scripts.interface_actions import configure_interfaces

def get_action_map() -> Dict[str, Callable]:
    """Return a mapping of action names to their corresponding functions."""
    return {
        'ping': ping_hosts,
        'interfaces': configure_interfaces
    }

def execute_actions(
    actions: List[str],
    username: str,
    password: str,
    host_ips: List[str],
    hosts: List[Dict],
    connect_to_hosts: Callable,
    disconnect_from_hosts: Callable
) -> None:
    """Execute the specified actions for the given hosts."""
    action_map = get_action_map()
    valid_actions = action_map.keys()

    try:
        for action in actions:
            if action not in valid_actions:
                print(f"Invalid action '{action}'. Valid actions are: {list(valid_actions)}")
                continue

            print(f"Executing action: {action}")
            action_func = action_map[action]
            action_func(
                username=username,
                password=password,
                host_ips=host_ips,
                hosts=hosts,
                connect_to_hosts=connect_to_hosts,
                disconnect_from_hosts=disconnect_from_hosts
            )
    except KeyboardInterrupt:
        print("Action execution interrupted by user.")
        raise
