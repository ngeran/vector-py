Vector-Py: Juniper Network Automation Toolkit
vector-py is a Python-based automation toolkit for managing Juniper Networks devices (SRX, EX, MX, ACX). It provides a menu-driven interface to perform tasks such as pinging hosts, configuring interfaces, monitoring routing tables, and upgrading device software. The toolkit uses junos-eznc (PyEZ) for device interactions and supports both local execution and GitHub integration.
This README focuses on the Code Upgrade feature, which automates software upgrades for Juniper devices, ensuring reliable installation, validation, and version verification with robust fallback mechanisms.
Features

Menu-Driven Interface: Select vendors, products, and software releases interactively.
Automated Upgrades: Installs and validates Juniper Junos software with automatic reboot and version verification.
Robust Version Verification:
Uses dev.facts['version'] from PyEZ for reliable version retrieval.
Falls back to ssh <username>@<device-ip> "show version" if PyEZ fails.


Device Probing: Waits for devices to become available post-reboot using ping-based probing (60-second intervals).
Robust Error Handling: Handles connection issues, RPC errors, and transient SSH failures with retries.
Logging: Detailed logs for debugging, stored in network_automation.log.
GitHub Integration: Option to push changes to a GitHub repository.

Prerequisites

System:
Linux (e.g., Ubuntu/Debian) with Python 3.7+.
ping utility (sudo apt-get install iputils-ping).
SSH client installed (openssh-client).


Python Packages:pip install jnpr.junos pyyaml


Juniper Devices:
SSH enabled with credentials (username/password).
Sufficient storage on /cf/var or /var/tmp (e.g., >500 MB for SRX320, >100 MB for SRX210H).
Upgrade images (e.g., junos-srxsme-23.4R2-S3.9.tgz) pre-uploaded to /var/tmp.


Repository Setup:
Clone the repository:git clone https://github.com/ngeran/vector-py.git
cd vector-py


Ensure data/upgrade_data.yml and data/upgrade_hosts.yml are configured (see Configuration).



Installation

Clone the Repository:git clone https://github.com/ngeran/vector-py.git
cd vector-py


Install Dependencies:pip install jnpr.junos pyyaml
sudo apt-get install iputils-ping openssh-client


Set Environment Variable:export VECTOR_PY_DIR=$PWD

Add to ~/.bashrc for persistence:echo "export VECTOR_PY_DIR=$PWD" >> ~/.bashrc
source ~/.bashrc


Verify Setup:python -m py_compile network-automation-launcher/launcher.py
python -m py_compile scripts/code_upgrade.py



Configuration

upgrade_data.yml:
Located in data/upgrade_data.yml.
Defines vendors, products, and releases. Example:products:
  - vendor-name: JUNIPER
    switches:
      - product: EX4600
        releases:
          - release: 23.4R2-S3
            os: junos-ex-23.4R2-S3.9.tgz
      - product: EX4400
        releases:
          - release: 23.4R2-S3
            os: junos-ex-23.4R2-S3.9.tgz
    firewalls:
      - product: SRX320
        releases:
          - release: 23.4R2-S3
            os: junos-srxsme-23.4R2-S3.9.tgz
          - release: 23.4R2-S4
            os: junos-srxsme-23.4R2-S4.2.tgz
          - release: 24.2R1-S2
            os: junos-srxsme-24.2R1-S2.5.tgz
      - product: SRX210H
        releases:
          - release: 12.1X46-D86
            os: junos-srxsme-12.1X46-D86-domestic.tgz
    routers:
      - product: MX-SERIES
        releases:
          - release: 23.4R2-S3
            os: junos-mx-23.4R2-S3.9.tgz
      - product: ACX
        releases:
          - release: 23.4R2-S3
            os: junos-acx-23.4R2-S3.9.tgz


Add new products or releases as needed.


upgrade_hosts.yml:
Located in data/upgrade_hosts.yml.
Stores target device IPs. Example:hosts:
  - 172.27.200.200
  - 172.27.200.201


Updated automatically when entering IPs manually.



Usage
Preparing Devices

Verify Device Storage:ssh admin@<device-ip>
show system storage
df -k /cf/var /var/tmp


Ensure sufficient space (e.g., >500 MB for SRX320, >100 MB for SRX210H).
Clean up if needed:request system storage cleanup
start shell user root
rm -rf /cf/var/log/*.gz
rm -rf /cf/var/tmp/*.tgz  # Keep target image
find /cf/var/log -type f -name "*.log" -exec rm -f {} \;
df -k /cf/var




Upload Upgrade Image:
Transfer the image to /var/tmp:scp junos-srxsme-23.4R2-S3.9.tgz admin@<device-ip>:/var/tmp/


Verify:ssh admin@<device-ip> "file list /var/tmp"
file checksum md5 /var/tmp/junos-srxsme-23.4R2-S3.9.tgz




Check Device Health:ssh admin@<device-ip>
show system alarms
show system processes extensive | match "PID|%CPU|%MEM"
start shell user root
ls -lh /var/run/pkg.active
rm -f /var/run/pkg.active  # If exists
exit



Running the Script

Navigate to Repository:cd /home/nikos/github/ngeran/vector-py


Clear Python Cache:find . -name '*.pyc' -delete
rm -rf scripts/__pycache__ network-automation-launcher/__pycache__


Run the Launcher:python network-automation-launcher/launcher.py


Perform Code Upgrade:
Select Code Upgrade:Select an action:
----------------------------------------
| Option | Action                  |
----------------------------------------
| 1      | Ping Hosts             |
| 2      | Configure Interfaces   |
| 3      | Monitor Routing Tables |
| 4      | Code Upgrade           |
----------------------------------------
Enter your choice (1-4): 4


Choose execution mode:Choose execution mode:
1. Execute locally
2. Push to GitHub
Enter your choice (1-2): 1


Select vendor (e.g., JUNIPER):Select a vendor:
----------------------------------------
| Option | Vendor                  |
----------------------------------------
| 1      | JUNIPER                |
----------------------------------------
Select a vendor (1-1): 1


Select product (e.g., SRX320):Select a product:
----------------------------------------
| Option | Product                 |
----------------------------------------
| 1      | EX4600                 |
| 2      | EX4400                 |
| 3      | SRX320                 |
| 4      | SRX210H                |
| 5      | MX-SERIES              |
| 6      | ACX                    |
----------------------------------------
Select a product (1-6): 3


Select release (e.g., 23.4R2-S3):Available releases:
----------------------------------------
| Option | Release                 |
----------------------------------------
| 1      | 23.4R2-S3              |
| 2      | 23.4R2-S4              |
| 3      | 24.2R1-S2              |
----------------------------------------
Select a release (1-3): 1


Enter host IPs:Read hosts from upgrade_hosts.yml? (y/n): n
Enter a host IP (or press Enter to finish): 172.27.200.200
Enter a host IP (or press Enter to finish):


Enter credentials:Username: admin
Password: <password>


The script will:
Connect to the device.
Verify the image exists in /var/tmp.
Check the current version using dev.facts['version'] (or CLI fallback) and warn about downgrades.
Install and validate the software.
Reboot the device.
Probe for availability (up to 15 minutes, checking every 60 seconds).
Verify the version using dev.facts['version'] (with CLI and SSH fallbacks, up to 5 attempts, retrying every 60 seconds).
Display a summary:Upgrade Summary:
Successful: 1 device(s)
  - 172.27.200.200
Failed: 0 device(s)
Code upgrade process completed successfully.







Post-Upgrade Cleanup

Remove Old Images:ssh admin@<device-ip>
start shell user root
rm -f /cf/var/tmp/<old-image>.tgz
df -k /cf/var
exit
request system storage cleanup


Verify Device:ssh admin@<device-ip>
show version
show system alarms
df -k /cf/var



Troubleshooting

Error: 'NoneType' object has no attribute 'timeout':
The script now falls back to ssh if PyEZ fails. Verify SSH access:ssh admin@<device-ip> "show version"


Check /var/log/sshd on the device for SSH issues.
Increase max_attempts or retry_interval in verify_version.


Error: Device not reachable after reboot:
Verify network connectivity:ping <device-ip>


Check device logs:ssh admin@<device-ip> "show log messages | last"




Error: SSH command failed:
Ensure SSH keys are set up or password authentication is enabled.
Test manually:ssh admin@<device-ip> "show version"




Storage Issues:
If /cf/var is full:ssh admin@<device-ip>
start shell user root
find /cf/var -type f -name "*.core" -exec rm -f {} \;
rm -rf /cf/var/db
df -k /cf/var




Logs:
Check detailed logs:cat /home/nikos/github/ngeran/vector-py/network_automation.log





Manual Fallback
If the script fails:
ssh admin@<device-ip>
request system software add /var/tmp/<image>.tgz no-validate reboot

For SRX210H with storage issues:
ssh admin@<device-ip>
start shell user root
mv /cf/var/tmp/<image>.tgz /mfs/
exit
request system software add /mfs/<image>.tgz no-validate reboot

Contributing

Submit issues or pull requests to https://github.com/ngeran/vector-py.
Ensure code follows PEP 8 and includes logging.

License
MIT License. See LICENSE for details.
