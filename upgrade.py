from jnpr.junos import Device
from jnpr.junos.exception import ConnectError, RpcError  # Fixed imports
from jnpr.junos.utils.sw import SW

# Device credentials and image path
device_ip = "172.27.200.200"
username = "admin"
password = "manolis1"
image_path = "/var/tmp/junos-srxsme-23.4R2-S3.9.tgz"

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
    else:
        print("❌ Installation did not complete successfully. No reboot issued.")

    dev.close()

except ConnectError as e:
    print(f"❌ Connection error: {e}")
except RpcError as e:
    print(f"❌ RPC error during install: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
