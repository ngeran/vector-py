from jnpr.junos.utils.config import Config
from jnpr.junos.exception import ConfigLoadError, CommitError
from jnpr.junos import Device
import logging

logger = logging.getLogger(__name__)

def configure_device(dev: Device, config_text: str, host_name: str, host_ip: str) -> bool:
    """
    Load and commit configuration text on a Junos device.

    Args:
        dev: Junos Device object.
        config_text: Configuration string to load (text format).
        host_name: Device hostname for logging.
        host_ip: Device IP for logging.

    Returns:
        bool: True if configuration succeeds, False otherwise.
    """
    try:
        with Config(dev, mode='exclusive') as cu:
            cu.load(config_text, format='text')
            cu.commit()
        print(f"Interfaces configured for {host_name} ({host_ip})")
        return True
    except (ConfigLoadError, CommitError) as error:
        print(f"Failed to configure interfaces for {host_name} ({host_ip}): {error}")
        return False
    except Exception as error:
        print(f"Unexpected error for {host_name} ({host_ip}): {error}")
        return False
