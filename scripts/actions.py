import os
import importlib
import sys
import logging
from scripts.utils import load_yaml_file

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def get_action_map():
    """Dynamically load action map from action_map.yml."""
    action_map_file = os.path.join(SCRIPT_DIR, "../data/action_map.yml")
    logger.debug(f"Loading action_map.yml from: {action_map_file}")
    action_map_data = load_yaml_file(action_map_file)

    if not action_map_data or 'actions' not in action_map_data:
        logger.error("Failed to load action_map.yml or no actions defined.")
        return {}

    # Ensure scripts/ is in sys.path
    scripts_dir = SCRIPT_DIR
    project_root = os.path.dirname(os.path.dirname(SCRIPT_DIR))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    logger.debug(f"sys.path: {sys.path}")

    action_map = {}
    available_modules = [f[:-3] for f in os.listdir(scripts_dir) if f.endswith('.py') and f != '__init__.py']
    logger.debug(f"Available modules in scripts/: {available_modules}")

    for action in action_map_data['actions']:
        action_name = action.get('name')
        function_path = action.get('function')

        if not action_name or not function_path:
            logger.warning(f"Skipping invalid action: {action}")
            continue

        logger.debug(f"Attempting to load function: {function_path} for action: {action_name}")
        try:
            # Split function_path into module and function name
            module_path, function_name = function_path.rsplit('.', 1)
            # Import the module
            logger.debug(f"Importing module: {module_path}")
            module = importlib.import_module(module_path)
            # Get the function
            function = getattr(module, function_name)
            action_map[action_name] = function
            logger.debug(f"Successfully loaded function: {function_path}")
        except (ImportError, AttributeError) as error:
            logger.error(f"Failed to load function {function_path} for action {action_name}: {error}")

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
    logger.debug("Executing actions: %s", actions)
    action_map = get_action_map()
    connections = None

    try:
        for action in actions:
            if action not in action_map:
                logger.error(f"Invalid action '{action}'. Valid actions are: {list(action_map.keys())}")
                return

            action_func = action_map[action]
            logger.info(f"Executing action: {action}")

            connections = connect_to_hosts(username, password, host_ips)
            if not connections:
                logger.error(f"No devices connected for action: {action}")
                return

            # Execute the action
            action_func(
                username=username,
                password=password,
                host_ips=host_ips,
                hosts=hosts,
                single_check=True  # For route_monitor to run one cycle
            )
            logger.info(f"Completed action: {action}")

    except Exception as error:
        logger.error(f"Error executing action {action}: {error}")

    finally:
        if connections:
            disconnect_from_hosts(connections)
