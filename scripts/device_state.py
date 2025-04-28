import logging
import os
import subprocess
import time

from jnpr.junos.exception import ConnectError, ConnectTimeoutError, RpcError, ProbeError, ConnectRefusedError
from utils.connection import connect_to_hosts, disconnect_from_hosts  # Adjust if in a different module

logger = logging.getLogger(__name__)


def check_image_exists(dev, image_path: str, hostname: str) -> bool:
    """Check if the upgrade image exists on the device."""
    try:
        image_name = os.path.basename(image_path)
        result = dev.cli("file list /var/tmp/", warning=False)
        if image_name in result.split():
            logger.info(f"Image {image_path} found on {hostname}")
            print(f"✅ Image {image_path} found on {hostname}")
            return True
        logger.error(f"Image {image_path} not found on {hostname}")
        print(f"❌ Image {image_path} not found on {hostname}")
        return False
    except Exception as e:
        logger.error(f"Error checking image on {hostname}: {e}")
        print(f"❌ Error checking image on {hostname}: {e}")
        return False


def check_current_version(dev, hostname: str, target_version: str) -> bool:
    """Check current Junos version and warn about downgrade."""
    logger.info(f"Checking current version on {hostname}")
    print(f"Checking current version on {hostname}...")
    try:
        current_version = dev.facts.get("version")
        if not current_version:
            logger.warning(f"No version found in facts on {hostname}. Falling back to CLI.")
            version_output = dev.cli("show version", warning=False)
            for line in version_output.splitlines():
                if "JUNOS Software Release" in line:
                    current_version = line.split("[")[-1].strip("]").strip()
                    break
        if current_version:
            logger.info(f"Current Junos version on {hostname}: {current_version}")
            print(f"✅ Current Junos version on {hostname}: {current_version}")
            if current_version == target_version:
                logger.info(f"{hostname} already on target version {target_version}. Skipping upgrade.")
                print(f"✅ {hostname} already on target version {target_version}. Skipping upgrade.")
                return False
            current_parts = [int(x) if x.isdigit() else x for x in current_version.replace("-", ".").split(".")]
            target_parts = [int(x) if x.isdigit() else x for x in target_version.replace("-", ".").split(".")]
            if current_parts > target_parts:
                logger.warning(f"Selected version {target_version} is older than current {current_version} on {hostname}")
                print(f"⚠️ Warning: Selected version {target_version} is older than current {current_version} on {hostname}.")
                choice = input("Proceed with downgrade? (y/n): ").strip().lower()
                if choice != "y":
                    logger.info(f"User chose to skip downgrade on {hostname}")
                    print(f"Skipping upgrade for {hostname} to avoid downgrade.")
                    return False
        return True
    except Exception as e:
        logger.warning(f"Failed to check Junos version on {hostname}: {e}. Proceeding with upgrade.")
        print(f"⚠️ Warning: Failed to check Junos version on {hostname}: {e}. Proceeding with upgrade.")
        return True


def probe_device(hostname: str, username: str, password: str, max_wait: int = 900, interval: int = 60) -> bool:
    """Probe device availability using ping and PyEZ connection until it responds or times out."""
    logger.info(f"Probing {hostname} for availability post-reboot")
    print(f"Probing {hostname} for availability post-reboot...")
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            # Check ping
            ping_result = subprocess.run(
                ["ping", "-c", "1", "-W", "2", hostname],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if ping_result.returncode != 0:
                logger.debug(f"Ping to {hostname} failed: {ping_result.stderr}")
                print(f"⚠️ {hostname} not yet reachable via ping. Retrying in {interval} seconds...")
                time.sleep(interval)
                continue

            # Check PyEZ connection
            connections = connect_to_hosts([hostname], username, password)
            if connections:
                logger.info(f"{hostname} is reachable and PyEZ connection is up")
                print(f"✅ {hostname} is reachable and PyEZ connection is up")
                disconnect_from_hosts(connections)
                return True
            logger.debug(f"PyEZ connection to {hostname} failed")
            print(f"⚠️ {hostname} pingable but PyEZ not ready. Retrying in {interval} seconds...")
        except Exception as e:
            logger.debug(f"Probe to {hostname} failed: {e}")
            print(f"⚠️ {hostname} not yet fully reachable. Retrying in {interval} seconds...")
        time.sleep(interval)
    logger.error(f"{hostname} did not become reachable within {max_wait} seconds")
    print(f"❌ {hostname} did not become reachable within {max_wait} seconds")
    return False


def verify_version(
    hostname: str,
    username: str,
    password: str,
    target_version: str,
    max_attempts: int = 30,
    retry_interval: int = 30,
) -> tuple:
    """
    Verifies device software version matches the target version.
    """
    logger.info(f"Attempting to verify version on {hostname} against target '{target_version}'")
    print(f"Attempting to verify version on {hostname} against target '{target_version}'...")
    last_exception = None

    for attempt in range(max_attempts):
        connections = []
        try:
            print(f"Attempt {attempt + 1}/{max_attempts}: Connecting to {hostname}...")
            logger.info(f"Attempt {attempt + 1}/{max_attempts}: Connecting to {hostname}...")

            connections = connect_to_hosts([hostname], username, password)
            if not connections:
                raise ConnectError(f"{hostname}: Failed to establish connection")

            dev = connections[0]
            if not dev.connected:
                raise ConnectError(f"{hostname}: Connection failed (connected flag is False)")

            facts = dev.facts
            current_version = facts.get("version")

            if current_version:
                print(f"✅ Version on {hostname}: {current_version}")
                base_current = current_version.split(".")[0] if "." in current_version else current_version
                base_target = target_version.split(".")[0] if "." in target_version else target_version
                match = base_current == base_target
                disconnect_from_hosts(connections)
                if match:
                    logger.info(f"Version {current_version} matches target {target_version}")
                    return True, current_version, None
                else:
                    logger.warning(f"Version mismatch: Found {current_version}, Target {target_version}")
                    return False, current_version, f"Version mismatch: Found {current_version}, Target {target_version}"
            else:
                raise ValueError("Version key not found in device facts.")
        except (ConnectRefusedError, ConnectError, ConnectTimeoutError, ProbeError, RpcError) as e:
            last_exception = e
            logger.warning(f"Attempt {attempt + 1} failed: {type(e).__name__} - {e}")
            print(f"⚠️ {type(e).__name__} during verification. Retrying...")
        except Exception as e:
            last_exception = e
            logger.error(f"Unexpected error during verification on {hostname}: {e}", exc_info=True)
            print(f"⚠️ Unexpected error: {e}")
        finally:
            disconnect_from_hosts(connections)

        if attempt < max_attempts - 1:
            time.sleep(retry_interval)
        else:
            logger.error(f"All {max_attempts} verification attempts failed on {hostname}")

    error_message = f"Failed to verify version on {hostname} after {max_attempts} attempts. Last error: {last_exception}"
    return False, None, error_message
