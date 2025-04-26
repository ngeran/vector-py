---

```markdown
# Step-by-Step Guide to Using the Code Upgrade Script

This guide provides detailed instructions for using the `code_upgrade.py` script to upgrade or downgrade the Junos OS on Juniper devices, such as the SRX320 or SRX210H. The script is located in the `/home/nikos/github/ngeran/vector-py` repository and automates the process of selecting a vendor, product, release, and target devices, then performing the software installation, reboot, and version verification.

## Prerequisites

Before starting, ensure the following are in place:

1. **Environment Setup**:
   - The script is located in `/home/nikos/github/ngeran/vector-py/scripts/code_upgrade.py`.
   - The repository contains:
     - `data/upgrade_data.yml`: Defines vendors, products, and available releases.
     - `data/upgrade_hosts.yml`: Stores host IPs (optional).
     - `network-automation-launcher/launcher.py`: The entry point for running the script.
   - Verify the repository:
     ```bash
     cd /home/nikos/github/ngeran/vector-py
     ls -l scripts/code_upgrade.py data/upgrade_data.yml network-automation-launcher/launcher.py
     ```

2. **Dependencies**:
   - Install required Python packages:
     ```bash
     pip install junos-eznc pyyaml
     ```
   - Verify:
     ```bash
     pip show junos-eznc pyyaml
     ```
   - Ensure `python3` is installed:
     ```bash
     python3 --version
     ```

3. **Device Preparation**:
   - Ensure the target device (e.g., SRX320 at `172.27.200.200`) is reachable:
     ```bash
     ping -c 4 172.27.200.200
     ```
   - Verify SSH access:
     ```bash
     ssh admin@172.27.200.200 "show version"
     ```
     - Default credentials: `username: admin`, `password: ******`.
   - The upgrade image (e.g., `junos-srxsme-23.4R2-S3.9.tgz`) must be in `/var/tmp` on the device:
     ```bash
     ssh admin@172.27.200.200 "file list /var/tmp"
     ```
     If missing, upload it:
     ```bash
     scp /path/to/junos-srxsme-23.4R2-S3.9.tgz admin@172.27.200.200:/var/tmp/
     ```
   - Check available storage:
     ```bash
     ssh admin@172.27.200.200 "show system storage"
     ```
     Ensure `/cf/var` has at least 500 MB free.

4. **Network Access**:
   - The host running the script must have SSH access to the target device(s).
   - Ensure no firewall rules block SSH (port 22) or Netconf (port 830).

5. **Git Repository**:
   - Ensure the repository is up to date:
     ```bash
     cd /home/nikos/github/ngeran/vector-py
     git pull origin main
     ```

## Step-by-Step Instructions

### Step 1: Navigate to the Repository
Change to the project directory:
```bash
cd /home/nikos/github/ngeran/vector-py
```

### Step 2: Clear Python Cache
Remove any cached Python files to avoid conflicts:
```bash
find /home/nikos/github/ngeran/vector-py -name '*.pyc' -delete
rm -rf /home/nikos/github/ngeran/vector-py/scripts/__pycache__
rm -rf /home/nikos/github/ngeran/vector-py/network-automation-launcher/__pycache__
```

### Step 3: Verify Script Syntax
Ensure the script has no syntax errors:
```bash
python -m py_compile /home/nikos/github/ngeran/vector-py/scripts/code_upgrade.py
```
If errors occur, view details:
```bash
python -m py_compile /home/nikos/github/ngeran/vector-py/scripts/code_upgrade.py 2>&1
```
Fix any issues in `scripts/code_upgrade.py` using a text editor (e.g., `nvim`).

### Step 4: Verify `upgrade_data.yml`
Check that the `upgrade_data.yml` file contains the correct product and release information:
```bash
cat /home/nikos/github/ngeran/vector-py/data/upgrade_data.yml
```
Example entry for SRX320:
```yaml
- vendor-name: JUNIPER
  firewalls:
    - product: SRX320
      releases:
        - release: 23.4R2-S3.9
          os: junos-srxsme-23.4R2-S3.9.tgz
        - release: 24.2R1-S2.5
          os: junos-srxsme-24.2R1-S2.5.tgz
```
If the desired release or image is missing, edit the file:
```bash
nvim /home/nikos/github/ngeran/vector-py/data/upgrade_data.yml
```
Save changes:
```vim
:wq
```

### Step 5: Run the Script
Launch the script using the launcher:
```bash
python network-automation-launcher/launcher.py
```

### Step 6: Select Options
Follow the prompts to configure the upgrade:

1. **Select Action**:
   ```
   Select an action:
   ----------------------------------------
   | Option | Action                  |
   ----------------------------------------
   | 1      | Ping Hosts             |
   | 2      | Configure Interfaces   |
   | 3      | Monitor Routing Tables |
   | 4      | Code Upgrade           |
   ----------------------------------------
   Enter your choice (1-4):
   ```
   - Enter: `4` (Code Upgrade).

2. **Choose Execution Mode**:
   ```
   Choose execution mode:
   1. Execute locally
   2. Push to GitHub
   Enter your choice (1-2):
   ```
   - Enter: `1` (Execute locally).

3. **Select Vendor**:
   ```
   Select a vendor:
   ----------------------------------------
   | Option | Vendor                  |
   ----------------------------------------
   | 1      | JUNIPER                |
   ----------------------------------------
   Select a vendor (1-1):
   ```
   - Enter: `1` (JUNIPER).

4. **Select Product**:
   ```
   Select a product:
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
   Select a product (1-6):
   ```
   - Enter: `3` (SRX320) or `4` (SRX210H), depending on the target device.

5. **Select Release**:
   ```
   Available releases:
   ----------------------------------------
   | Option | Release                 |
   ----------------------------------------
   | 1      | 23.4R2-S3              |
   | 2      | 23.4R2-S4              |
   | 3      | 24.2R1-S2              |
   ----------------------------------------
   Select a release (1-3):
   ```
   - Enter: `1` (23.4R2-S3) or another release as needed.
   - Note: The script matches sub-releases (e.g., `23.4R2-S3.9` matches `23.4R2-S3`).

6. **Specify Hosts**:
   ```
   Read hosts from upgrade_hosts.yml? (y/n):
   ```
   - Enter: `n` (to manually enter IPs) or `y` (to load from `upgrade_hosts.yml`).
   - If `n`, enter IPs:
     ```
     Enter a host IP (or press Enter to finish): 172.27.200.200
     Enter a host IP (or press Enter to finish):
     ```
     - Press Enter when done.
   - The script saves IPs to `upgrade_hosts.yml`.

7. **Enter Credentials**:
   ```
   Username: admin
   Password: ******
   ```

### Step 7: Monitor the Upgrade Process
The script will:
1. Connect to the device(s):
   ```
   Connecting to devices...
   ✅ Successfully logged in to 172.27.200.200
   ```
2. Check for the image:
   ```
   ✅ Image /var/tmp/junos-srxsme-23.4R2-S3.9.tgz found on 172.27.200.200
   ```
3. Verify the current version and warn about downgrades:
   ```
   Checking current version on 172.27.200.200...
   ✅ Current Junos version on 172.27.200.200: 24.2R1-S2.5
   ⚠️ Warning: Selected version 23.4R2-S3 is older than current 24.2R1-S2.5 on 172.27.200.200.
   Proceed with downgrade? (y/n): y
   ```
   - Enter: `y` to proceed with a downgrade, or `n` to skip.
4. Install

 the software:
   ```
   Installing software with validation (no reboot) on 172.27.200.200...
   ✅ Installation validated successfully. Rebooting...
   ✅ Reboot initiated on 172.27.200.200
   ```
5. Wait for the device to reboot and become reachable:
   ```
   Device 172.27.200.200 is rebooting. Waiting for availability...
   Probing 172.27.200.200 for availability post-reboot...
   ✅ 172.27.200.200 is reachable and PyEZ connection is up
   ```
6. Verify the version:
   ```
   Attempting to verify version on 172.27.200.200 against target '23.4R2-S3'...
   ✅ Version on 172.27.200.200: 23.4R2-S3.9 (via facts)
   ✅ Version 23.4R2-S3.9 matches target 23.4R2-S3.
   ✅ Upgrade successful on 172.27.200.200. Version: 23.4R2-S3.9
   ```
7. Display the summary:
   ```
   Upgrade Summary:
   Successful: 1 device(s)
     - 172.27.200.200
   Failed: 0 device(s)
   Code upgrade process completed successfully.
   ```

### Step 8: Post-Upgrade Verification
Verify the device’s stability:
```bash
ssh admin@172.27.200.200
show system alarms
show system storage
show version
show system processes extensive | match "PID|%CPU|%MEM"
start shell user root
ls -lh /var/run/pkg.active
exit
file show /var/log/software_install_status.log
```

### Step 9: Clean Up Device Storage
Free up space by removing old images:
```bash
ssh admin@172.27.200.200
request system storage cleanup
start shell user root
ls -lh /cf/var/tmp
rm -f /cf/var/tmp/junos-srxsme-<old-version>.tgz  # e.g., junos-srxsme-24.2R1-S2.5.tgz
df -k /cf/var
exit
```
Verify `/cf/var` has at least 500 MB free:
```bash
ssh admin@172.27.200.200 "show system storage"
```

### Step 10: Commit Changes to GitHub
If you modified `upgrade_data.yml` or the script, commit the changes:
```bash
cd /home/nikos/github/ngeran/vector-py
git add scripts/code_upgrade.py data/upgrade_data.yml
git commit -m "Completed code upgrade for SRX320 to 23.4R2-S3.9"
git push origin main
```

## Troubleshooting

If the script fails, check the following:

1. **Script Errors**:
   ```bash
   python -m py_compile /home/nikos/github/ngeran/vector-py/scripts/code_upgrade.py 2>&1
   cat /home/nikos/github/ngeran/vector-py/network_automation.log
   ```

2. **Connection Issues**:
   ```bash
   ping -c 4 172.27.200.200
   ssh admin@172.27.200.200 "show version"
   ssh admin@172.27.200.200 "show configuration system services"
   ```

3. **Image Missing**:
   ```bash
   ssh admin@172.27.200.200 "file list /var/tmp"
   scp /path/to/junos-srxsme-23.4R2-S3.9.tgz admin@172.27.200.200:/var/tmp/
   ```

4. **Version Mismatch**:
   ```bash
   cat /home/nikos/github/ngeran/vector-py/data/upgrade_data.yml
   ```

5. **Storage Issues**:
   ```bash
   ssh admin@172.27.200.200
   request system storage cleanup
   start shell user root
   du -sk /cf/var/* | sort -nr
   rm -rf /cf/var/log/*.gz
   find /cf/var/log -type f -name "*.log" -exec rm -f {} \;
   find /cf/var -type f -name "*.core" -exec rm -f {} \;
   rm -rf /cf/var/db
   df -k /cf/var
   exit
   ```

6. **Collect Debug Information**:
   Share:
   ```bash
   ssh admin@172.27.200.200 "show system alarms; show system storage; show version; show system processes extensive | match \"PID|%CPU|%MEM\"; start shell user root; ls -lh /var/run/pkg.active; exit; file show /var/log/software_install_status.log"
   cat /home/nikos/github/ngeran/vector-py/network_automation.log
   cat /home/nikos/github/ngeran/vector-py/data/upgrade_data.yml
   ```

## Notes
- **Credentials**: The script uses `admin`/`******` by default. Update as needed for your environment.
- **Downgrades**: The script warns about downgrades (e.g., from `24.2R1-S2.5` to `23.4R2-S3.9`). Always confirm (`y`) to proceed.
- **Sub-Releases**: The script matches sub-releases (e.g., `23.4R2-S3.9` to `23.4R2-S3`). Update `upgrade_data.yml` for exact versions to avoid confusion.
- **SRX210H**: If upgrading the SRX210H, ensure `/cf/var` has sufficient space (see Troubleshooting).
- **Logs**: Check `/home/nikos/github/ngeran/vector-py/network_automation.log` for detailed debug information.
```

Let me know if you'd like this as a downloadable `.md` file or want to preview how it looks rendered in GitHub style.
