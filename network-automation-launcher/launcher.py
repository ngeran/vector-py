import os
import sys
import logging

# Debug sys.path
print("Initial sys.path:", sys.path)

# Add vector-py directory to sys.path
VECTOR_PY_DIR = os.getenv("VECTOR_PY_DIR", "/home/nikos/github/ngeran/vector-py")
if VECTOR_PY_DIR not in sys.path:
    sys.path.insert(0, VECTOR_PY_DIR)
    print(f"Added {VECTOR_PY_DIR} to sys.path")

print("Updated sys.path:", sys.path)

from scripts.network_automation import display_menu, load_yaml_file
from scripts.git_operations import git_commit_and_push

# Configure logging
logging.basicConfig(
    filename=os.path.join(VECTOR_PY_DIR, 'network_automation.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the network automation launcher."""
    try:
        # Load actions from actions.yml
        actions_file = os.path.join(VECTOR_PY_DIR, 'data/actions.yml')
        actions_data = load_yaml_file(actions_file)
        actions = actions_data.get('actions', [])

        # Display menu and get user choice
        choice = display_menu(actions)
        if choice is None or choice not in range(1, len(actions) + 1):
            logger.error("Failed to get valid action choice")
            print("Failed to select a valid action. Exiting.")
            return

        selected_action = actions[choice - 1]
        action_name = selected_action['name']
        logger.info(f"Selected action: {action_name}")

        # Prompt for local execution or GitHub push
        max_retries = 5
        retries = 0
        while retries < max_retries:
            print("\nChoose execution mode:")
            print("1. Execute locally")
            print("2. Push to GitHub")
            try:
                mode_choice = input("Enter your choice (1-2): ").strip()
                logger.info(f"Raw mode input received: '{mode_choice}'")
                if mode_choice in ['1', '2']:
                    break
                logger.error(f"Invalid execution mode: {mode_choice}")
                print("Invalid choice. Please enter 1 or 2")
                retries += 1
            except EOFError:
                logger.error("EOF received for mode choice")
                print("Input interrupted. Please enter 1 or 2")
                retries += 1
        else:
            logger.error(f"Max retries ({max_retries}) reached for mode choice")
            print("Too many invalid attempts. Exiting.")
            return

        if mode_choice == '2':
            # Files to commit
            files_to_commit = [
                "scripts/launcher.py",
                "scripts/network_automation.py",
                "scripts/connect_to_hosts.py",
                "scripts/actions.py",
                "scripts/interface_actions.py",
                "scripts/diagnostic_actions.py",
                "scripts/route_monitor.py",
                "scripts/utils.py",
                "scripts/main.py",
                "scripts/junos_actions.py",
                "data/hosts_data.yml",
                "data/actions.yml",
                "data/action_map.yml",
                "data/inventory.yml",
                "data/git_config.yml",
                "templates/interface_template.j2"
            ]
            repo_path = VECTOR_PY_DIR
            logger.info(f"Preparing to push to GitHub for action: {action_name}")

            # Commit and push
            success = git_commit_and_push(repo_path, action_name, files_to_commit)
            if success:
                logger.info(f"Git push completed for action: {action_name}")
                print(f"Code pushed to GitHub for action: {action_name}")
            else:
                logger.error(f"Git push failed for action: {action_name}")
                print(f"Git push failed for action: {action_name}")
                return

        # Execute locally
        if mode_choice == '1':
            logger.info(f"Executing action {action_name} locally")
            from scripts.network_automation import main as network_main
            network_main(action_name=action_name)

    except Exception as e:
        logger.error(f"Error in launcher: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
