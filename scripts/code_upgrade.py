import os
import logging
import json
from datetime import datetime
from typing import List, Dict
from jnpr.junos import Device
from jnpr.junos.utils.sw import SW
from jnpr.junos.exception import ConnectError
from scripts.utils import load_yaml_file, save_yaml_file, capture_device_state, compare_states
from scripts.connect_to_hosts import connect_to_hosts, disconnect_from_hosts

logger = logging.getLogger(__name__)

def display_products(products: List[Dict]) -> int:
    """Display a menu of products and return the user's choice."""
    print("\nSelect a product:")
    print("----------------------------------------")
    print("| Option | Product                 |")
    print("----------------------------------------")
    for i, product in enumerate(products, 1):
        print(f"| {i:<6} | {product['product']:<22} |")
    print("----------------------------------------")
    max_retries = 5
    retries = 0
    while retries < max_retries:
        try:
            choice = input(f"Enter your choice (1-{len(products)}): ").strip()
            logger.info(f"Raw product input received: '{choice}'")
            if not choice:
                logger.error("Empty input received")
                print(f"Invalid choice. Please enter a number between 1 and {len(products)}")
                retries += 1
                continue
            choice = int(choice)
            if 1 <= choice <= len(products):
                logger.info(f"Valid product choice selected: {choice}")
                return choice - 1
            logger.error(f"Choice out of range: {choice}")
            print(f"Invalid choice. Please enter a number between 1 and {len(products)}")
            retries += 1
        except ValueError:
            logger.error(f"Non-numeric input: '{choice}'")
            print(f"Invalid choice. Please enter a number between 1 and {len(products)}")
            retries += 1
        except EOFError:
            logger.error("EOF received during input")
            print(f"Input interrupted. Please enter a number between 1 and {len(products)}")
            retries += 1
        except KeyboardInterrupt:
            logger.info("Product selection interrupted by user (Ctrl+C)")
            print("\nProgram interrupted by user. Exiting.")
            return None
    logger.error(f"Max retries ({max_retries}) reached in display_products")
    print("Too many invalid attempts. Exiting.")
    return None

def display_releases(product: Dict) -> str:
    """Display available releases for a product and return the selected release."""
    releases = [product['release']]
    print("\nAvailable releases:")
    print("----------------------------------------")
    print("| Option | Release                 |")
    print("----------------------------------------")
    for i, release in enumerate(releases, 1):
        print(f"| {i:<6} | {release:<22} |")
    print("----------------------------------------")
    max_retries = 5
    retries = 0
    while retries < max_retries:
        try:
            choice = input(f"Enter your choice (1-{len(releases)}): ").strip()
            logger.info(f"Raw release input received: '{choice}'")
            if not choice:
                logger.error("Empty input received")
                print(f"Invalid choice. Please enter a number between 1 and {len(releases)}")
                retries += 1
                continue
            choice = int(choice)
            if 1 <= choice <= len(releases):
                logger.info(f"Valid release choice selected: {choice}")
                return releases[choice - 1]
            logger.error(f"Choice out of range: {choice}")
            print(f"Invalid choice. Please enter a number between 1 and {len(releases)}")
            retries += 1
        except ValueError:
            logger.error(f"Non-numeric input: '{choice}'")
            print(f"Invalid choice. Please enter a number between 1 and {len(releases)}")
            retries += 1
        except EOFError:
            logger.error("EOF received during input")
            print(f"Input interrupted. Please enter a number between 1 and {len(releases)}")
            retries += 1
        except KeyboardInterrupt:
            logger.info("Release selection interrupted by user (Ctrl+C)")
            print("\nProgram interrupted by user. Exiting.")
            return None
    logger.error(f"Max retries ({max_retries}) reached in display_releases")
    print("Too many invalid attempts. Exiting.")
    return None

def get_host_ips() -> List[str]:
    """Prompt user to read hosts from upgrade_hosts.yml or enter IPs manually."""
    host_ips = []
    upgrade_hosts_file = os.path.join(os.getenv("VECTOR_PY_DIR", "/home/nikos/github/ngeran/vector-py"), 'data/upgrade_hosts.yml')

    print("\nDo you want to read hosts from upgrade_hosts.yml? (y/n)")
    try:
        use_file = input().strip().lower()
        logger.info(f"User chose to read from file: {use_file}")

        if use_file == 'y' and os.path.exists(upgrade_hosts_file):
            try:
                hosts_data = load_yaml_file(upgrade_hosts_file)
                host_ips = hosts_data.get('hosts', [])
                logger.info(f"Loaded hosts from {upgrade_hosts_file}: {host_ips}")
                print(f"Loaded hosts: {host_ips}")
            except Exception as e:
                logger.error(f"Error reading {upgrade_hosts_file}: {e}")
                print(f"Error reading {upgrade_hosts_file}: {e}")

        while True:
            print("\nEnter a host IP (or press Enter to finish):")
            ip = input().strip()
            if not ip:
                break
            if '.' in ip and all(part.isdigit() for part in ip.split('.')):
                host_ips.append(ip)
                logger.info(f"Added host IP: {ip}")
            else:
                logger.error(f"Invalid IP address: {ip}")
                print(f"Invalid IP address: {ip}")

        if host_ips:
            try:
                save_yaml_file(upgrade_hosts_file, {'hosts': host_ips})
                logger.info(f"Saved hosts to {upgrade_hosts_file}: {host_ips}")
                print(f"Saved hosts to {upgrade_hosts_file}")
            except Exception as e:
                logger.error(f"Error saving {upgrade_hosts_file}: {e}")
                print(f"Error saving {upgrade_hosts_file}: {e}")

        return host_ips
    except KeyboardInterrupt:
        logger.info("Host input interrupted by user (Ctrl+C)")
        print("\nProgram interrupted by user. Exiting.")
        return []

def get_credentials() -> tuple:
    """Prompt user for username and password."""
    try:
        print("\nEnter username:")
        username = input().strip()
        print("Enter password:")
        password = input().strip()
        logger.info(f"Received credentials - username: {username}")
        return username, password
    except KeyboardInterrupt:
        logger.info("Credential input interrupted by user (Ctrl+C)")
        print("\nProgram interrupted by user. Exiting.")
        return "", ""

def code_upgrade():
    """Perform code upgrade on selected devices and capture state."""
    try:
        logger.info("Starting code_upgrade action")
        print("DEBUG: Starting code_upgrade")

        # Load upgrade_data.yml
        upgrade_data_file = os.path.join(os.getenv("VECTOR_PY_DIR", "/home/nikos/github/ngeran/vector-py"), 'data/upgrade_data.yml')
        upgrade_data = load_yaml_file(upgrade_data_file)
        products = upgrade_data.get('products', [])[0].get('switches', [])
        logger.info(f"Loaded products: {[p['product'] for p in products]}")

        # Display product menu
        product_idx = display_products(products)
        if product_idx is None:
            logger.error("No product selected")
            return

        selected_product = products[product_idx]
        logger.info(f"Selected product: {selected_product['product']}")

        # Display release menu
        selected_release = display_releases(selected_product)
        if selected_release is None:
            logger.error("No release selected")
            return
        logger.info(f"Selected release: {selected_release}")

        # Get host IPs
        host_ips = get_host_ips()
        if not host_ips:
            logger.error("No host IPs provided")
            print("Error: No host IPs provided")
            return
        logger.info(f"Host IPs: {host_ips}")

        # Get credentials
        username, password = get_credentials()
        if not username or not password:
            logger.error("No credentials provided")
            print("Error: No credentials provided")
            return

        # Connect to hosts
        connections = connect_to_hosts(host_ips, username, password)
        if not connections:
            logger.error("No devices connected for code upgrade")
            print("No devices connected for code upgrade")
            return

        # Prepare state storage
        state_data = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        state_file = os.path.join(os.getenv("VECTOR_PY_DIR", "/home/nikos/github/ngeran/vector-py"), f'reports/upgrade_state_{timestamp}.json')
        os.makedirs(os.path.dirname(state_file), exist_ok=True)

        # Capture pre-upgrade state
        for dev in connections:
            hostname = dev.hostname
            state_data[hostname] = {'pre_upgrade': capture_device_state(dev, hostname)}
            logger.info(f"Pre-upgrade state captured for {hostname}")

        # Perform upgrade
        image_path = f"/var/tmp/{selected_product['os']}"
        for dev in connections:
            hostname = dev.hostname
            try:
                logger.info(f"Starting upgrade on {hostname}")
                print(f"DEBUG: Upgrading {hostname} with {image_path}")
                sw = SW(dev)
                result = sw.install(package=image_path, validate=True, progress=True)
                if result:
                    logger.info(f"Upgrade successful on {hostname}")
                    print(f"Upgrade successful on {hostname}")
                    # Reboot device
                    sw.reboot()
                    logger.info(f"Rebooted {hostname} after upgrade")
                    print(f"Rebooted {hostname} after upgrade")
                else:
                    logger.error(f"Upgrade failed on {hostname}")
                    print(f"Upgrade failed on {hostname}")
                    state_data[hostname]['upgrade_status'] = 'failed'
                    continue

                # Reconnect after reboot (wait for device to come back)
                try:
                    dev.close()
                    dev = Device(host=hostname, user=username, password=password)
                    dev.open(timeout=300)
                    logger.info(f"Reconnected to {hostname} after reboot")
                except ConnectError as e:
                    logger.error(f"Failed to reconnect to {hostname} after reboot: {e}")
                    print(f"Failed to reconnect to {hostname} after reboot: {e}")
                    state_data[hostname]['upgrade_status'] = 'failed_reconnect'
                    continue

                # Capture post-upgrade state
                state_data[hostname]['post_upgrade'] = capture_device_state(dev, hostname)
                logger.info(f"Post-upgrade state captured for {hostname}")
                state_data[hostname]['upgrade_status'] = 'successful'

                # Compare states
                differences = compare_states(state_data[hostname]['pre_upgrade'], state_data[hostname]['post_upgrade'])
                state_data[hostname]['differences'] = differences
                if differences:
                    logger.info(f"State differences found for {hostname}: {differences}")
                    print(f"\nState differences for {hostname}:")
                    for key, diff in differences.items():
                        print(f"{key.replace('_', ' ').title()}:")
                        print(f"  Pre: {diff['pre'][:100]}...")
                        print(f"  Post: {diff['post'][:100]}...")
                        print(f"  Note: {diff['note']}")
                else:
                    logger.info(f"No state differences for {hostname}")
                    print(f"No state differences for {hostname}")

            except Exception as e:
                logger.error(f"Error upgrading {hostname}: {e}")
                print(f"Error upgrading {hostname}: {e}")
                state_data[hostname]['upgrade_status'] = f'failed: {str(e)}'

        # Save state data to JSON
        try:
            with open(state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
            logger.info(f"Saved state data to {state_file}")
            print(f"Saved state data to {state_file}")
        except Exception as e:
            logger.error(f"Error saving state file {state_file}: {e}")
            print(f"Error saving state file {state_file}: {e}")

        disconnect_from_hosts(connections)
        logger.info("Code upgrade action completed")
        print("DEBUG: Code upgrade completed")

    except KeyboardInterrupt:
        logger.info("Code upgrade interrupted by user (Ctrl+C)")
        print("\nProgram interrupted by user. Exiting.")
    except Exception as e:
        logger.error(f"Error in code_upgrade: {e}")
        print(f"Error: {e}")
