import os
import yaml
from typing import List, Dict
from scripts.actions import execute_actions
from scripts.connect_to_hosts import connect_to_hosts, disconnect_from_hosts
from scripts.utils import load_yaml_file
import logging
import sys

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def display_menu(actions: List[Dict]):
    """Display the action selection menu."""
    print("\nSelect an action:")
    print("-" * 40)
    print("| Option | Action                  |")
    print("-" * 40)
    for i, action in enumerate(actions, 1):
        print(f"| {i:<6} | {action['display_name']:<22} |")
    print("-" * 40)

def update_hosts_data(template_file: str):
    """Update hosts_data.yml with the selected template file."""
    hosts_data_file = os.path.join(SCRIPT_DIR, "../data/hosts_data.yml")
    hosts_data = load_yaml_file(hosts_data_file)
    if not hosts_data:
        logger.error("Failed to load hosts_data.yml.")
        return False
    if template_file:
        hosts_data['template_file'] = template_file
    else:
        hosts_data.pop('template_file', None)
    try:
        with open(hosts_data_file, 'w') as f:
            yaml.safe_dump(hosts_data, f)
        logger.info(f"Updated hosts_data.yml with template: {template_file or 'none'}")
        return True
    except Exception as e:
        logger.error(f"Error updating hosts_data.yml: {e}")
        return False

def main():
    """Main function for network automation."""
    actions_file = os.path.join(SCRIPT_DIR, "../data/actions.yml")
    hosts_data_file = os.path.join(SCRIPT_DIR, "../data/hosts_data.yml")

    actions_data = load_yaml_file(actions_file)
    actions = actions_data.get('actions', [])
    if not actions:
        logger.error("No actions defined in actions.yml.")
        sys.exit(1)

    hosts_data = load_yaml_file(hosts_data_file)
    if not hosts_data:
        logger.error("Failed to load hosts_data.yml.")
        sys.exit(1)

    username = hosts_data.get('username')
    password = hosts_data.get('password')
    hosts = hosts_data.get('hosts', [])
    host_ips = [host['ip_address'] for host in hosts]
    if not host_ips:
        logger.error("No hosts defined in hosts_data.yml.")
        sys.exit(1)

    # Read choice from stdin (piped from launcher.py)
    display_menu(actions)  # For logging/debugging
    try:
        choice = sys.stdin.read().strip()
        logger.info(f"Received choice: {choice}")
        choice = int(choice)
        if 1 <= choice <= len(actions):
            action = actions[choice - 1]
            template_file = action.get('template_file')
            action_name = action.get('name')
            if update_hosts_data(template_file):
                execute_actions(
                    actions=[action_name],
                    username=username,
                    password=password,
                    host_ips=host_ips,
                    hosts=hosts,
                    connect_to_hosts=connect_to_hosts,
                    disconnect_from_hosts=disconnect_from_hosts
                )
            else:
                logger.error("Failed to update hosts_data.yml. Aborting.")
                print("Failed to update hosts_data.yml. Aborting.")
                sys.exit(1)
        else:
            logger.error(f"Invalid choice: {choice}. Must be between 1 and {len(actions)}.")
            print(f"Invalid choice: {choice}. Please select between 1 and {len(actions)}.")
            sys.exit(1)
        logger.info("Action completed, exiting")
        sys.exit(0)  # Explicitly exit after success
    except ValueError:
        logger.error(f"Invalid input: {choice}. Must be a number.")
        print("Invalid input. Please enter a number.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during execution: {e}")
        print(f"Error during execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
