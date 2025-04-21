import os
import yaml
from typing import List, Dict
from scripts.actions import execute_actions
from scripts.connect_to_hosts import connect_to_hosts, disconnect_from_hosts
from scripts.utils import load_yaml_file
import logging
from logging.handlers import RotatingFileHandler
import sys
import termios

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Ensure log directory exists
log_dir = "/home/nikos/github/ngeran/vector-py"
os.makedirs(log_dir, exist_ok=True)

# Console handler (WARNING and above)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

# File handler (INFO and above)
log_file = os.path.join(log_dir, "network_automation.log")
file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# Add handlers
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Suppress ncclient logs
logging.getLogger("ncclient").setLevel(logging.WARNING)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def is_interactive():
    """Check if the script is running interactively (connected to a terminal)."""
    try:
        return os.isatty(sys.stdin.fileno())
    except (AttributeError, termios.error):
        return False

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

    # Only display menu if running interactively
    if is_interactive():
        display_menu(actions)

    # Read choice from stdin (piped from launcher.py or interactive)
    try:
        choice = sys.stdin.read().strip() if not is_interactive() else input(f"Enter your choice (1-{len(actions)}): ")
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
