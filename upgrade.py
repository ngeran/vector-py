import time

from jnpr.junos import Device
from jnpr.junos.exception import ConnectError, RpcError
from jnpr.junos.utils.sw import SW

# Device credentials and image path
device_ip = "172.27.200.200"
username = "admin"
password = "manolis1"
image_path = "/var/tmp/junos-srxsme-24.2R1-S2.5.tgz"


def get_junos_version(dev):
    # Get the device facts, including the version
    facts = dev.facts
    return facts.get("version", "Unknown version")


try:
    print("Connecting to device...")
    dev = Device(host=device_ip, user=username, passwd=password)
    dev.open()

    print(f"✅ Successfully logged in to {device_ip}")

    sw = SW(dev)

    print("Installing software with validation (no reboot)...")
    success = sw.install(package=image_path, validate=True, no_copy=True, progress=True)

    if success:
        print("✅ Installation validated successfully. Rebooting...")
        sw.reboot()

        # Wait for device to come back online (you can adjust the sleep time)
        print("Waiting for the device to come back online...")
        time.sleep(60)  # Wait for 60 seconds; adjust as necessary

        # Reconnect to the device
        print("Reconnecting to the device...")
        dev.open()

        # Get and print the new version after the reboot
        new_version = get_junos_version(dev)
        print(f"✅ Device is back online. Current JUNOS version: {new_version}")

    else:
        print("❌ Installation did not complete successfully. No reboot issued.")

    dev.close()

except ConnectError as e:
    print(f"❌ Connection error: {e}")
except RpcError as e:
    print(f"❌ RPC error during install: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
