import os
import sys
import logging
from scripts.network_automation import display_menu, load_yaml_file
from scripts.git_operations import git_commit_and_push

# Add vector-py directory to sys.path
VECTOR_PY_DIR = os.getenv("VECTOR_PY_DIR", "/home/nikos/github/ngeran/vector-py")
if VECTOR_PY_DIR not in sys.path:
    sys.path.insert(0, VECTOR_PY_DIR)


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
        if not choice:
            logger.error("Invalid action choice")
            print("Invalid choice. Exiting.")
            return

        selected_action = actions[choice - 1]
        action_name = selected_action['name']
        logger.info(f"Selected action: {action_name}")

        # Prompt for local execution or GitHub push
        print("\nChoose execution mode:")
        print("1. Execute locally")
        print("2. Push to GitHub")
        mode_choice = input("Enter your choice (1-2): ").strip()

        if mode_choice not in ['1', '2']:
            logger.error(f"Invalid execution mode: {mode_choice}")
            print("Invalid choice. Exiting.")
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
