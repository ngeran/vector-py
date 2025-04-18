import os
import importlib
from scripts.utils import load_yaml_file

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def get_action_map():
    """Dynamically load action map from action_map.yml."""
    action_map_file = os.path.join(SCRIPT_DIR, "../data/action_map.yml")
    action_map_data = load_yaml_file(action_map_file)

    if not action_map_data or 'actions' not in action_map_data:
        print("Failed to load action_map.yml or no actions defined.")
        return {}

    action_map = {}
    for action in action_map_data['actions']:
        action_name = action.get('name')
        function_path = action.get('function')

        if not action_name or not function_path:
            print(f"Skipping invalid action: {action}")
            continue

        try:
            # Split function_path into module and function name
            module_path, function_name = function_path.rsplit('.', 1)
            # Import the module
            module = importlib.import_module(module_path)
            # Get the function
            function = getattr(module, function_name)
            action_map[action_name] = function
        except (ImportError, AttributeError) as error:
            print(f"Failed to load function {function_path} for action {action_name}: {error}")

    return action_map

def execute_actions(
    actions: list,
    username: str,
    password: str,
    host_ips: list,
    hosts: list,
    connect_to_hosts,
    disconnect_from_hosts
):
    """Execute the specified actions on the given hosts."""
    action_map = get_action_map()
    connections = None

    try:
        for action in actions:
            if action not in action_map:
                print(f"Invalid action '{action}'. Valid actions are: {list(action_map.keys())}")
                return

            action_func = action_map[action]
            print(f"Executing action: {action}")

            connections = connect_to_hosts(username, password, host_ips)
            if not connections:
                print(f"No devices connected for action: {action}")
                return

            # Execute the action
            action_func(
                username=username,
                password=password,
                host_ips=host_ips,
                hosts=hosts,
                single_check=True  # For route_monitor to run one cycle
            )

    except Exception as error:
        print(f"Error executing action {action}: {error}")

    finally:
        if connections:
            disconnect_from_hosts(connections)
