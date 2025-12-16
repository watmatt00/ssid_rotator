# Systemd Service Files

These service files enable automatic SSID rotation and web interface management.

## Installation

### On the Raspberry Pi:

```bash
# Copy service files to systemd directory
sudo cp ~/ssid_rotator/deployment/systemd/*.service /etc/systemd/system/
sudo cp ~/ssid_rotator/deployment/systemd/*.timer /etc/systemd/system/

# Reload systemd to recognize new files
sudo systemctl daemon-reload

# Enable and start the rotation timer (rotates every 18 hours)
sudo systemctl enable ssid-rotator.timer
sudo systemctl start ssid-rotator.timer

# Enable and start the web interface
sudo systemctl enable ssid-web-manager
sudo systemctl start ssid-web-manager
```

## Service Descriptions

### ssid-rotator.service
- **Type**: Oneshot (runs once per trigger)
- **Function**: Executes the SSID rotation script
- **Triggered by**: ssid-rotator.timer
- **Logs**: Appends to `/var/log/ssid-rotator.log`

### ssid-rotator.timer
- **Function**: Triggers SSID rotation on schedule
- **Schedule**: 
  - First run: 5 minutes after boot
  - Subsequent runs: Every 18 hours
  - Persistent: Runs missed rotations if system was off
- **Installed**: Managed by `timers.target`

### ssid-web-manager.service
- **Type**: Simple (long-running daemon)
- **Function**: Runs Flask web interface on port 5000
- **Auto-restart**: Yes (10 second delay after failure)
- **Access**: https://rotator.local:5000 or https://192.168.102.205:5000
- **SSL/TLS**: Automatically uses certificates from `~/certs/` if present

## Verification

```bash
# Check timer status
sudo systemctl status ssid-rotator.timer
sudo systemctl list-timers | grep ssid

# Check web service status
sudo systemctl status ssid-web-manager

# View logs
sudo journalctl -u ssid-rotator.service -n 50
sudo journalctl -u ssid-web-manager -n 50
tail -f /var/log/ssid-rotator.log
```

## Stopping Services

```bash
# Stop timer
sudo systemctl stop ssid-rotator.timer
sudo systemctl disable ssid-rotator.timer

# Stop web interface
sudo systemctl stop ssid-web-manager
sudo systemctl disable ssid-web-manager
```

## Manual Rotation Trigger

Even with the timer enabled, you can manually trigger a rotation:

```bash
sudo systemctl start ssid-rotator.service
```

Or run the script directly:

```bash
python3 ~/ssid_rotator/src/rotate_ssid.py
```
