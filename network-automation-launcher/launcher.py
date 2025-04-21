import os
import subprocess
import yaml
import logging
from logging.handlers import RotatingFileHandler
from typing import List, Dict

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Ensure log directory exists
log_dir = "/home/nikos/github/network-automation-launcher"
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

# Path to the vector-py project
VECTOR_PY_DIR = "/home/nikos/github/ngeran/vector-py"
ACTIONS_FILE = os.path.join(VECTOR_PY_DIR, "data", "actions.yml")
HOSTS_DATA_FILE = os.path.join(VECTOR_PY_DIR, "data", "hosts_data.yml")
MAIN_PY = os.path.join(VECTOR_PY_DIR, "main.py")

def load_yaml_file(file_path: str) -> Dict:
    """Load a YAML file and return its contents."""
    if not os.path.exists(file_path):
        logger.error(f"YAML file not found: {file_path}")
        return {}
    try:
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
            if data is None:
                logger.error(f"YAML file {file_path} is empty or invalid")
                return {}
            logger.info(f"Loaded YAML file: {file_path}")
            return data
    except Exception as e:
        logger.error(f"Error loading YAML file {file_path}: {e}")
        return {}

def display_menu(actions: List[Dict]):
    """Display the action selection menu."""
    print("\nSelect an action:")
    print("-" * 40)
    print("| Option | Action                  |")
    print("-" * 40)
    for i, action in enumerate(actions, 1):
        print(f"| {i:<6} | {action['display_name']:<22} |")
    print("-" * 40)

def update_hosts_data(template_file: str, action_name: str):
    """Update hosts_data.yml with the selected template file."""
    if not os.path.exists(HOSTS_DATA_FILE):
        logger.error(f"hosts_data.yml not found at {HOSTS_DATA_FILE}")
        return False
    hosts_data = load_yaml_file(HOSTS_DATA_FILE)
    if not hosts_data:
        logger.error("Failed to load hosts_data.yml")
        return False
    if template_file:
        hosts_data['template_file'] = template_file
    else:
        hosts_data.pop('template_file', None)
    try:
        with open(HOSTS_DATA_FILE, 'w') as f:
            yaml.safe_dump(hosts_data, f)
        logger.info(f"Updated hosts_data.yml with template: {template_file or 'none'} for action: {action_name}")
        return True
    except PermissionError as e:
        logger.error(f"Permission denied writing to {HOSTS_DATA_FILE}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error updating {HOSTS_DATA_FILE}: {e}")
        return False

def execute_main_py(choice: int):
    """Execute main.py with the selected choice."""
    if not os.path.exists(MAIN_PY):
        logger.error(f"main.py not found at {MAIN_PY}")
        return
    try:
        logger.info(f"Executing main.py with choice {choice}")
        process = subprocess.run(
            ["python", MAIN_PY],
            input=str(choice),
            text=True,
            capture_output=True,
            cwd=VECTOR_PY_DIR,
            timeout=60
        )
        # Filter out menu and INFO logs from stdout
        output_lines = [
            line for line in process.stdout.split('\n')
            if not (line.startswith(('Select an action:', '---', '| Option', 'Enter your choice')) or 'INFO:' in line)
        ]
        print('\n'.join(output_lines))
        # Log stderr only for WARNING and ERROR
        if process.stderr:
            stderr_lines = [line for line in process.stderr.split('\n') if 'WARNING' in line or 'ERROR' in line]
            if stderr_lines:
                logger.error(f"main.py errors: {''.join(stderr_lines)}")
        if process.returncode != 0:
            logger.error(f"main.py exited with code {process.returncode}")
    except subprocess.TimeoutExpired:
        logger.error("main.py timed out after 60 seconds")
        print("main.py timed out after 60 seconds")
    except Exception as e:
        logger.error(f"Error executing main.py: {e}")
        print(f"Error executing main.py: {e}")

def main():
    """Main function for the launcher."""
    logger.info("Starting network automation launcher")

    if not os.path.exists(ACTIONS_FILE):
        logger.error(f"actions.yml not found at {ACTIONS_FILE}")
        return

    actions_data = load_yaml_file(ACTIONS_FILE)
    actions = actions_data.get('actions', [])

    if not actions:
        logger.error("No actions defined in actions.yml")
        return

    while True:
        display_menu(actions)
        try:
            choice = input(f"Enter your choice (1-{len(actions)}): ")
            choice = int(choice)
            if 1 <= choice <= len(actions):
                action = actions[choice - 1]
                template_file = action.get('template_file')
                action_name = action.get('name')
                if update_hosts_data(template_file, action_name):
                    execute_main_py(choice)
                else:
                    logger.error("Failed to update hosts_data.yml. Aborting")
                    print("Failed to update hosts_data.yml. Aborting.")
            else:
                print(f"Invalid choice. Please select between 1 and {len(actions)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            logger.info("Exiting launcher")
            print("\nExiting launcher.")
            break

if __name__ == "__main__":
    main()
