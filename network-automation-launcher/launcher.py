import os
import subprocess
import yaml
from typing import List, Dict

# Path to the vector-py project
VECTOR_PY_DIR = "/home/nikos/github/ngeran/vector-py"
ACTIONS_FILE = os.path.join(VECTOR_PY_DIR, "data", "actions.yml")
HOSTS_DATA_FILE = os.path.join(VECTOR_PY_DIR, "data", "hosts_data.yml")
MAIN_PY = os.path.join(VECTOR_PY_DIR, "main.py")

def load_yaml_file(file_path: str) -> Dict:
    """Load a YAML file and return its contents."""
    try:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
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

def update_hosts_data(template_file: str):
    """Update hosts_data.yml with the selected template file."""
    hosts_data = load_yaml_file(HOSTS_DATA_FILE)
    if not hosts_data:
        print("Failed to load hosts_data.yml.")
        return False
    hosts_data['template_file'] = template_file
    try:
        with open(HOSTS_DATA_FILE, 'w') as f:
            yaml.safe_dump(hosts_data, f)
        print(f"Updated hosts_data.yml with template: {template_file}")
        return True
    except Exception as e:
        print(f"Error updating hosts_data.yml: {e}")
        return False

def execute_main_py(choice: int):
    """Execute main.py with the selected choice."""
    try:
        # Run main.py and pass the choice via stdin
        process = subprocess.run(
            ["python", MAIN_PY],
            input=str(choice),
            text=True,
            capture_output=True,
            cwd=VECTOR_PY_DIR
        )
        print(process.stdout)
        if process.stderr:
            print(f"Errors: {process.stderr}")
        if process.returncode != 0:
            print(f"main.py exited with code {process.returncode}")
    except Exception as e:
        print(f"Error executing main.py: {e}")

def main():
    """Main function for the launcher."""
    actions_data = load_yaml_file(ACTIONS_FILE)
    actions = actions_data.get('actions', [])

    if not actions:
        print("No actions defined in actions.yml.")
        return

    while True:
        display_menu(actions)
        choice = input(f"Enter your choice (1-{len(actions)}): ")
        try:
            choice = int(choice)
            if 1 <= choice <= len(actions):
                action = actions[choice - 1]
                template_file = action.get('template_file')
                if template_file and update_hosts_data(action['name']):
                    execute_main_py(choice)
                else:
                    print("Failed to update hosts_data.yml. Aborting.")
            else:
                print(f"Invalid choice. Please select between 1 and {len(actions)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            print("\nExiting launcher.")
            break

if __name__ == "__main__":
    main()
