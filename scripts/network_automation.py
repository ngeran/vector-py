import logging
import yaml
from .actions import ping_hosts, configure_interfaces, monitor_routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='network_automation.log'
)
logger = logging.getLogger(__name__)

def display_menu(actions):
    """Display a menu of actions and return the user's choice."""
    print("Select an action:")
    print("----------------------------------------")
    print("| Option | Action                  |")
    print("----------------------------------------")
    for i, action in enumerate(actions, 1):
        print(f"| {i:<6} | {action['name']:<22} |")
    print("----------------------------------------")
    max_retries = 5
    retries = 0
    while retries < max_retries:
        try:
            raw_input = input(f"Enter your choice (1-{len(actions)}): ").strip()
            logger.info(f"Raw input received: '{raw_input}'")
            if not raw_input:
                logger.error("Empty input received")
                print(f"Invalid choice. Please enter a number between 1 and {len(actions)}")
                retries += 1
                continue
            choice = int(raw_input)
            if 1 <= choice <= len(actions):
                logger.info(f"Valid choice selected: {choice}")
                return choice
            logger.error(f"Choice out of range: {choice}")
            print(f"Invalid choice. Please enter a number between 1 and {len(actions)}")
            retries += 1
        except ValueError:
            logger.error(f"Non-numeric input: '{raw_input}'")
            print(f"Invalid choice. Please enter a number between 1 and {len(actions)}")
            retries += 1
        except EOFError:
            logger.error("EOF received during input")
            print(f"Input interrupted. Please enter a number between 1 and {len(actions)}")
            retries += 1
    logger.error(f"Max retries ({max_retries}) reached in display_menu")
    print("Too many invalid attempts. Exiting.")
    return None

def load_yaml_file(file_path):
    """Load and return the contents of a YAML file."""
    try:
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)
        logger.info(f"Loaded YAML file: {file_path}")
        return data
    except Exception as e:
        logger.error(f"Error loading YAML file {file_path}: {e}")
        raise

def main(action_name=None):
    """Main function to execute network automation actions."""
    try:
        logger.info(f"Executing action: {action_name}")
        if not action_name:
            logger.error("No action name provided")
            print("Error: No action name provided")
            return

        # Map action names to functions
        action_map = {
            'ping': ping_hosts,
            'interfaces': configure_interfaces,
            'route_monitor': monitor_routes
        }

        action_func = action_map.get(action_name)
        if not action_func:
            logger.error(f"Unknown action: {action_name}")
            print(f"Error: Unknown action {action_name}")
            return

        # Execute the action
        action_func()
        logger.info(f"Completed action: {action_name}")

    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    main()
