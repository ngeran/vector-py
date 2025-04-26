import os
import logging
import time
from typing import List, Dict
from jnpr.junos import Device
from jnpr.junos.utils.sw import SW
from jnpr.junos.exception import ConnectError, RpcTimeoutError
from scripts.utils import load_yaml_file, save_yaml_file
from scripts.connect_to_hosts import connect_to_hosts, disconnect_from_hosts

logger = logging.getLogger(__name__)

def display_vendors(vendors: List[Dict]) -> int:
    """Display a menu of vendors and return the user's choice."""
    print("\nSelect a vendor:")
    print("----------------------------------------")
    print("| Option | Vendor                  |")
    print("----------------------------------------")
    for i, vendor in enumerate(vendors, 1):
        print(f"| {i:<6} | {vendor['vendor-name']:<22} |")
    print("----------------------------------------")
    max_retries = 5
    retries = 0
    while retries < max_retries:
        try:
            choice = input(f"Select a vendor (1-{len(vendors)}): ").strip()
            logger.info(f"Raw vendor input received: '{choice}'")
            if not choice:
                logger.error("Empty input received")
                print(f"Invalid choice. Please enter a number between 1 and {len(vendors)}")
                retries += 1
                continue
            choice = int(choice)
            if 1 <= choice <= len(vendors):
                logger.info(f"Valid vendor choice selected: {choice}")
                return choice - 1
            logger.error(f"Choice out of range: {choice}")
            print(f"Invalid choice. Please enter a number between 1 and {len(vendors)}")
            retries += 1
        except ValueError:
            logger.error(f"Non-numeric input: '{choice}'")
            print(f"Invalid choice. Please enter a number between 1 and {len(vendors)}")
            retries += 1
        except EOFError:
            logger.error("EOF received during input")
            print(f"Input interrupted. Please enter a number between 1 and {len(vendors)}")
            retries += 1
        except KeyboardInterrupt:
            logger.info("Vendor selection interrupted by user (Ctrl+C)")
            print("\nProgram interrupted by user. Exiting.")
            return None
    logger.error(f"Max retries ({max_retries}) reached in display_vendors")
    print("Too many invalid attempts. Exiting.")
    return None

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
            choice = input(f"Select a product (1-{len(products)}): ").strip()
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

def display_releases(product: Dict) -> Dict:
    """Display available releases for a product and return the selected release dictionary."""
    releases = product.get('releases', [])
    if not releases:
        logger.error(f"No releases found for product {product['product']}")
        print(f"Error: No releases found for product {product['product']}")
        return None
    print("\nAvailable releases:")
    print("----------------------------------------")
    print("| Option | Release                 |")
    print("----------------------------------------")
    for i, release in enumerate(releases, 1):
        print(f"| {i:<6} | {release['release']:<22} |")
    print("----------------------------------------")
    max_retries = 5
    retries = 0
    while retries < max_retries:
        try:
            choice = input(f"Select a release (1-{len(releases)}): ").strip()
            logger.info(f"Raw release input received: '{choice}'")
            if not choice:
                logger.error("Empty input received")
                print(f"Invalid choice. Please enter a number between 1 and {len(releases)}")
                retries += 1
                continue
            choice = int(choice)
            if 1 <= choice <= len(releases):
                logger.info(f"Valid release choice selected: {releases[choice - 1]['release']}")
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

    try:
        choice = input("Read hosts from upgrade_hosts.yml? (y/n): ").strip().lower()
        logger.info(f"User chose to read from file: {choice}")

        if choice == 'y' and os.path.exists(upgrade_hosts_file):
            try:
                hosts_data = load_yaml_file(upgrade_hosts_file)
                host_ips = hosts_data.get('hosts', [])
                logger.info(f"Loaded hosts from {upgrade_hosts_file}: {host_ips}")
                print(f"Loaded hosts: {host_ips}")
            except Exception as e:
                logger.error(f"Error reading {upgrade_hosts_file}: {e}")
                print(f"Error reading {upgrade_hosts_file}: {e}")

        while True:
            ip = input("Enter a host IP (or press Enter to finish): ").strip()
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
        username = input("Username: ").strip()
        password = input("Password: ").strip()
        logger.info(f"Received credentials - username: {username}")
        return username, password
    except KeyboardInterrupt:
        logger.info("Credential input interrupted by user (Ctrl+C)")
        print("\nProgram interrupted by user. Exiting.")
        return "", ""

def probe_device(dev: Device, hostname: str, username: str, password: str) -> bool:
    """Probe the device to check if it's reachable and responsive."""
    print(f"Probing device {hostname}...")
    logger.info(f"Probing device {hostname}")
    try:
        if not dev.connected:
            dev = Device(host=hostname, user=username, password=password)
            dev.open(timeout=300)
        with dev:
            dev.cli("show version", warning=False)
        print(f"Device {hostname} is reachable and responsive.")
        logger.info(f"Device {hostname} is reachable and responsive")
        return True
    except (ConnectError, Exception) as e:
        print(f"Failed to probe {hostname}: {e}")
        logger.error(f"Failed to probe {hostname}: {e}")
        return False

def check_image_exists(dev: Device, image_path: str, hostname: str) -> bool:
    """Check if the upgrade image exists on the device."""
    try:
        with dev:
            image_name = image_path.split('/')[-1]
            result = dev.cli("file list /var/tmp/", warning=False)
            if image_name in result.split():
                logger.info(f"Image {image_path} found on {hostname}")
                print(f"Image {image_path} found on {hostname}")
                return True
            else:
                logger.error(f"Image {image_path} not found on {hostname}")
                print(f"Error: Image {image_path} not found on {hostname}")
                return False
    except Exception as e:
        logger.error(f"Error checking image on {hostname}: {e}")
        print(f"Error checking image on {hostname}: {e}")
        return False

def check_pending_install(dev: Device, image_path: str, hostname: str) -> bool:
    """Check if there is a pending or active install on the device."""
    logger.debug(f"Starting pending install check on {hostname}")
    try:
        with dev:
            dev.timeout = 30  # Reduced timeout
            logger.debug(f"Executing 'show system software information' on {hostname}")
            result = dev.cli("show system software information", warning=False)
            logger.debug(f"Software information result on {hostname}: {result}")
            if "installation in progress" in result.lower() or "pending" in result.lower() or "package -X update" in result.lower():
                logger.error(f"Active or pending install detected on {hostname}")
                print(f"Error: Active or pending install detected on {hostname}.")
                choice = input("Resolve pending install? (1: Reboot, 2: Rollback, 3: Skip): ").strip()
                logger.info(f"User chose pending install action: {choice}")
                if choice == '1':
                    print(f"Initiating reboot on {hostname}...")
                    dev.cli("request system reboot", warning=False)
                    logger.info(f"Reboot initiated on {hostname} to resolve pending install")
                    print(f"Please wait 5-10 minutes for {hostname} to reboot, then rerun the script.")
                    return True
                elif choice == '2':
                    print(f"Initiating rollback on {hostname}...")
                    dev.cli("request system software rollback", warning=False)
                    logger.info(f"Rollback initiated on {hostname} to resolve pending install")
                    print(f"Rollback completed on {hostname}. Proceeding with upgrade.")
                    return False
                else:
                    logger.info(f"User chose to skip pending install on {hostname}")
                    print(f"Skipping upgrade for {hostname} due to pending install.")
                    return True
            logger.debug(f"No pending install detected on {hostname}")
            return False
    except RpcTimeoutError as e:
        logger.warning(f"Timeout checking pending install on {hostname}: {e}. Assuming active install.")
        print(f"Warning: Timeout checking pending install on {hostname}: {e}. Assuming active install.")
        choice = input("Resolve pending install? (1: Reboot, 2: Rollback, 3: Skip): ").strip()
        logger.info(f"User chose pending install action: {choice}")
        if choice == '1':
            print(f"Initiating reboot on {hostname}...")
            dev.cli("request system reboot", warning=False)
            logger.info(f"Reboot initiated on {hostname} to resolve pending install")
            print(f"Please wait 5-10 minutes for {hostname} to reboot, then rerun the script.")
            return True
        elif choice == '2':
            print(f"Initiating rollback on {hostname}...")
            dev.cli("request system software rollback", warning=False)
            logger.info(f"Rollback initiated on {hostname} to resolve pending install")
            print(f"Rollback completed on {hostname}. Proceeding with upgrade.")
            return False
        else:
            logger.info(f"User chose to skip pending install on {hostname}")
            print(f"Skipping upgrade for {hostname} due to pending install.")
            return True
    except Exception as e:
        logger.warning(f"Could not check pending install on {hostname}: {e}. Proceeding with caution.")
        print(f"Warning: Could not check pending install on {hostname}: {e}. Proceeding with caution.")
        return False

def progress_callback(dev: Device, report: str) -> None:
    """Callback function to report progress during software installation."""
    logger.info(f"Progress on {dev.hostname}: {report}")
    print(f"Progress on {dev.hostname}: {report}")

def code_upgrade():
    """Perform code upgrade on selected devices with probing and user messages."""
    upgrade_status = []
    try:
        logger.info("Starting code_upgrade action")
        print("Starting code upgrade process...")

        # Load upgrade_data.yml
        upgrade_data_file = os.path.join(os.getenv("VECTOR_PY_DIR", "/home/nikos/github/ngeran/vector-py"), 'data/upgrade_data.yml')
        upgrade_data = load_yaml_file(upgrade_data_file)
        if not upgrade_data:
            logger.error("Failed to load upgrade_data.yml")
            print("Error: Failed to load upgrade_data.yml")
            return
        vendors = upgrade_data.get('products', [])
        logger.info(f"Loaded vendors: {[v['vendor-name'] for v in vendors]}")

        # Display vendor menu
        vendor_idx = display_vendors(vendors)
        if vendor_idx is None:
            logger.error("No vendor selected")
            return
        selected_vendor = vendors[vendor_idx]
        logger.info(f"Selected vendor: {selected_vendor['vendor-name']}")
        print(f"Selected vendor: {selected_vendor['vendor-name']}")

        # Aggregate products from switches, firewalls, and routers
        products = []
        for device_type in ['switches', 'firewalls', 'routers']:
            products.extend(selected_vendor.get(device_type, []))
        logger.info(f"Loaded products: {[p['product'] for p in products]}")

        # Display product menu
        product_idx = display_products(products)
        if product_idx is None:
            logger.error("No product selected")
            return
        selected_product = products[product_idx]
        logger.info(f"Selected product: {selected_product['product']}")
        print(f"Selected product: {selected_product['product']}")

        # Display release menu
        selected_release = display_releases(selected_product)
        if selected_release is None:
            logger.error("No release selected")
            return
        logger.info(f"Selected release: {selected_release['release']}")
        print(f"Selected release: {selected_release['release']}")

        # Get host IPs
        host_ips = get_host_ips()
        if not host_ips:
            logger.error("No host IPs provided")
            print("Error: No host IPs provided")
            return
        logger.info(f"Host IPs: {host_ips}")
        print(f"Hosts to upgrade: {host_ips}")

        # Get credentials
        username, password = get_credentials()
        if not username or not password:
            logger.error("No credentials provided")
            print("Error: No credentials provided")
            return

        # Connect to hosts
        print("Connecting to devices...")
        connections = connect_to_hosts(host_ips, username, password)
        if not connections:
            logger.error("No devices connected for code upgrade")
            print("Error: No devices connected for code upgrade")
            return
        logger.info(f"Connected to devices: {[dev.hostname for dev in connections]}")

        # Perform upgrade
        image_path = f"/var/tmp/{selected_release['os']}"
        target_version = selected_release['release']
        for dev in connections:
            hostname = dev.hostname
            status = {'hostname': hostname, 'success': False, 'error': None}
            try:
                # Increase command timeout
                dev.timeout = 300

                # Probe device before upgrade
                if not probe_device(dev, hostname, username, password):
                    logger.error(f"Skipping upgrade for {hostname} due to probe failure")
                    print(f"Skipping upgrade for {hostname} due to probe failure")
                    status['error'] = "Probe failure"
                    upgrade_status.append(status)
                    continue

                # Check current Junos version
                try:
                    with dev:
                        version_output = dev.cli("show version", warning=False)
                        logger.debug(f"Version output for {hostname}: {version_output}")
                        current_version = None
                        for line in version_output.splitlines():
                            if "JUNOS Software Release" in line:
                                current_version = line.split('[')[-1].strip(']').strip()
                                break
                        if current_version:
                            logger.info(f"Current Junos version on {hostname}: {current_version}")
                            print(f"Current Junos version on {hostname}: {current_version}")
                            if current_version == target_version:
                                logger.info(f"{hostname} already on target version {target_version}. Skipping upgrade.")
                                print(f"{hostname} already on target version {target_version}. Skipping upgrade.")
                                status['success'] = True
                                upgrade_status.append(status)
                                continue
                            # Warn about potential downgrade
                            current_parts = [int(x) if x.isdigit() else x for x in current_version.replace('-', '.').split('.')]
                            target_parts = [int(x) if x.isdigit() else x for x in target_version.replace('-', '.').split('.')]
                            if current_parts > target_parts:
                                logger.warning(f"Selected version {target_version} is older than current {current_version} on {hostname}")
                                print(f"Warning: Selected version {target_version} is older than current {current_version} on {hostname}.")
                                choice = input("Proceed with downgrade? (y/n): ").strip().lower()
                                if choice != 'y':
                                    logger.info(f"User chose to skip downgrade on {hostname}")
                                    print(f"Skipping upgrade for {hostname} to avoid downgrade.")
                                    status['success'] = True
                                    upgrade_status.append(status)
                                    continue
                        else:
                            logger.warning(f"Could not determine Junos version on {hostname}")
                            print(f"Warning: Could not determine Junos version on {hostname}")
                except Exception as e:
                    logger.warning(f"Failed to check Junos version on {hostname}: {e}. Proceeding with upgrade.")
                    print(f"Warning: Failed to check Junos version on {hostname}: {e}. Proceeding with upgrade.")

                # Check if image exists
                if not check_image_exists(dev, image_path, hostname):
                    logger.error(f"Skipping upgrade for {hostname} due to missing image")
                    print(f"Skipping upgrade for {hostname} due to missing image")
                    status['error'] = "Missing image"
                    upgrade_status.append(status)
                    continue

                # Check for pending install
                if check_pending_install(dev, image_path, hostname):
                    logger.error(f"Skipping upgrade for {hostname} due to unresolved pending install")
                    status['error'] = "Pending install"
                    upgrade_status.append(status)
                    continue

                # Perform upgrade using SW class
                logger.debug(f"Starting software upgrade on {hostname} with image {image_path}")
                print(f"Installing upgrade on {hostname} with image {image_path}...")
                try:
                    sw = SW(dev)
                    logger.debug(f"SW.install parameters: package={image_path}, validate=False, no_copy=True, timeout=600")
                    ok = sw.install(
                        package=image_path,
                        validate=False,
                        no_copy=True,
                        progress=progress_callback,
                        timeout=600
                    )
                    logger.debug(f"Software install result on {hostname}: {ok}")
                    if not ok:
                        raise ValueError("Software installation failed")
                    logger.info(f"Software upgrade completed on {hostname}")
                    print(f"Software upgrade completed on {hostname}")
                except TypeError as e:
                    logger.error(f"TypeError during software upgrade on {hostname}: {e}")
                    print(f"Error: TypeError during software upgrade on {hostname}: {e}. Falling back to CLI method...")
                    try:
                        result = dev.cli(f"request system software add {image_path} no-validate", warning=False, timeout=600)
                        logger.debug(f"CLI upgrade result on {hostname}: {result}")
                        if "error" in result.lower() or "failed" in result.lower():
                            if "Could not format alternate root" in result:
                                logger.error(f"Storage failure on {hostname}: {result}")
                                print(f"Error: Storage failure on {hostname}: {result}")
                                print("Recommendation: Check disk health with 'show system storage' and 'show system alarms'. Consider USB recovery or Juniper support.")
                                status['error'] = "Storage failure: Could not format alternate root"
                            elif "Not enough space in /var" in result:
                                logger.error(f"Insufficient disk space in /var on {hostname}: {result}")
                                print(f"Error: Insufficient disk space in /var on {hostname}: {result}")
                                print("Recommendation: Run 'request system storage cleanup' or manually remove files from /var.")
                                status['error'] = "Insufficient disk space in /var"
                            else:
                                logger.error(f"CLI upgrade failed on {hostname}: {result}")
                                print(f"Error: CLI upgrade failed on {hostname}: {result}")
                                status['error'] = f"CLI upgrade failed: {result}"
                            upgrade_status.append(status)
                            continue
                        logger.info(f"CLI software upgrade completed on {hostname}")
                        print(f"CLI software upgrade completed on {hostname}")
                    except Exception as cli_e:
                        logger.error(f"CLI upgrade failed on {hostname}: {cli_e}")
                        print(f"Error: CLI upgrade failed on {hostname}: {cli_e}")
                        error_msg = str(cli_e)
                        if "Could not format alternate root" in error_msg:
                            print("Recommendation: Check disk health with 'show system storage' and 'show system alarms'. Consider USB recovery or Juniper support.")
                            status['error'] = "Storage failure: Could not format alternate root"
                        elif "Not enough space in /var" in error_msg:
                            print("Recommendation: Run 'request system storage cleanup' or manually remove files from /var.")
                            status['error'] = "Insufficient disk space in /var"
                        else:
                            status['error'] = f"CLI upgrade failed: {cli_e}"
                        upgrade_status.append(status)
                        continue
                except RpcTimeoutError as e:
                    logger.error(f"Timeout during software upgrade on {hostname}: {e}")
                    print(f"Error: Timeout during software upgrade on {hostname}: {e}")
                    status['error'] = f"Timeout: {e}"
                    upgrade_status.append(status)
                    continue
                except Exception as e:
                    logger.error(f"Software upgrade failed on {hostname}: {e}")
                    print(f"Error: Software upgrade failed on {hostname}: {e}")
                    error_msg = str(e)
                    if "Could not format alternate root" in error_msg:
                        print("Recommendation: Check disk health with 'show system storage' and 'show system alarms'. Consider USB recovery or Juniper support.")
                        status['error'] = "Storage failure: Could not format alternate root"
                    elif "Not enough space in /var" in error_msg:
                        print("Recommendation: Run 'request system storage cleanup' or manually remove files from /var.")
                        status['error'] = "Insufficient disk space in /var"
                    else:
                        status['error'] = str(e)
                    upgrade_status.append(status)
                    continue

                # Perform reboot
                try:
                    logger.debug(f"Initiating reboot on {hostname}")
                    sw.reboot()
                    logger.info(f"Reboot initiated on {hostname}")
                    print(f"Reboot initiated on {hostname}")
                except Exception as e:
                    logger.error(f"Reboot failed on {hostname}: {e}")
                    print(f"Reboot failed on {hostname}: {e}")
                    status['error'] = f"Reboot failed: {e}"
                    upgrade_status.append(status)
                    continue

                # Wait for reboot and reconnect
                print(f"Device {hostname} is rebooting. Waiting for reconnection...")
                time.sleep(120)
                dev.close()
                max_attempts = 5
                for attempt in range(max_attempts):
                    try:
                        dev = Device(host=hostname, user=username, password=password)
                        dev.open(timeout=300)
                        logger.info(f"Reconnected to {hostname} after reboot")
                        print(f"Reconnected to {hostname} after reboot")
                        break
                    except ConnectError as e:
                        logger.warning(f"Reconnect attempt {attempt + 1}/{max_attempts} failed for {hostname}: {e}")
                        print(f"Reconnect attempt {attempt + 1}/{max_attempts} failed for {hostname}. Retrying...")
                        time.sleep(60)
                else:
                    logger.error(f"Failed to reconnect to {hostname} after {max_attempts} attempts")
                    print(f"Error: Failed to reconnect to {hostname} after reboot")
                    status['error'] = "Reconnect failure"
                    upgrade_status.append(status)
                    continue

                # Probe device after reboot
                if probe_device(dev, hostname, username, password):
                    logger.info(f"Post-upgrade probe successful for {hostname}")
                    print(f"Upgrade and reboot completed successfully for {hostname}")
                    status['success'] = True
                    upgrade_status.append(status)
                else:
                    logger.error(f"Post-upgrade probe failed for {hostname}")
                    print(f"Warning: Post-upgrade probe failed for {hostname}")
                    status['error'] = "Post-upgrade probe failure"
                    upgrade_status.append(status)

            except Exception as e:
                logger.error(f"Error upgrading {hostname}: {e}")
                print(f"Error upgrading {hostname}: {e}")
                status['error'] = str(e)
                upgrade_status.append(status)

        disconnect_from_hosts(connections)

        # Summarize upgrade status
        successful = [s for s in upgrade_status if s['success']]
        failed = [s for s in upgrade_status if not s['success']]
        logger.info(f"Upgrade summary: {len(successful)} successful, {len(failed)} failed")
        print("\nUpgrade Summary:")
        print(f"Successful: {len(successful)} device(s)")
        for s in successful:
            print(f"  - {s['hostname']}")
        print(f"Failed: {len(failed)} device(s)")
        for s in failed:
            print(f"  - {s['hostname']}: {s['error']}")

        if failed:
            logger.warning("Code upgrade process completed with failures")
            print("Code upgrade process completed with failures.")
        else:
            logger.info("Code upgrade process completed successfully")
            print("Code upgrade process completed successfully.")

    except KeyboardInterrupt:
        logger.info("Code upgrade interrupted by user (Ctrl+C)")
        print("\nProgram interrupted by user. Exiting.")
    except Exception as e:
        logger.error(f"Error in code_upgrade: {e}")
        print(f"Error: {e}")
