# /home/nikos/github/ngeran/vectautomation/scripts/network_automation.py
import os
import yaml
from scripts.utils import merge_host_data, load_yaml_file
from scripts.connect_to_hosts import connect_to_hosts, disconnect_from_hosts
from scripts.actions import execute_actions

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def update_hosts_data_template(template: str, hosts_data_file: str):
    """Update the template field in hosts_data.yml."""
    try:
        with open(hosts_data_file, 'r') as f:
            data = yaml.safe_load(f) or {}

        data['template'] = template

        with open(hosts_data_file, 'w') as f:
            yaml.safe_dump(data, f, default_flow_style=False)

        print(f"Updated hosts_data.yml with template: {template}")
    except Exception as error:
        print(f"Failed to update hosts_data.yml: {error}")
        raise

def prompt_user_for_template(actions: list):
    """Prompt user to select an action from actions.yml and return the template name."""
    if not actions:
        print("No actions defined in actions.yml.")
        raise ValueError("Empty actions list")

    # Create simple ASCII table
    print("\nSelect an action:")
    print("-" * 40)
    print("| Option | Action                  |")
    print("-" * 40)
    for idx, action in enumerate(actions, 1):
        print(f"| {idx:<6} | {action['display_name']:<23} |")
    print("-" * 40)

    valid_choices = [str(idx) for idx in range(1, len(actions) + 1)]
    while True:
        choice = input(f"Enter your choice (1-{len(actions)}): ").strip()
        if choice in valid_choices:
            return actions[int(choice) - 1]['name']
        print(f"Invalid choice. Please enter a number between 1 and {len(actions)}.")

def main():
    """Execute the action specified by user input in hosts_data.yml."""
    try:
        inventory_file = os.path.join(SCRIPT_DIR, "../data/inventory.yml")
        hosts_data_file = os.path.join(SCRIPT_DIR, "../data/hosts_data.yml")
        actions_file = os.path.join(SCRIPT_DIR, "../data/actions.yml")

        # Load actions.yml
        actions_data = load_yaml_file(actions_file)
        actions = actions_data.get('actions', [])
        if not actions:
            print("No actions defined in actions.yml.")
            return

        # Prompt user and update template
        template = prompt_user_for_template(actions)
        update_hosts_data_template(template, hosts_data_file)

        merged_data = merge_host_data(inventory_file, hosts_data_file)
        if not merged_data:
            print("Failed to load or merge data. Exiting.")
            return

        hosts_data = load_yaml_file(hosts_data_file)
        valid_templates = [action['name'] for action in actions]

        if template not in valid_templates:
            print(f"Invalid template '{template}' in hosts_data.yml. Valid templates are:", valid_templates)
            return

        username = merged_data['username']
        password = merged_data['password']
        hosts = merged_data['hosts']
        host_ips = [host['ip_address'] for host in hosts_data.get('hosts', [])]

        execute_actions(
            actions=[template],
            username=username,
            password=password,
            host_ips=host_ips,
            hosts=hosts,
            connect_to_hosts=connect_to_hosts,
            disconnect_from_hosts=disconnect_from_hosts
        )

        print(f"Completed action: {template}")

    except KeyboardInterrupt:
        print("Script interrupted by user.")
        return
    except Exception as error:
        print(f"Error during execution: {error}")

if __name__ == "__main__":
    main()
