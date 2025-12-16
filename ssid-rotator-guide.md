# SSID Rotation System with Web Management

## Overview

This system automatically rotates a WiFi SSID through a list of names every 18 hours. Perfect for displaying funny WiFi names that change regularly while keeping your production networks protected.

### Features

- 🔄 Automatic SSID rotation every 18 hours
- 🌐 Web interface to manage SSID list
- 🔒 Protected SSID list (never modified)
- 📊 Visual status display showing current/next SSID
- ✅ Safety checks to prevent modifying production SSIDs
- 📝 JSON-based configuration (easy to backup/restore)

### System Specifications

**Hardware:** UniFi Dream Router (UDR) Pro 7
**Network:** 192.168.102.1
**Target SSID:** "Fuck the orange turd" (ID: `69363fd4005cd02fa28ab902`)
**Protected Networks:** 7Oaks, 7Oaks-IOT, newnative, 7Oaks-Work
**API Endpoint:** `https://192.168.102.1/proxy/network/api/s/default/rest/wlanconf`

**Note:** UDR7 routers require `/proxy/network` prefix for all network controller API calls.

### Architecture

```
┌─────────────────────┐
│  Web Interface      │  ← Manage SSID lists via browser
│  (Flask App)        │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│  ssid_list.json     │  ← Stores rotation & protected SSIDs
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│  Rotation Script    │  ← Runs every 18 hours via cron
│  (Python)           │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│  UniFi UDR7 API     │  ← Updates the actual SSID
└─────────────────────┘
```

---

## Important: UDR7 API Path Requirements

**CRITICAL:** The UniFi Dream Router (UDR) Pro 7 uses a different API path structure than standalone UniFi controllers.

All network controller API calls require the `/proxy/network` prefix:
- ✅ Correct: `https://192.168.102.1/proxy/network/api/auth/login`
- ❌ Wrong: `https://192.168.102.1/api/auth/login`

The code in this guide has been updated to use the correct `/proxy/network` prefix for UDR7 compatibility.

---

## Prerequisites

- UniFi Dream Router (UDR) Pro 7
- Python 3
- Admin access to your UDR
- Linux machine to run the scripts (Ubuntu PC, Raspberry Pi, etc.)

---

## Host Configuration

**Raspberry Pi Zero W Details:**
- **Hostname:** `rotator`
- **DNS Name:** `rotator.local`
- **IP Address:** `192.168.102.205` (static)
- **Username:** `pi`
- **Password:** `rotator`
- **OS:** Raspberry Pi OS Lite
- **SSH Access:** `ssh pi@rotator.local` or `ssh pi@192.168.102.205`
- **Web Interface:** `http://rotator.local:5000` or `http://192.168.102.205:5000`

---

## Deployment Strategy

This project follows a **Git-based deployment workflow** to maintain a read-only production environment:

### Development vs Production

| Environment | Purpose | Editing | Updates |
|------------|---------|---------|---------|
| **PC/Laptop** | Development | ✅ Edit all scripts locally | `git push` to GitHub |
| **Raspberry Pi** | Production | ❌ Never edit files on Pi | `bash ~/ssid_rotator/ops_tools/update_app.sh` |

### Key Principles

1. **All code editing happens on PC** - Push changes to GitHub
2. **Pi is read-only (code)** - Only pulls updates via git
3. **Configuration via Web UI** - Manage SSID lists through browser
4. **State files are writable** - `/var/lib/ssid_rotator/` for runtime data
5. **One-command updates** - `update_app.sh` pulls code and restarts services

### File Locations

```
~/ssid_rotator/              # Code repository (read-only in production)
├── src/                     # Python scripts
├── ops_tools/               # Operational scripts
│   └── update_app.sh       # Update script
└── deployment/              # Systemd service files

/var/lib/ssid_rotator/      # Runtime state (writable)
├── ssid_list.json          # SSID configuration (editable via web UI)
├── state.json              # Rotation state
└── *.backup                # Auto-generated backups

/var/log/                   # Logs (writable)
└── ssid-rotator.log        # Rotation activity log
```

### Update Workflow

**On PC (after making code changes):**
```bash
git add .
git commit -m "Description of changes"
git push origin main
```

**On Pi (to receive updates):**
```bash
ssh pi@rotator.local
bash ~/ssid_rotator/ops_tools/update_app.sh
```

The update script automatically:
- Pulls latest code from GitHub
- Cleans Python cache
- Restarts web interface service
- Logs all actions

---

## Installation Steps

### Initial Deployment (One-Time Setup)

This section covers first-time installation on your Raspberry Pi. After initial setup, all updates happen via `ops_tools/update_app.sh`.

### Step 1: Clone Repository

```bash
# SSH into your Pi
ssh pi@rotator.local

# Clone the repository to home directory
cd ~
git clone https://github.com/watmatt00/ssid_rotator.git
cd ssid_rotator
```

### Step 2: Install Dependencies

```bash
# Install required Python packages
pip3 install flask requests --break-system-packages

# Alternatively, if requirements.txt exists:
# pip3 install -r requirements.txt --break-system-packages
```

### Step 3: Create Runtime Directories

```bash
# Create state/config directory
sudo mkdir -p /var/lib/ssid_rotator
sudo chown pi:pi /var/lib/ssid_rotator

# Create log file
sudo touch /var/log/ssid-rotator.log
sudo chown pi:pi /var/log/ssid-rotator.log
```

### Step 4: Create Initial Configuration File

Create `/var/lib/ssid_rotator/ssid_list.json`:

```bash
# Copy example configuration (once files are in repo)
# For now, create manually:
nano /var/lib/ssid_rotator/ssid_list.json
```

Paste this content:

```json
{
  "active_rotation": [
    "FBI Surveillance Van #4",
    "Pretty Fly for a WiFi",
    "The LAN Before Time",
    "Tell My WiFi Love Her",
    "Drop It Like Its Hotspot"
  ],
  "reserve_pool": [
    "LAN Solo",
    "The Ping in the North",
    "Silence of the LANs",
    "Get Off My LAN",
    "Router? I Hardly Know Her"
  ],
  "protected_ssids": [
    "7Oaks",
    "7Oaks-IOT",
    "newnative",
    "7Oaks-Work"
  ],
  "last_updated": "2024-12-16T00:00:00",
  "updated_by": "initial_setup"
}
```

**Configuration Notes:**
- **Active Rotation**: 5-7 SSIDs currently rotating (faster cycles)
- **Reserve Pool**: SSIDs waiting to be promoted to active rotation
- **Protected SSIDs**: Production networks that will NEVER be modified
  - `7Oaks` - Main 5GHz network
  - `7Oaks-IOT` - IoT 2.4GHz network  
  - `newnative` - Secondary 5GHz network
  - `7Oaks-Work` - Work network (both bands)
- Target SSID: **"Fuck the orange turd"** (ID: `69363fd4005cd02fa28ab902`)
- Cycle time: 5 SSIDs × 18 hours = **3.75 days per full cycle**

**⚠️ Important:** After initial setup, manage SSID lists via the web interface at `http://rotator.local:5000`. Never edit `ssid_list.json` directly after deployment.

### Step 5: Deploy Scripts from Repository

**Note:** In the current phase, scripts need to be created manually. Once the repository structure is complete, this step will simply reference existing files.

For now, create the rotation script at `~/ssid_rotator/src/rotate_ssid.py`:

```python
#!/usr/bin/env python3
import requests
import urllib3
import json
import os
from datetime import datetime

# Disable SSL warnings for self-signed cert
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
CONFIG = {
    "unifi_host": "192.168.102.1",  # Your UDR IP
    "username": "admin",
    "password": "your-password",  # Your actual admin password
    "current_ssid_name": "Fuck the orange turd",  # Initial SSID name to find
    "target_wlan_id": "69363fd4005cd02fa28ab902",  # The WLAN ID to rotate (optional, will auto-discover if not set)
    "state_file": "/var/lib/ssid_rotator/state.json",
    "ssid_list_file": "/var/lib/ssid_rotator/ssid_list.json"
}

class UniFiAPI:
    def __init__(self, host, username, password):
        self.host = host
        # UDR7 requires /proxy/network prefix for network controller API
        self.base_url = f"https://{host}/proxy/network"
        self.session = requests.Session()
        self.login(username, password)
    
    def login(self, username, password):
        url = f"{self.base_url}/api/auth/login"
        data = {"username": username, "password": password}
        response = self.session.post(url, json=data, verify=False)
        response.raise_for_status()
        print(f"[{datetime.now()}] Logged in successfully")
    
    def get_wlan_configs(self):
        url = f"{self.base_url}/api/s/default/rest/wlanconf"
        response = self.session.get(url, verify=False)
        return response.json()['data']
    
    def get_wlan_by_id(self, wlan_id):
        url = f"{self.base_url}/api/s/default/rest/wlanconf/{wlan_id}"
        response = self.session.get(url, verify=False)
        return response.json()['data'][0]
    
    def get_wlan_by_name(self, ssid_name):
        wlans = self.get_wlan_configs()
        for wlan in wlans:
            if wlan.get('name') == ssid_name:
                return wlan
        return None
    
    def update_ssid(self, wlan_id, new_ssid):
        url = f"{self.base_url}/api/s/default/rest/wlanconf/{wlan_id}"
        
        # Get current config
        current_config = self.get_wlan_by_id(wlan_id)
        
        # Update the SSID name
        old_name = current_config['name']
        current_config['name'] = new_ssid
        
        # Send the update
        response = self.session.put(url, json=current_config, verify=False)
        response.raise_for_status()
        
        print(f"[{datetime.now()}] Updated SSID from '{old_name}' to '{new_ssid}'")
        return response.json()

class SSIDRotator:
    def __init__(self, config):
        self.config = config
        self.state_file = config['state_file']
        self.ssid_list_file = config['ssid_list_file']
        self.ensure_dirs()
        self.load_ssid_list()
    
    def ensure_dirs(self):
        """Create necessary directories"""
        for filepath in [self.state_file, self.ssid_list_file]:
            directory = os.path.dirname(filepath)
            os.makedirs(directory, exist_ok=True)
    
    def load_ssid_list(self):
        """Load SSID list from JSON file with validation"""
        if not os.path.exists(self.ssid_list_file):
            raise Exception(f"SSID list file not found: {self.ssid_list_file}")
        
        with open(self.ssid_list_file, 'r') as f:
            data = json.load(f)
        
        # Load active rotation list (this is what gets rotated)
        self.ssid_list = data.get('active_rotation', [])
        
        # Load reserve pool (for reference/logging only)
        self.reserve_pool = data.get('reserve_pool', [])
        
        # Load protected SSIDs
        self.protected_ssids = data.get('protected_ssids', [])
        
        # Validation
        if not self.ssid_list:
            raise Exception("Active rotation list is empty - add SSIDs before rotating")
        
        if len(self.ssid_list) < 2:
            print(f"[{datetime.now()}] Warning: Only 1 SSID in active rotation - rotation will have no effect")
        
        # Check for duplicates in active rotation
        if len(self.ssid_list) != len(set(self.ssid_list)):
            print(f"[{datetime.now()}] Warning: Duplicate SSIDs in active rotation")
        
        # Calculate cycle time
        cycle_days = (len(self.ssid_list) * 18) / 24
        
        print(f"[{datetime.now()}] Loaded {len(self.ssid_list)} SSIDs in active rotation ({cycle_days:.1f} days per cycle)")
        print(f"[{datetime.now()}] Reserve pool contains {len(self.reserve_pool)} SSIDs")
        print(f"[{datetime.now()}] Protected SSIDs: {', '.join(self.protected_ssids)}")

    
    def load_state(self):
        """Load the current rotation state"""
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {"current_index": 0, "wlan_id": None}
    
    def save_state(self, state):
        """Save the rotation state"""
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def get_next_ssid(self, current_index):
        """Get the next SSID in the rotation"""
        next_index = (current_index + 1) % len(self.ssid_list)
        return self.ssid_list[next_index], next_index
    
    def is_protected_ssid(self, ssid_name):
        """Check if an SSID is in the protected list"""
        return ssid_name in self.protected_ssids
    
    def validate_target_wlan(self, api, wlan_id):
        """Ensure the target WLAN is not a protected SSID"""
        wlan = api.get_wlan_by_id(wlan_id)
        current_name = wlan['name']
        
        if self.is_protected_ssid(current_name):
            raise Exception(
                f"SAFETY CHECK FAILED: WLAN ID {wlan_id} has protected SSID '{current_name}'. "
                f"Protected SSIDs are: {', '.join(self.protected_ssids)}. "
                f"This script will NOT modify protected SSIDs."
            )
        
        print(f"[{datetime.now()}] Safety check passed: '{current_name}' is not a protected SSID")
        return True
    
    def discover_wlan_id(self, api):
        """Find the WLAN ID for the target SSID"""
        print(f"[{datetime.now()}] Discovering WLAN ID...")
        
        # First try the configured name
        wlan = api.get_wlan_by_name(self.config['current_ssid_name'])
        
        # If not found, try any name in the rotation list
        if wlan is None:
            print(f"[{datetime.now()}] '{self.config['current_ssid_name']}' not found, checking rotation list...")
            for ssid in self.ssid_list:
                wlan = api.get_wlan_by_name(ssid)
                if wlan:
                    print(f"[{datetime.now()}] Found WLAN with name '{ssid}'")
                    break
        
        if wlan is None:
            # List all available SSIDs for debugging
            all_wlans = api.get_wlan_configs()
            available_ssids = [w['name'] for w in all_wlans]
            raise Exception(
                f"Could not find WLAN with name '{self.config['current_ssid_name']}' "
                f"or any from the rotation list. Available SSIDs: {', '.join(available_ssids)}"
            )
        
        # Safety check: ensure it's not a protected SSID
        if self.is_protected_ssid(wlan['name']):
            raise Exception(
                f"SAFETY CHECK FAILED: The discovered WLAN has protected SSID '{wlan['name']}'. "
                f"Protected SSIDs cannot be used for rotation. "
                f"Please update CONFIG['current_ssid_name'] to point to a non-protected SSID."
            )
        
        print(f"[{datetime.now()}] Found WLAN ID: {wlan['_id']} (current name: '{wlan['name']}')")
        return wlan['_id']
    
    def rotate(self):
        """Perform the SSID rotation"""
        # Reload SSID list (in case it was updated)
        self.load_ssid_list()
        
        # Validation: check for overlap
        overlap = set(self.protected_ssids) & set(self.ssid_list)
        if overlap:
            raise Exception(
                f"CONFIGURATION ERROR: The following SSIDs appear in both protected and rotation lists: {overlap}"
            )
        
        # Load state
        state = self.load_state()
        
        # Connect to UniFi
        api = UniFiAPI(
            self.config['unifi_host'],
            self.config['username'],
            self.config['password']
        )
        
        # Get WLAN ID if not already stored
        if state.get('wlan_id') is None:
            state['wlan_id'] = self.discover_wlan_id(api)
        
        # CRITICAL: Validate that we're not about to modify a protected SSID
        self.validate_target_wlan(api, state['wlan_id'])
        
        # Get next SSID
        next_ssid, next_index = self.get_next_ssid(state['current_index'])
        
        # Additional safety check: ensure next SSID is not protected
        if self.is_protected_ssid(next_ssid):
            raise Exception(
                f"SAFETY CHECK FAILED: Next SSID '{next_ssid}' is in the protected list."
            )
        
        print(f"[{datetime.now()}] Rotating to SSID #{next_index + 1}/{len(self.ssid_list)}: {next_ssid}")
        
        # Update the SSID
        api.update_ssid(state['wlan_id'], next_ssid)
        
        # Update and save state
        state['current_index'] = next_index
        state['last_rotation'] = datetime.now().isoformat()
        self.save_state(state)
        
        next_ssid_preview = self.ssid_list[(next_index + 1) % len(self.ssid_list)]
        print(f"[{datetime.now()}] Rotation complete. Next rotation will use: {next_ssid_preview}")

def main():
    print(f"[{datetime.now()}] Starting SSID rotator...")
    
    try:
        rotator = SSIDRotator(CONFIG)
        rotator.rotate()
    except Exception as e:
        print(f"[{datetime.now()}] ERROR: {e}")
        raise

if __name__ == "__main__":
    main()
```

**Update the password** in the CONFIG section before saving:
```python
CONFIG = {
    "unifi_host": "192.168.102.1",
    "username": "admin",
    "password": "C0,5prings@@@",  # ← Update this with your actual password
    ...
}
```

Make it executable:
```bash
chmod +x ~/ssid_rotator/src/rotate_ssid.py
```

### Step 6: Create the Web Management Interface

Create `~/ssid_rotator/src/web_manager.py`:

```python
#!/usr/bin/env python3
from flask import Flask, render_template_string, request, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

CONFIG = {
    "ssid_list_file": "/var/lib/ssid_rotator/ssid_list.json",
    "state_file": "/var/lib/ssid_rotator/state.json"
}

def load_ssid_data():
    """Load SSID configuration"""
    if not os.path.exists(CONFIG['ssid_list_file']):
        return {
            "active_rotation": [],
            "reserve_pool": [],
            "protected_ssids": [],
            "last_updated": None,
            "updated_by": None
        }
    
    with open(CONFIG['ssid_list_file'], 'r') as f:
        return json.load(f)

def save_ssid_data(data):
    """Save SSID configuration"""
    data['last_updated'] = datetime.now().isoformat()
    with open(CONFIG['ssid_list_file'], 'w') as f:
        json.dump(data, f, indent=2)

def load_state():
    """Load rotation state"""
    if not os.path.exists(CONFIG['state_file']):
        return None
    
    with open(CONFIG['state_file'], 'r') as f:
        return json.load(f)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>SSID Rotation Manager</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #f5f5f5;
            padding: 20px;
            line-height: 1.6;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 { color: #333; margin-bottom: 10px; }
        .subtitle { color: #666; margin-bottom: 30px; font-size: 14px; }
        .section {
            margin-bottom: 40px;
            padding: 20px;
            background: #f9f9f9;
            border-radius: 8px;
        }
        .section h2 {
            color: #444;
            margin-bottom: 15px;
            font-size: 18px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .badge {
            background: #007bff;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: normal;
        }
        .badge.cycle-time {
            background: #28a745;
        }
        .badge.reserve {
            background: #6c757d;
        }
        .list-container {
            background: white;
            border: 1px solid #ddd;
            border-radius: 6px;
            padding: 15px;
        }
        .ssid-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px;
            border-bottom: 1px solid #eee;
            transition: background 0.2s;
        }
        .ssid-item:last-child { border-bottom: none; }
        .ssid-item:hover { background: #f5f5f5; }
        .ssid-item.current {
            background: #e3f2fd;
            font-weight: bold;
        }
        .ssid-item.reserve {
            background: #f8f9fa;
        }
        .ssid-item.protected {
            background: #fff3cd;
        }
        .ssid-name {
            display: flex;
            align-items: center;
            gap: 10px;
            flex: 1;
        }
        .ssid-index {
            background: #6c757d;
            color: white;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: bold;
        }
        .ssid-item.reserve .ssid-index {
            background: #adb5bd;
        }
        .tag {
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
        }
        .tag.current { background: #2196F3; color: white; }
        .tag.next { background: #4CAF50; color: white; }
        .tag.protected { background: #FF9800; color: white; }
        .btn {
            padding: 8px 12px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 13px;
            transition: all 0.2s;
            margin-left: 5px;
        }
        .btn-delete {
            background: #dc3545;
            color: white;
        }
        .btn-delete:hover {
            background: #c82333;
        }
        .btn-primary {
            background: #007bff;
            color: white;
            padding: 10px 20px;
        }
        .btn-primary:hover {
            background: #0056b3;
        }
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        .btn-secondary:hover {
            background: #5a6268;
        }
        .btn-success {
            background: #28a745;
            color: white;
        }
        .btn-success:hover {
            background: #218838;
        }
        .add-form {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        .add-form input {
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        .status-info {
            background: #e3f2fd;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
        }
        .status-row {
            display: flex;
            justify-content: space-between;
            margin: 5px 0;
            font-size: 14px;
        }
        .status-label {
            color: #666;
        }
        .status-value {
            font-weight: bold;
            color: #333;
        }
        .empty-state {
            text-align: center;
            padding: 40px;
            color: #999;
        }
        .warning {
            background: #fff3cd;
            border: 1px solid #ffc107;
            padding: 12px;
            border-radius: 4px;
            margin: 15px 0;
            color: #856404;
        }
        .info-box {
            background: #d1ecf1;
            border: 1px solid #bee5eb;
            padding: 12px;
            border-radius: 4px;
            margin: 15px 0;
            color: #0c5460;
            font-size: 13px;
        }
        .button-group {
            display: flex;
            gap: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔄 SSID Rotation Manager</h1>
        <p class="subtitle">Two-stage rotation system: Active rotation for fast cycles, reserve pool for storage</p>

        {% if state %}
        <div class="status-info">
            <div class="status-row">
                <span class="status-label">Current SSID:</span>
                <span class="status-value">{{ active[state.current_index] if state.current_index < active|length else 'N/A' }}</span>
            </div>
            <div class="status-row">
                <span class="status-label">Next Rotation:</span>
                <span class="status-value">{{ active[(state.current_index + 1) % active|length] if active else 'N/A' }}</span>
            </div>
            <div class="status-row">
                <span class="status-label">Last Rotation:</span>
                <span class="status-value">{{ state.last_rotation or 'Never' }}</span>
            </div>
            <div class="status-row">
                <span class="status-label">Position in Cycle:</span>
                <span class="status-value">{{ state.current_index + 1 }} of {{ active|length }}</span>
            </div>
            <div class="status-row">
                <span class="status-label">Full Cycle Time:</span>
                <span class="status-value">{{ ((active|length * 18) / 24)|round(1) }} days</span>
            </div>
        </div>
        {% endif %}

        <div class="section">
            <h2>
                ⚡ Active Rotation
                <span class="badge">{{ active|length }} SSIDs</span>
                <span class="badge cycle-time">
                    ~{{ ((active|length * 18) / 24)|round(1) }} day cycle
                </span>
            </h2>
            
            <div class="info-box">
                💡 These SSIDs are currently in rotation. They cycle every 18 hours. Move SSIDs to/from reserve pool to refresh the rotation.
            </div>

            <div class="list-container">
                {% if active %}
                    {% for ssid in active %}
                    <div class="ssid-item {% if state and loop.index0 == state.current_index %}current{% endif %}">
                        <div class="ssid-name">
                            <span class="ssid-index">{{ loop.index }}</span>
                            <span>{{ ssid }}</span>
                            {% if state and loop.index0 == state.current_index %}
                                <span class="tag current">Current</span>
                            {% elif state and loop.index0 == (state.current_index + 1) % active|length %}
                                <span class="tag next">Next</span>
                            {% endif %}
                        </div>
                        <div class="button-group">
                            <button class="btn btn-secondary" onclick="moveToReserve('{{ ssid }}')">→ Reserve</button>
                            <button class="btn btn-delete" onclick="deleteSSID('{{ ssid }}', 'active')">Delete</button>
                        </div>
                    </div>
                    {% endfor %}
                {% else %}
                    <div class="empty-state">
                        <p>No SSIDs in active rotation</p>
                        <p style="font-size: 12px; margin-top: 10px;">Add SSIDs below or promote from reserve pool</p>
                    </div>
                {% endif %}
            </div>

            <form class="add-form" onsubmit="addSSID(event, 'active')">
                <input type="text" id="new-active-ssid" placeholder="Add new SSID to active rotation..." required>
                <button type="submit" class="btn btn-primary">Add to Active</button>
            </form>
        </div>

        <div class="section">
            <h2>
                💾 Reserve Pool
                <span class="badge reserve">{{ reserve|length }} SSIDs</span>
            </h2>
            
            <div class="info-box">
                📦 SSIDs in reserve are not currently rotating. Promote them to active rotation when you want to see them appear.
            </div>

            <div class="list-container">
                {% if reserve %}
                    {% for ssid in reserve %}
                    <div class="ssid-item reserve">
                        <div class="ssid-name">
                            <span class="ssid-index">💤</span>
                            <span>{{ ssid }}</span>
                        </div>
                        <div class="button-group">
                            <button class="btn btn-success" onclick="moveToActive('{{ ssid }}')">⚡ Activate</button>
                            <button class="btn btn-delete" onclick="deleteSSID('{{ ssid }}', 'reserve')">Delete</button>
                        </div>
                    </div>
                    {% endfor %}
                {% else %}
                    <div class="empty-state">
                        <p>Reserve pool is empty</p>
                        <p style="font-size: 12px; margin-top: 10px;">Add SSIDs here for future use</p>
                    </div>
                {% endif %}
            </div>

            <form class="add-form" onsubmit="addSSID(event, 'reserve')">
                <input type="text" id="new-reserve-ssid" placeholder="Add new SSID to reserve pool..." required>
                <button type="submit" class="btn btn-primary">Add to Reserve</button>
            </form>
        </div>

        <div class="section">
            <h2>
                🔒 Protected SSIDs
                <span class="badge" style="background: #ff9800;">{{ protected|length }}</span>
            </h2>
            
            <div class="warning">
                ⚠️ Protected SSIDs will never be modified by the rotation script
            </div>

            <div class="list-container">
                {% if protected %}
                    {% for ssid in protected %}
                    <div class="ssid-item protected">
                        <div class="ssid-name">
                            <span class="ssid-index">🔒</span>
                            <span>{{ ssid }}</span>
                            <span class="tag protected">Protected</span>
                        </div>
                        <button class="btn btn-delete" onclick="deleteSSID('{{ ssid }}', 'protected')">Remove</button>
                    </div>
                    {% endfor %}
                {% else %}
                    <div class="empty-state">
                        <p>No protected SSIDs configured</p>
                    </div>
                {% endif %}
            </div>

            <form class="add-form" onsubmit="addSSID(event, 'protected')">
                <input type="text" id="new-protected-ssid" placeholder="Enter SSID to protect..." required>
                <button type="submit" class="btn btn-primary">Add Protected SSID</button>
            </form>
        </div>

        <div style="text-align: center; color: #999; font-size: 12px; margin-top: 30px;">
            Last updated: {{ last_updated or 'Never' }}
        </div>
    </div>

    <script>
        function addSSID(event, listType) {
            event.preventDefault();
            const inputId = listType === 'active' ? 'new-active-ssid' : 
                           listType === 'reserve' ? 'new-reserve-ssid' : 
                           'new-protected-ssid';
            const input = document.getElementById(inputId);
            const ssid = input.value.trim();
            
            if (!ssid) return;

            fetch('/api/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ssid: ssid, list_type: listType })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    alert('Error: ' + data.error);
                }
            });
        }

        function deleteSSID(ssid, listType) {
            if (!confirm(`Delete "${ssid}" from ${listType}?`)) return;

            fetch('/api/delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ssid: ssid, list_type: listType })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    alert('Error: ' + data.error);
                }
            });
        }

        function moveToReserve(ssid) {
            if (!confirm(`Move "${ssid}" to reserve pool?`)) return;

            fetch('/api/move', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ssid: ssid, from: 'active', to: 'reserve' })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    alert('Error: ' + data.error);
                }
            });
        }

        function moveToActive(ssid) {
            if (!confirm(`Move "${ssid}" to active rotation?`)) return;

            fetch('/api/move', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ssid: ssid, from: 'reserve', to: 'active' })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    alert('Error: ' + data.error);
                }
            });
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    data = load_ssid_data()
    state = load_state()
    
    return render_template_string(
        HTML_TEMPLATE,
        active=data.get('active_rotation', []),
        reserve=data.get('reserve_pool', []),
        protected=data.get('protected_ssids', []),
        last_updated=data.get('last_updated'),
        state=state
    )

@app.route('/api/add', methods=['POST'])
def add_ssid():
    req_data = request.json
    ssid = req_data.get('ssid', '').strip()
    list_type = req_data.get('list_type', 'active')  # 'active', 'reserve', or 'protected'
    
    if not ssid:
        return jsonify({'success': False, 'error': 'SSID name is required'})
    
    data = load_ssid_data()
    
    # Check if SSID already exists in any list
    all_ssids = (data.get('active_rotation', []) + 
                 data.get('reserve_pool', []) + 
                 data.get('protected_ssids', []))
    
    if ssid in all_ssids:
        return jsonify({'success': False, 'error': 'SSID already exists in another list'})
    
    # Add to appropriate list
    if list_type == 'protected':
        if 'protected_ssids' not in data:
            data['protected_ssids'] = []
        data['protected_ssids'].append(ssid)
    elif list_type == 'reserve':
        if 'reserve_pool' not in data:
            data['reserve_pool'] = []
        data['reserve_pool'].append(ssid)
    else:  # 'active'
        if 'active_rotation' not in data:
            data['active_rotation'] = []
        data['active_rotation'].append(ssid)
    
    data['updated_by'] = 'web_interface'
    save_ssid_data(data)
    
    return jsonify({'success': True})

@app.route('/api/delete', methods=['POST'])
def delete_ssid():
    req_data = request.json
    ssid = req_data.get('ssid', '').strip()
    list_type = req_data.get('list_type', 'active')  # 'active', 'reserve', or 'protected'
    
    if not ssid:
        return jsonify({'success': False, 'error': 'SSID name is required'})
    
    data = load_ssid_data()
    
    # Remove from appropriate list
    if list_type == 'protected':
        if ssid in data.get('protected_ssids', []):
            data['protected_ssids'].remove(ssid)
        else:
            return jsonify({'success': False, 'error': 'SSID not found in protected list'})
    elif list_type == 'reserve':
        if ssid in data.get('reserve_pool', []):
            data['reserve_pool'].remove(ssid)
        else:
            return jsonify({'success': False, 'error': 'SSID not found in reserve pool'})
    else:  # 'active'
        if ssid in data.get('active_rotation', []):
            data['active_rotation'].remove(ssid)
        else:
            return jsonify({'success': False, 'error': 'SSID not found in active rotation'})
    
    data['updated_by'] = 'web_interface'
    save_ssid_data(data)
    
    return jsonify({'success': True})

@app.route('/api/move', methods=['POST'])
def move_ssid():
    """Move SSID between active and reserve lists"""
    req_data = request.json
    ssid = req_data.get('ssid', '').strip()
    from_list = req_data.get('from', 'active')
    to_list = req_data.get('to', 'reserve')
    
    if not ssid:
        return jsonify({'success': False, 'error': 'SSID name is required'})
    
    data = load_ssid_data()
    
    # Remove from source list
    if from_list == 'active':
        if ssid not in data.get('active_rotation', []):
            return jsonify({'success': False, 'error': 'SSID not found in active rotation'})
        data['active_rotation'].remove(ssid)
    elif from_list == 'reserve':
        if ssid not in data.get('reserve_pool', []):
            return jsonify({'success': False, 'error': 'SSID not found in reserve pool'})
        data['reserve_pool'].remove(ssid)
    else:
        return jsonify({'success': False, 'error': 'Invalid source list'})
    
    # Add to destination list
    if to_list == 'active':
        if 'active_rotation' not in data:
            data['active_rotation'] = []
        data['active_rotation'].append(ssid)
    elif to_list == 'reserve':
        if 'reserve_pool' not in data:
            data['reserve_pool'] = []
        data['reserve_pool'].append(ssid)
    else:
        return jsonify({'success': False, 'error': 'Invalid destination list'})
    
    data['updated_by'] = 'web_interface'
    save_ssid_data(data)
    
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
```

Make it executable:
```bash
chmod +x ~/ssid_rotator/src/web_manager.py
```

---

## Two-Stage List Architecture

### Why Two-Stage?

With a firm 18-hour rotation period and a collection of 10-20 SSIDs, a single rotating list would take 7.5 to 15 days for a full cycle. The two-stage approach solves this by:

1. **Active Rotation (5-7 SSIDs)**: Fast cycling through your current favorites
   - 5 SSIDs × 18 hours = **3.75 days** per cycle
   - 7 SSIDs × 18 hours = **5.25 days** per cycle

2. **Reserve Pool (5-15 SSIDs)**: Storage for SSIDs you want to keep but not show right now
   - Swap in/out whenever you want something fresh
   - Perfect for seasonal, themed, or occasional use SSIDs

### How It Works

```
┌─────────────────────────────┐
│   ACTIVE ROTATION (5-7)     │  ← Rotates every 18 hours
│  - FBI Surveillance Van #4  │
│  - Pretty Fly for a WiFi    │
│  - The LAN Before Time      │
│  - Tell My WiFi Love Her    │
│  - Drop It Like Its Hotspot │
└─────────────────────────────┘
           ↕️ Move via Web UI
┌─────────────────────────────┐
│   RESERVE POOL (5-15)       │  ← Not rotating
│  - LAN Solo                 │
│  - The Ping in the North    │
│  - Silence of the LANs      │
│  - ... more SSIDs ...       │
└─────────────────────────────┘
```

### Usage Patterns

**Low Maintenance Mode:**
- Set 5-7 favorite SSIDs in active rotation
- Leave reserve pool untouched for months
- Fast cycling through your best jokes

**Active Curator Mode:**
- Swap 1-2 SSIDs every week via web UI
- Test new SSIDs by promoting to active
- Keep rotation fresh without managing too many at once

**Seasonal/Themed Rotation:**
- **December**: Holiday themed SSIDs in active
- **October**: Halloween themed SSIDs in active  
- **Super Bowl Weekend**: Sports themed in active
- **Rest of year**: Your "greatest hits" in active

### Benefits Over Single List

| Aspect | Single List (10-20 SSIDs) | Two-Stage (5-7 Active) |
|--------|---------------------------|------------------------|
| Cycle Time | 7.5-15 days | 3.75-5.25 days |
| Control | All or nothing | Curated experience |
| Adding New SSIDs | Increases cycle time | Add to reserve, no impact |
| Seasonal Themes | Difficult | Easy to swap |
| Testing New SSIDs | Committed immediately | Test in active first |

---

## Configuration

### Update Rotation Script Configuration

Edit `~/ssid_rotator/src/rotate_ssid.py` and update the CONFIG section:

```python
CONFIG = {
    "unifi_host": "192.168.102.1",  # Your UDR IP address
    "username": "admin",           # Your UDR admin username
    "password": "C0,5prings@@@",   # Your UDR admin password
    "current_ssid_name": "Fuck the orange turd",  # Current name of the SSID you want to rotate
    "state_file": "/var/lib/ssid_rotator/state.json",
    "ssid_list_file": "/var/lib/ssid_rotator/ssid_list.json"
}
```

### Update SSID List Configuration

Edit `/var/lib/ssid_rotator/ssid_list.json` and configure your lists:

```json
{
  "active_rotation": [
    "FBI Surveillance Van #4",
    "Pretty Fly for a WiFi",
    "The LAN Before Time"
  ],
  "reserve_pool": [
    "LAN Solo",
    "The Ping in the North",
    "Silence of the LANs"
  ],
  "protected_ssids": [
    "7Oaks",
    "7Oaks-IOT",
    "newnative",
    "7Oaks-Work"
  ],
  "last_updated": null,
  "updated_by": "initial_setup"
}
```

**Important Notes:**
- The SSID **"Fuck the orange turd"** will be the one that rotates
- The 5 networks in `protected_ssids` will **NEVER** be modified
- Start with **5 SSIDs in active rotation** for a ~4 day cycle
- Put remaining SSIDs in **reserve pool**
- Use the web interface to swap SSIDs between active and reserve as desired

---

## Testing

### Test the Rotation Script Manually

```bash
# Test a manual rotation
python3 ~/ssid_rotator/src/rotate_ssid.py

# Check the output for any errors
# Verify the SSID changed in your UniFi interface at https://192.168.102.1
```

### Test the Web Interface

```bash
# Start the web manager
python3 ~/ssid_rotator/src/web_manager.py

# Open browser to http://rotator.local:5000 or http://192.168.102.205:5000
# Try adding/removing SSIDs
```

---

## Updating the Application

### Production Update Workflow

After initial deployment, **all code changes should be made on your PC and pushed to GitHub**. The Pi pulls updates using a single command.

### On Your PC (Development)

```bash
# 1. Make changes to Python scripts locally
cd ~/path/to/ssid_rotator

# 2. Test changes if possible (API connectivity, syntax, etc.)
python3 -m py_compile src/rotate_ssid.py
python3 -m py_compile src/web_manager.py

# 3. Commit and push to GitHub
git add .
git commit -m "Description of your changes"
git push origin main
```

### On the Raspberry Pi (Production)

```bash
# SSH into Pi
ssh pi@rotator.local

# Run the update script
bash ~/ssid_rotator/ops_tools/update_app.sh
```

**What `ops_tools/update_app.sh` does:**
1. Fetches latest code from GitHub
2. Resets local repository to `origin/main` (discards any local changes)
3. Cleans Python cache (`__pycache__`, `.pyc` files)
4. Sets execute permissions on scripts
5. Restarts web interface service
6. Logs all actions to `/var/log/ssid-rotator.log`

### Important Rules

✅ **DO:**
- Edit code on PC/laptop
- Test changes before pushing
- Use `update_app.sh` to deploy to Pi
- Edit SSID lists via web interface

❌ **DON'T:**
- Edit Python files directly on Pi
- Make git commits from Pi
- Manually restart services (let update script handle it)
- Edit `ssid_list.json` directly (use web UI)

### Manual Service Restart (If Needed)

If you need to restart services without updating code:

```bash
# Restart web interface only
sudo systemctl restart ssid-web-manager

# Check web interface status
sudo systemctl status ssid-web-manager

# View recent logs
tail -50 /var/log/ssid-rotator.log
```

---

## Scheduling Automatic Rotation

### Option 1: Cron Job (Recommended for Simple Setup)

```bash
# Edit crontab
crontab -e

# Add this line for rotation every 18 hours
0 */18 * * * /usr/bin/python3 ~/ssid_rotator/src/rotate_ssid.py >> /var/log/ssid-rotator.log 2>&1
```

### Option 2: Systemd Timer (More Precise)

**Note:** Once repository structure is complete, service files will be in `~/ssid_rotator/deployment/systemd/` and can be copied with:
```bash
sudo cp ~/ssid_rotator/deployment/systemd/*.service /etc/systemd/system/
sudo cp ~/ssid_rotator/deployment/systemd/*.timer /etc/systemd/system/
```

For now, create manually:

Create `/etc/systemd/system/ssid-rotator.service`:

```ini
[Unit]
Description=SSID Rotator Service

[Service]
Type=oneshot
User=pi
ExecStart=/usr/bin/python3 /home/pi/ssid_rotator/rotate_ssid.py
StandardOutput=append:/var/log/ssid-rotator.log
StandardError=append:/var/log/ssid-rotator.log
```

Create `/etc/systemd/system/ssid-rotator.timer`:

```ini
[Unit]
Description=SSID Rotator Timer

[Timer]
OnBootSec=5min
OnUnitActiveSec=18h
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable ssid-rotator.timer
sudo systemctl start ssid-rotator.timer

# Check status
sudo systemctl status ssid-rotator.timer
sudo systemctl list-timers
```

---

## Using the Web Interface

### Overview

The web interface provides easy management of your two-stage SSID rotation system. Access it at `http://rotator.local:5000` or `http://192.168.102.205:5000`

### Managing Active Rotation

The **Active Rotation** section shows SSIDs currently cycling:
- Green badge shows cycle time (e.g., "~3.8 day cycle")
- Current SSID is highlighted in blue
- Click **"→ Reserve"** to move SSID to reserve pool
- Add new SSIDs directly to active rotation with the form

**Best Practice:** Keep 5-7 SSIDs in active rotation for optimal cycle time (3.75-5.25 days)

### Managing Reserve Pool

The **Reserve Pool** section stores SSIDs not currently rotating:
- SSIDs here don't appear until you promote them
- Click **"⚡ Activate"** to move SSID to active rotation
- Perfect for seasonal SSIDs, new ideas, or occasional use
- No limit on reserve pool size

### Common Workflows

**Adding a New SSID:**
1. Add to reserve pool first
2. See how you like it in the list
3. Promote to active if it's good
4. Delete from reserve if you don't like it

**Seasonal Refresh (e.g., Christmas):**
1. Move 2-3 current active SSIDs to reserve
2. Promote 2-3 holiday-themed SSIDs from reserve to active
3. Enjoy themed rotation for December
4. Swap back in January

**Testing New Ideas:**
1. Add several new SSIDs to reserve
2. Over time, promote one at a time to active
3. See which ones get noticed/reactions
4. Keep winners in active, move duds back to reserve

### Features

✅ **Two-Stage List Management** - Active rotation vs. reserve pool  
✅ **Real-time Status** - Current SSID, next SSID, cycle time  
✅ **One-Click Movement** - Promote/demote between lists  
✅ **Visual Indicators** - Current highlighted, next marked  
✅ **Safety Validation** - Prevents duplicates across lists  
✅ **Protected SSIDs** - Separate management for production networks  

---

## Running Web Interface as a Service

**Note:** Once repository structure is complete, this file will be at `~/ssid_rotator/deployment/systemd/ssid-web-manager.service`.

For now, create `/etc/systemd/system/ssid-web-manager.service`:

```ini
[Unit]
Description=SSID Rotation Web Manager
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/ssid_rotator
ExecStart=/usr/bin/python3 /home/pi/ssid_rotator/src/web_manager.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable ssid-web-manager
sudo systemctl start ssid-web-manager
sudo systemctl status ssid-web-manager
```

Access the web interface at: `http://rotator.local:5000` or `http://192.168.102.205:5000`

**After Initial Setup:** The `ops_tools/update_app.sh` script automatically restarts this service when pulling code updates.

---

## Monitoring and Logs

### View Rotation Logs

```bash
# View recent rotations
tail -f /var/log/ssid-rotator.log

# View last 50 lines
tail -n 50 /var/log/ssid-rotator.log
```

### Check Current State

```bash
# View current rotation state
cat /var/lib/ssid_rotator/state.json

# View SSID list configuration
cat /var/lib/ssid_rotator/ssid_list.json
```

### Setup Log Rotation

Create `/etc/logrotate.d/ssid-rotator`:

```
/var/log/ssid-rotator.log {
    weekly
    rotate 4
    compress
    missingok
    notifempty
}
```

---

## Funny SSID Ideas

### Classic Funny
- FBI Surveillance Van #4
- Pretty Fly for a WiFi
- The LAN Before Time
- Tell My WiFi Love Her
- Drop It Like Its Hotspot
- Abraham Linksys
- The Promised LAN
- Silence of the LANs

### Neighborhood Trolling
- Yell PENIS for Password
- Mom Click Here For Internet
- Get Off My LAN
- Not The WiFi You're Looking For
- Connect at Own Risk
- Virus Distribution Center
- Loading...
- Searching...

### Geeky References
- Winternet Is Coming
- LAN Solo
- The Ping in the North
- House LANnister
- Obi-WAN Kenobi
- The Matrix Has You
- Is This The Krusty Krab
- No This Is Patrick

### Tech Support Jokes
- 404 Network Unavailable
- IP Freely
- Router? I Hardly Know Her
- Your Network Is Down
- Stop Pinging Me
- Network Not Found
- Connection Refused

---

## Troubleshooting

### Rotation Script Not Working

```bash
# Check if script can reach UDR
curl -k https://192.168.102.1

# Test login manually
python3 -c "
import requests
import urllib3
urllib3.disable_warnings()
r = requests.post('https://192.168.102.1/proxy/network/api/auth/login',
                  json={'username': 'admin', 'password': 'C0,5prings@@@'},
                  verify=False)
print(r.status_code, r.json())
"

# Check for Python errors
python3 ~/ssid_rotator/src/rotate_ssid.py
```

### Web Interface Not Accessible

```bash
# Check if service is running
sudo systemctl status ssid-web-manager

# Check if port is listening
sudo netstat -tlnp | grep 5000

# Check logs
sudo journalctl -u ssid-web-manager -f
```

### SSID Not Changing

1. Check logs: `tail /var/log/ssid-rotator.log`
2. Verify WLAN ID is correct
3. Check that target SSID is not in protected list
4. Verify UDR credentials are correct
5. Check that SSID list is not empty

### Protected SSID Being Modified

The script has multiple safety checks. If this happens:
1. Check `/var/lib/ssid_rotator/ssid_list.json`
2. Verify protected_ssids list is correct
3. Check rotation script logs for safety check messages

---

## Backup and Restore

### Backup Configuration

```bash
# Backup all configuration
tar -czf ssid-rotator-backup-$(date +%Y%m%d).tar.gz \
    /var/lib/ssid_rotator/ \
    ~/ssid_rotator/ \
    /etc/systemd/system/ssid-*.service \
    /etc/systemd/system/ssid-*.timer

# Backup just the SSID list
cp /var/lib/ssid_rotator/ssid_list.json \
   /var/lib/ssid_rotator/ssid_list.json.backup
```

### Restore Configuration

```bash
# Restore from backup
tar -xzf ssid-rotator-backup-YYYYMMDD.tar.gz -C /

# Reload systemd
sudo systemctl daemon-reload
```

---

## Security Considerations

### Web Interface Security

1. **Firewall**: Only allow access from trusted IPs
   ```bash
   # Example: Only allow from local network
   sudo ufw allow from 192.168.1.0/24 to any port 5000
   ```

2. **Add HTTPS**: Use SSL certificates (you're familiar with this from your Flask work)
   ```python
   # In web_manager.py
   app.run(host='0.0.0.0', port=5443, ssl_context=('cert.pem', 'key.pem'))
   ```

3. **Add Authentication**: Consider adding basic auth for the web interface

### UniFi Credentials

- Store credentials securely
- Consider using environment variables instead of hardcoded passwords
- Use a dedicated admin account with limited permissions if possible

---

## Maintenance

### Update Code (Python Scripts)

**All code changes must be made on your PC and deployed via Git:**

```bash
# On PC: Make changes, commit, push
git add .
git commit -m "Your changes"
git push origin main

# On Pi: Pull updates
ssh pi@rotator.local
bash ~/ssid_rotator/ops_tools/update_app.sh
```

**Never edit Python files directly on the Pi.** The git workflow ensures clean deployments and easy rollbacks.

### Update SSID Lists

**Recommended: Via Web Interface**
1. Open `http://rotator.local:5000` or `http://192.168.102.205:5000`
2. Add/remove SSIDs through the UI
3. Move SSIDs between active rotation and reserve pool

**Alternative: Direct File Edit (Not Recommended)**
```bash
# Only if web interface is unavailable
nano /var/lib/ssid_rotator/ssid_list.json
# Edit and save - be careful with JSON syntax
```

⚠️ **Warning:** Direct file editing bypasses validation and can cause JSON syntax errors. Always use the web interface when possible.

### Check Rotation Schedule

```bash
# For cron
crontab -l

# For systemd timer
sudo systemctl list-timers | grep ssid
```

### Manual Rotation

```bash
# Force a rotation now (useful for testing)
python3 ~/ssid_rotator/src/rotate_ssid.py

# View results
tail -20 /var/log/ssid-rotator.log
```

### Backup Configuration

```bash
# Backup SSID list
cp /var/lib/ssid_rotator/ssid_list.json ~/ssid_list_backup_$(date +%Y%m%d).json

# Backup state
cp /var/lib/ssid_rotator/state.json ~/state_backup_$(date +%Y%m%d).json

# Copy to PC for safekeeping
scp pi@rotator.local:~/ssid_list_backup_*.json ~/backups/
```

---

## Uninstallation

```bash
# Stop services
sudo systemctl stop ssid-web-manager
sudo systemctl disable ssid-web-manager
sudo systemctl stop ssid-rotator.timer
sudo systemctl disable ssid-rotator.timer

# Remove files
sudo rm -rf ~/ssid_rotator
sudo rm -rf /var/lib/ssid_rotator
sudo rm /var/log/ssid-rotator.log
sudo rm /etc/systemd/system/ssid-*.service
sudo rm /etc/systemd/system/ssid-*.timer

# Remove cron job
crontab -e  # Remove the SSID rotator line

# Reload systemd
sudo systemctl daemon-reload
```

---

## Advanced Customization

### Change Rotation Interval

Edit cron job to change from 18 hours to something else:

```cron
# Every 12 hours
0 */12 * * * /usr/bin/python3 ~/ssid_rotator/src/rotate_ssid.py >> /var/log/ssid-rotator.log 2>&1

# Every 6 hours
0 */6 * * * /usr/bin/python3 ~/ssid_rotator/src/rotate_ssid.py >> /var/log/ssid-rotator.log 2>&1

# Once per day at 3am
0 3 * * * /usr/bin/python3 ~/ssid_rotator/src/rotate_ssid.py >> /var/log/ssid-rotator.log 2>&1
```

### Add Notifications

Add to rotation script to send notifications when SSID changes:

```python
# Email notification
def send_email_notification(old_ssid, new_ssid):
    import smtplib
    from email.message import EmailMessage
    
    msg = EmailMessage()
    msg['Subject'] = f'SSID Changed: {new_ssid}'
    msg['From'] = 'ssid-rotator@example.com'
    msg['To'] = 'you@example.com'
    msg.set_content(f'SSID rotated from "{old_ssid}" to "{new_ssid}"')
    
    with smtplib.SMTP('localhost') as s:
        s.send_message(msg)

# Webhook notification (Discord, Slack, etc.)
def send_webhook_notification(old_ssid, new_ssid):
    import requests
    webhook_url = "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL"
    data = {
        "content": f"🔄 SSID changed from '{old_ssid}' to '{new_ssid}'"
    }
    requests.post(webhook_url, json=data)
```

### Random Rotation

Modify rotation script to pick randomly instead of sequentially:

```python
import random

def get_next_ssid(self, current_index):
    """Get a random SSID from the list"""
    available_ssids = [i for i in range(len(self.ssid_list)) if i != current_index]
    next_index = random.choice(available_ssids) if available_ssids else 0
    return self.ssid_list[next_index], next_index
```

---

## Future Features: Rotation Strategies

Currently, the system rotates through SSIDs **sequentially** (in-line, one after another). This section explores alternative rotation strategies you could implement.

### Current Behavior: Sequential Rotation

The default rotation is sequential through the list:

```python
def get_next_ssid(self, current_index):
    """Get the next SSID in the rotation"""
    next_index = (current_index + 1) % len(self.ssid_list)
    return self.ssid_list[next_index], next_index
```

**Example:**
If your list is:
1. FBI Surveillance Van #4
2. Pretty Fly for a WiFi
3. The LAN Before Time
4. Tell My WiFi Love Her
5. Drop It Like Its Hotspot

Rotation pattern: 1 → 2 → 3 → 4 → 5 → 1 → 2 → ...

### Alternative Strategy 1: Random Rotation

For more unpredictability and entertainment value:

```python
import random

def get_next_ssid(self, current_index):
    """Get a random SSID from the list (avoiding current)"""
    # Get all indices except the current one
    available_indices = [i for i in range(len(self.ssid_list)) if i != current_index]
    
    # If only one SSID, or empty list after filtering
    if not available_indices:
        return self.ssid_list[0], 0
    
    # Pick random index
    next_index = random.choice(available_indices)
    return self.ssid_list[next_index], next_index
```

**Pros:**
- More unpredictable and entertaining
- Harder for neighbors to predict pattern
- Each rotation feels fresh

**Cons:**
- Some SSIDs might not appear for long periods
- Harder to debug issues
- Less predictable for your own use

### Alternative Strategy 2: Weighted Random

Some SSIDs are funnier than others - make your favorites appear more often:

```python
import random

def get_next_ssid(self, current_index):
    """Get next SSID with weighted probability"""
    # Define weights (higher = appears more often)
    weights = {
        "FBI Surveillance Van #4": 3,     # 3x more likely
        "Pretty Fly for a WiFi": 2,       # 2x more likely
        "Tell My WiFi Love Her": 2,       # 2x more likely
        # Others default to weight of 1
    }
    
    # Build weighted list
    weighted_choices = []
    for i, ssid in enumerate(self.ssid_list):
        if i != current_index:  # Don't repeat current
            weight = weights.get(ssid, 1)
            weighted_choices.extend([i] * weight)
    
    if not weighted_choices:
        return self.ssid_list[0], 0
    
    next_index = random.choice(weighted_choices)
    return self.ssid_list[next_index], next_index
```

**To store weights in the JSON file:**

```json
{
  "ssids": [
    {
      "name": "FBI Surveillance Van #4",
      "weight": 3
    },
    {
      "name": "Pretty Fly for a WiFi",
      "weight": 2
    },
    {
      "name": "The LAN Before Time",
      "weight": 1
    }
  ],
  "protected_ssids": ["ProdSSID1", "ProdSSID2"]
}
```

### Alternative Strategy 3: Time-Based Rotation

Rotate based on time of day or day of week:

```python
from datetime import datetime

def get_next_ssid(self, current_index):
    """Select SSID based on time of day"""
    now = datetime.now()
    hour = now.hour
    
    # Morning SSIDs (6am - 12pm)
    morning_ssids = ["Good Morning Vietnam", "Rise and Shine"]
    
    # Afternoon SSIDs (12pm - 6pm)
    afternoon_ssids = ["Working Hard or Hardly Working", "Still At Work"]
    
    # Evening SSIDs (6pm - 12am)
    evening_ssids = ["Netflix and Chill", "Game Time"]
    
    # Night SSIDs (12am - 6am)
    night_ssids = ["Why Are You Awake", "Go To Sleep"]
    
    if 6 <= hour < 12:
        ssid_list = morning_ssids
    elif 12 <= hour < 18:
        ssid_list = afternoon_ssids
    elif 18 <= hour < 24:
        ssid_list = evening_ssids
    else:
        ssid_list = night_ssids
    
    # Filter to only SSIDs that exist in main list
    available = [self.ssid_list.index(s) for s in ssid_list if s in self.ssid_list]
    
    if available:
        next_index = random.choice(available)
    else:
        # Fallback to sequential if no time-based SSIDs found
        next_index = (current_index + 1) % len(self.ssid_list)
    
    return self.ssid_list[next_index], next_index
```

### Alternative Strategy 4: Shuffle Rotation

Go through all SSIDs in random order, then reshuffle:

```python
import random

class SSIDRotator:
    def __init__(self, config):
        # ... existing code ...
        self.shuffle_order = []
    
    def get_next_ssid(self, current_index):
        """Shuffle through all SSIDs before repeating"""
        # If shuffle list is empty or exhausted, create new shuffle
        if not hasattr(self, 'shuffle_order') or not self.shuffle_order:
            self.shuffle_order = list(range(len(self.ssid_list)))
            random.shuffle(self.shuffle_order)
            
            # Remove current SSID from beginning of new shuffle
            if current_index in self.shuffle_order:
                self.shuffle_order.remove(current_index)
        
        # Get next from shuffle
        next_index = self.shuffle_order.pop(0)
        return self.ssid_list[next_index], next_index
```

This ensures every SSID appears once before any SSID repeats.

### Comparison of Rotation Strategies

| Strategy | Predictability | Fair Distribution | Fun Factor | Complexity |
|----------|---------------|-------------------|------------|------------|
| Sequential | High | Perfect | Medium | Low |
| Random | Low | Good (over time) | High | Low |
| Weighted | Low | Configurable | High | Medium |
| Time-Based | Medium | Variable | Very High | Medium |
| Shuffle | Medium | Perfect | High | Medium |

### Implementation: Adding Rotation Strategy Selection

To make rotation strategy configurable, update the code:

**1. Add to configuration file:**

```json
{
  "ssids": ["SSID1", "SSID2", "SSID3"],
  "protected_ssids": ["Prod1"],
  "rotation_strategy": "sequential",
  "rotation_config": {
    "weights": {
      "SSID1": 2,
      "SSID2": 1
    }
  }
}
```

**2. Update SSIDRotator class:**

```python
def get_next_ssid(self, current_index):
    """Get next SSID based on configured strategy"""
    strategy = self.rotation_config.get('rotation_strategy', 'sequential')
    
    if strategy == 'sequential':
        return self._get_next_sequential(current_index)
    elif strategy == 'random':
        return self._get_next_random(current_index)
    elif strategy == 'weighted':
        return self._get_next_weighted(current_index)
    elif strategy == 'time_based':
        return self._get_next_time_based(current_index)
    elif strategy == 'shuffle':
        return self._get_next_shuffle(current_index)
    else:
        # Default to sequential
        return self._get_next_sequential(current_index)

def _get_next_sequential(self, current_index):
    """Sequential rotation"""
    next_index = (current_index + 1) % len(self.ssid_list)
    return self.ssid_list[next_index], next_index

def _get_next_random(self, current_index):
    """Random rotation"""
    available_indices = [i for i in range(len(self.ssid_list)) if i != current_index]
    if not available_indices:
        return self.ssid_list[0], 0
    next_index = random.choice(available_indices)
    return self.ssid_list[next_index], next_index

# ... implement other strategies ...
```

**3. Add to Web Interface:**

```html
<div class="section">
    <h2>Rotation Strategy</h2>
    <select id="rotation-strategy">
        <option value="sequential">Sequential (1→2→3→...)</option>
        <option value="random">Random</option>
        <option value="weighted">Weighted Random</option>
        <option value="shuffle">Shuffle (no repeats until all shown)</option>
    </select>
    <button onclick="updateStrategy()">Update Strategy</button>
</div>
```

### Recommendations

**Start with Sequential** because:
- Simple and predictable
- Easy to debug
- Fair to all SSIDs
- Easy to understand rotation pattern

**Upgrade to Random** if you want:
- More entertainment value
- Harder for neighbors to predict
- More chaos and fun

**Use Weighted** if you have:
- Favorite SSIDs you want more often
- SSIDs for specific audiences/times
- Want control over frequency

**Try Time-Based** for:
- Context-aware humor
- Different audiences at different times
- Holiday/event-specific SSIDs

**Use Shuffle** for:
- Perfect fairness with variety
- Best of both sequential and random
- Guaranteed no immediate repeats

---

## FAQ

**Q: Can I have multiple rotating SSIDs?**
A: Yes, but you'd need to run separate instances with different config files and state files.

**Q: Will this disconnect my devices?**
A: Only devices connected to the rotating SSID. Your protected SSIDs are never touched.

**Q: Can I change the order of SSIDs in the rotation?**
A: Yes, just drag and drop in the web interface (or edit the JSON file manually).

**Q: What happens if I edit the list while a rotation is happening?**
A: The rotation script reloads the list before each rotation, so changes take effect immediately.

**Q: Can I see rotation history?**
A: Check the log file at `/var/log/ssid-rotator.log` for full history.

**Q: Does this work with other UniFi devices?**
A: Yes! This should work with any UniFi controller/device that has the standard API.

---

## Support and Updates

This is a standalone system with no external dependencies beyond Python and Flask. 

To update:
- Simply replace the Python scripts with newer versions
- Your configuration files remain unchanged

For issues:
- Check logs first
- Verify API connectivity to UDR
- Test manually before troubleshooting cron/systemd

---

## Failure Points and Mitigation

### Understanding Points of Failure

This section documents potential failure modes and how to prevent or recover from them.

### Failure Impact Matrix

| Failure Type | Impact | Likelihood | Detection | Recovery |
|-------------|--------|------------|-----------|----------|
| API Changes | High | Low | Immediate | Manual fix |
| Network Issues | Medium | Medium | Automatic retry | Self-healing |
| Auth Failure | High | Low | Immediate | Manual fix |
| State Corruption | Medium | Low | Next run | Backup restore |
| Empty List | Low | Low | Validation | User fix |
| WLAN ID Change | Medium | Low | Automatic rediscovery | Self-healing |
| Cron Failure | High | Low | Monitoring | Systemd alternative |
| Web UI Crash | Low | Low | Health check | Service restart |
| Disk Full | High | Low | Monitoring | Log rotation |
| Race Condition | Low | Very Low | Locking | Prevention |
| Firmware Update | Medium | Medium | Status check | Retry later |
| Encoding Issues | Low | Low | Validation | Prevention |

### 1. UniFi API Changes

**How it breaks:**
- Ubiquiti updates the API structure
- Endpoints change paths
- Authentication method changes
- Response format changes

**Symptoms:**
- Login fails with 404 or 401 errors
- WLAN config endpoints return errors
- JSON structure parsing fails

**Mitigation:**

```python
# Add to UniFiAPI class
def check_api_compatibility(self):
    """Check controller version for compatibility"""
    try:
        response = self.session.get(f"{self.base_url}/api/stat/sysinfo", verify=False)
        version = response.json()['data'][0]['version']
        print(f"[{datetime.now()}] Controller version: {version}")
        # Warn if version is much newer than tested
    except Exception as e:
        print(f"[{datetime.now()}] Warning: Could not verify API compatibility: {e}")

# Add more robust error handling
def update_ssid(self, wlan_id, new_ssid):
    url = f"{self.base_url}/api/s/default/rest/wlanconf/{wlan_id}"
    
    try:
        current_config = self.get_wlan_by_id(wlan_id)
        old_name = current_config['name']
        current_config['name'] = new_ssid
        
        response = self.session.put(url, json=current_config, verify=False)
        response.raise_for_status()
        
        print(f"[{datetime.now()}] Updated SSID from '{old_name}' to '{new_ssid}'")
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise Exception("API endpoint not found - controller may have been updated")
        elif e.response.status_code == 401:
            raise Exception("Authentication failed - credentials may be invalid")
        else:
            raise Exception(f"API error: {e}")
```

### 2. Network Connectivity Issues

**How it breaks:**
- UDR is unreachable
- Network timeout
- DNS resolution fails
- SSL/TLS handshake fails

**Symptoms:**
- `Connection refused` errors
- `Timeout` errors
- Script hangs

**Mitigation:**

```python
import time

# Replace login method with retry logic
def login(self, username, password, max_retries=3):
    """Login with retry logic"""
    for attempt in range(max_retries):
        try:
            url = f"{self.base_url}/api/auth/login"
            data = {"username": username, "password": password}
            response = self.session.post(
                url, 
                json=data, 
                verify=False,
                timeout=10  # Add timeout
            )
            response.raise_for_status()
            print(f"[{datetime.now()}] Logged in successfully")
            return True
        except requests.exceptions.Timeout:
            print(f"[{datetime.now()}] Timeout on attempt {attempt + 1}")
            if attempt < max_retries - 1:
                time.sleep(5)
        except requests.exceptions.ConnectionError:
            print(f"[{datetime.now()}] Connection error on attempt {attempt + 1}")
            if attempt < max_retries - 1:
                time.sleep(5)
    raise Exception("Failed to connect after retries")
```

### 3. Authentication Failures

**How it breaks:**
- Password changed on UDR
- Account locked after failed attempts
- Session expires mid-operation
- Account deleted or disabled

**Symptoms:**
- Login returns 401
- Operations fail with "unauthorized"

**Mitigation:**

```python
# Add credential testing
def test_credentials(self):
    """Test if credentials work before doing anything"""
    try:
        test_api = UniFiAPI(
            self.config['unifi_host'],
            self.config['username'],
            self.config['password']
        )
        return True
    except Exception as e:
        print(f"[{datetime.now()}] Credential test failed: {e}")
        # Send alert email/notification here
        return False

# Check in rotate() method before operations
def rotate(self):
    if not self.test_credentials():
        raise Exception("Credentials invalid - check configuration")
    # ... rest of rotation logic
```

### 4. State File Corruption

**How it breaks:**
- JSON file gets corrupted
- Disk full - can't write state
- Permissions issues
- Concurrent writes

**Symptoms:**
- JSON parsing errors
- Rotation resets to index 0
- Script crashes on state load

**Mitigation:**

```python
import shutil

def save_state(self, state):
    """Save with backup and atomic write"""
    temp_file = f"{self.state_file}.tmp"
    backup_file = f"{self.state_file}.backup"
    
    try:
        # Write to temp file first
        with open(temp_file, 'w') as f:
            json.dump(state, f, indent=2)
        
        # Backup old state
        if os.path.exists(self.state_file):
            shutil.copy(self.state_file, backup_file)
        
        # Atomic rename
        os.rename(temp_file, self.state_file)
    except Exception as e:
        print(f"[{datetime.now()}] State save error: {e}")
        # Restore from backup if available
        if os.path.exists(backup_file):
            shutil.copy(backup_file, self.state_file)
            raise

def load_state(self):
    """Load with fallback to backup"""
    try:
        with open(self.state_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"[{datetime.now()}] State file error: {e}")
        # Try backup
        backup_file = f"{self.state_file}.backup"
        if os.path.exists(backup_file):
            print(f"[{datetime.now()}] State corrupted, loading backup")
            with open(backup_file, 'r') as f:
                return json.load(f)
        # Return default state
        print(f"[{datetime.now()}] No backup found, using default state")
        return {"current_index": 0, "wlan_id": None}
```

### 5. Empty SSID List

**How it breaks:**
- User deletes all SSIDs from web interface
- JSON file edited incorrectly
- List becomes empty during editing

**Symptoms:**
- Division by zero error on modulo operation
- IndexError on list access

**Mitigation:**

```python
def load_ssid_list(self):
    """Load SSID list from JSON file with validation"""
    if not os.path.exists(self.ssid_list_file):
        raise Exception(f"SSID list file not found: {self.ssid_list_file}")
    
    with open(self.ssid_list_file, 'r') as f:
        data = json.load(f)
    
    self.ssid_list = data.get('ssids', [])
    self.protected_ssids = data.get('protected_ssids', [])
    
    # Validation
    if not self.ssid_list:
        raise Exception("SSID list is empty - add SSIDs before rotating")
    
    if len(self.ssid_list) < 2:
        print(f"[{datetime.now()}] Warning: Only 1 SSID in list - rotation will have no effect")
    
    # Check for duplicates
    if len(self.ssid_list) != len(set(self.ssid_list)):
        print(f"[{datetime.now()}] Warning: Duplicate SSIDs in list")
    
    print(f"[{datetime.now()}] Loaded {len(self.ssid_list)} SSIDs from configuration")
    print(f"[{datetime.now()}] Protected SSIDs: {', '.join(self.protected_ssids)}")
```

### 6. WLAN ID Changes

**How it breaks:**
- WLAN deleted and recreated in UniFi UI
- Multiple WLANs with same name
- WLAN ID no longer exists

**Symptoms:**
- 404 when trying to update WLAN
- Updates wrong SSID

**Mitigation:**

```python
def validate_wlan_id(self, api, wlan_id):
    """Check WLAN still exists and rediscover if needed"""
    try:
        wlan = api.get_wlan_by_id(wlan_id)
        return wlan_id
    except Exception as e:
        print(f"[{datetime.now()}] WLAN ID {wlan_id} no longer exists - rediscovering")
        # Force rediscovery
        new_wlan_id = self.discover_wlan_id(api)
        
        # Update state with new WLAN ID
        state = self.load_state()
        state['wlan_id'] = new_wlan_id
        self.save_state(state)
        
        return new_wlan_id

# Use in rotate() method
if state.get('wlan_id') is None:
    state['wlan_id'] = self.discover_wlan_id(api)
else:
    # Validate existing WLAN ID
    state['wlan_id'] = self.validate_wlan_id(api, state['wlan_id'])
```

### 7. Cron Job Failures

**How it breaks:**
- Cron daemon not running
- Wrong user context
- Environment variables missing
- Path issues

**Symptoms:**
- Script never runs
- Runs but can't find files/modules
- No log output

**Mitigation:**

```bash
# Better cron entry with full paths and error notification
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin
MAILTO=admin@example.com

0 */18 * * * /usr/bin/python3 ~/ssid_rotator/src/rotate_ssid.py >> /var/log/ssid-rotator.log 2>&1 || echo "SSID rotation failed at $(date)" >> /var/log/ssid-rotator-errors.log

# Create health check script
# ~/ssid_rotator/health_check.sh
#!/bin/bash
STATE_FILE="/var/lib/ssid_rotator/state.json"

if [ ! -f "$STATE_FILE" ]; then
    echo "State file missing" | mail -s "SSID Rotator Alert" admin@example.com
    exit 1
fi

LAST_RUN=$(stat -c %Y "$STATE_FILE")
NOW=$(date +%s)
DIFF=$((NOW - LAST_RUN))

# Alert if no rotation in 20 hours (should run every 18)
if [ $DIFF -gt 72000 ]; then
    HOURS=$((DIFF/3600))
    echo "SSID rotator hasn't run in $HOURS hours" | mail -s "SSID Rotator Alert" admin@example.com
fi

# Add to crontab for daily health check
# 0 10 * * * ~/ssid_rotator/health_check.sh
```

### 8. Web Interface Issues

**How it breaks:**
- Flask crashes
- Port already in use
- File permission errors
- Database lock on JSON file

**Symptoms:**
- Web interface not accessible
- Changes don't save
- 500 errors

**Mitigation:**

```python
import fcntl

def save_ssid_data(data):
    """Thread-safe save with file locking"""
    lockfile = "/var/lib/ssid_rotator/.lock"
    
    # Ensure lock directory exists
    os.makedirs(os.path.dirname(lockfile), exist_ok=True)
    
    with open(lockfile, 'w') as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            data['last_updated'] = datetime.now().isoformat()
            
            # Atomic write
            temp_file = f"{CONFIG['ssid_list_file']}.tmp"
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            os.rename(temp_file, CONFIG['ssid_list_file'])
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

# Better Flask error handling
@app.errorhandler(Exception)
def handle_error(e):
    app.logger.error(f"Error: {e}")
    return jsonify({
        'success': False, 
        'error': str(e)
    }), 500

# Health check endpoint
@app.route('/health')
def health():
    try:
        # Check if files exist and are readable
        data = load_ssid_data()
        state = load_state()
        return jsonify({
            'status': 'ok',
            'ssid_count': len(data.get('ssids', [])),
            'last_rotation': state.get('last_rotation') if state else None
        })
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'message': str(e)
        }), 500

# Add to systemd service file to auto-restart on failure
[Service]
Restart=always
RestartSec=10
```

### 9. Disk Space Issues

**How it breaks:**
- Logs grow too large
- No space for state files
- Backup files fill disk

**Symptoms:**
- Can't write state
- Rotation fails
- System becomes unstable

**Mitigation:**

```python
import shutil

def check_disk_space(path="/var/lib/ssid_rotator", min_mb=10):
    """Check if enough disk space available"""
    stat = shutil.disk_usage(path)
    free_mb = stat.free / (1024 * 1024)
    
    if free_mb < min_mb:
        raise Exception(f"Low disk space: {free_mb:.2f}MB remaining (need {min_mb}MB)")
    
    if free_mb < 50:
        print(f"[{datetime.now()}] Warning: Low disk space: {free_mb:.2f}MB remaining")
    
    return True

# Add to rotate() method
def rotate(self):
    # Check disk space before operations
    self.check_disk_space()
    # ... rest of rotation logic
```

Better log rotation:

```bash
# /etc/logrotate.d/ssid-rotator
/var/log/ssid-rotator.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    maxsize 10M
    create 0644 username username
    postrotate
        systemctl reload ssid-web-manager > /dev/null 2>&1 || true
    endscript
}
```

### 10. Race Conditions

**How it breaks:**
- Web UI updates list while rotation script runs
- Multiple cron jobs overlap
- Concurrent API calls

**Symptoms:**
- Inconsistent state
- Wrong SSID applied
- Partial updates

**Mitigation:**

```python
import fcntl
import atexit

class ProcessLock:
    """Prevent multiple instances from running simultaneously"""
    def __init__(self, lockfile="/var/run/ssid-rotator.pid"):
        self.lockfile = lockfile
        self.lock_fd = None
    
    def acquire(self):
        """Acquire exclusive lock"""
        try:
            self.lock_fd = open(self.lockfile, 'w')
            fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.lock_fd.write(str(os.getpid()))
            self.lock_fd.flush()
            return True
        except IOError:
            # Another instance is running
            if self.lock_fd:
                self.lock_fd.close()
            return False
    
    def release(self):
        """Release lock"""
        if self.lock_fd:
            try:
                fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_UN)
                self.lock_fd.close()
            except:
                pass
            try:
                if os.path.exists(self.lockfile):
                    os.remove(self.lockfile)
            except:
                pass

# Use in main()
def main():
    print(f"[{datetime.now()}] Starting SSID rotator...")
    
    # Acquire process lock
    lock = ProcessLock()
    if not lock.acquire():
        print(f"[{datetime.now()}] Another instance is already running. Exiting.")
        sys.exit(0)
    
    # Ensure lock is released on exit
    atexit.register(lock.release)
    
    try:
        rotator = SSIDRotator(CONFIG)
        rotator.rotate()
    except Exception as e:
        print(f"[{datetime.now()}] ERROR: {e}")
        raise
    finally:
        lock.release()
```

### 11. UDR Firmware Updates

**How it breaks:**
- Update changes API behavior
- Controller restarts during rotation
- New authentication requirements

**Symptoms:**
- Sudden API failures
- Authentication changes
- Different response formats

**Mitigation:**

```python
def check_system_status(self):
    """Check if controller is in a usable state"""
    try:
        response = self.session.get(
            f"{self.base_url}/api/stat/sysinfo", 
            verify=False,
            timeout=5
        )
        data = response.json()['data'][0]
        
        if data.get('state') == 'upgrading':
            raise Exception("Controller is upgrading - will retry later")
        
        if data.get('update_available'):
            print(f"[{datetime.now()}] Info: Update available for controller")
        
        return True
    except Exception as e:
        print(f"[{datetime.now()}] Warning: Could not check system status: {e}")
        return False

# Add to rotate() method before operations
api = UniFiAPI(...)
if not api.check_system_status():
    print(f"[{datetime.now()}] Controller not ready, skipping rotation")
    sys.exit(0)
```

### 12. Character Encoding Issues

**How it breaks:**
- Emoji or special characters in SSID
- Unicode handling problems
- JSON encoding errors

**Symptoms:**
- SSIDs display incorrectly
- JSON parse errors
- API rejects SSID

**Mitigation:**

```python
def validate_ssid(ssid):
    """Check SSID meets requirements"""
    if not ssid or not isinstance(ssid, str):
        raise ValueError("SSID must be a non-empty string")
    
    # Strip whitespace
    ssid = ssid.strip()
    
    if len(ssid) > 32:
        raise ValueError("SSID too long (max 32 characters)")
    
    if len(ssid) == 0:
        raise ValueError("SSID cannot be empty")
    
    # Check for problematic characters
    # UniFi generally supports UTF-8 but some client devices don't
    try:
        ssid.encode('utf-8')
    except UnicodeEncodeError:
        raise ValueError("SSID contains invalid characters")
    
    # Warn about potential compatibility issues
    if any(ord(c) > 127 for c in ssid):
        print(f"[{datetime.now()}] Warning: SSID '{ssid}' contains non-ASCII characters which may cause issues with some devices")
    
    return ssid

# Use in web interface
@app.route('/api/add', methods=['POST'])
def add_ssid():
    req_data = request.json
    ssid = req_data.get('ssid', '').strip()
    is_protected = req_data.get('protected', False)
    
    try:
        ssid = validate_ssid(ssid)
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)})
    
    # ... rest of add logic
```

### Monitoring & Health Check Script

Create a comprehensive monitoring script to detect issues:

```python
#!/usr/bin/env python3
# ~/ssid_rotator/monitor.py

import json
import os
import sys
from datetime import datetime, timedelta
import requests

def check_rotation_health():
    """Comprehensive health check for SSID rotator"""
    issues = []
    warnings = []
    
    # Check state file age
    state_file = "/var/lib/ssid_rotator/state.json"
    if os.path.exists(state_file):
        age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(state_file))
        if age > timedelta(hours=20):  # Should rotate every 18 hours
            issues.append(f"State file not updated in {age.total_seconds()/3600:.1f} hours")
        elif age > timedelta(hours=19):
            warnings.append(f"State file age is {age.total_seconds()/3600:.1f} hours")
    else:
        issues.append("State file does not exist")
    
    # Check SSID list file
    ssid_list_file = "/var/lib/ssid_rotator/ssid_list.json"
    if os.path.exists(ssid_list_file):
        try:
            with open(ssid_list_file, 'r') as f:
                data = json.load(f)
                if not data.get('ssids'):
                    issues.append("SSID list is empty")
                elif len(data.get('ssids', [])) < 2:
                    warnings.append("Only 1 SSID in rotation list")
        except json.JSONDecodeError:
            issues.append("SSID list file is corrupted")
    else:
        issues.append("SSID list file does not exist")
    
    # Check log for recent errors
    log_file = "/var/log/ssid-rotator.log"
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r') as f:
                recent = f.readlines()[-100:]  # Last 100 lines
                error_count = sum(1 for line in recent if 'ERROR' in line or 'FAILED' in line)
                if error_count > 5:
                    issues.append(f"{error_count} errors in recent logs")
                elif error_count > 0:
                    warnings.append(f"{error_count} errors in recent logs")
        except:
            warnings.append("Could not read log file")
    
    # Check disk space
    try:
        import shutil
        stat = shutil.disk_usage("/var/lib/ssid_rotator")
        free_mb = stat.free / (1024 * 1024)
        if free_mb < 10:
            issues.append(f"Critical: Low disk space: {free_mb:.1f}MB")
        elif free_mb < 50:
            warnings.append(f"Low disk space: {free_mb:.1f}MB")
    except:
        warnings.append("Could not check disk space")
    
    # Check web service health
    try:
        r = requests.get("http://192.168.102.205:5000/health", timeout=5)
        if r.status_code != 200:
            issues.append("Web interface health check failed")
        else:
            health_data = r.json()
            if health_data.get('status') != 'ok':
                issues.append(f"Web interface reports: {health_data.get('message', 'unknown error')}")
    except requests.exceptions.ConnectionError:
        issues.append("Web interface not responding")
    except Exception as e:
        warnings.append(f"Could not check web interface: {e}")
    
    # Check for stale PID file
    pid_file = "/var/run/ssid-rotator.pid"
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            # Check if process is actually running
            try:
                os.kill(pid, 0)  # Signal 0 doesn't kill, just checks
                warnings.append(f"Rotation process may be stuck (PID {pid})")
            except OSError:
                # Process not running, remove stale PID file
                os.remove(pid_file)
        except:
            pass
    
    # Report results
    print(f"[{datetime.now()}] Health Check Results:")
    
    if issues:
        print(f"[{datetime.now()}] CRITICAL ISSUES:")
        for issue in issues:
            print(f"  - {issue}")
        send_alert("CRITICAL", issues)
        return False
    
    if warnings:
        print(f"[{datetime.now()}] Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
        send_alert("WARNING", warnings)
    
    if not issues and not warnings:
        print(f"[{datetime.now()}] All checks passed ✓")
    
    return len(issues) == 0

def send_alert(level, messages):
    """Send alert notification"""
    # Implement your notification method here
    # Examples: email, webhook, SMS, Slack, Discord, etc.
    
    # Simple email example:
    # import smtplib
    # from email.message import EmailMessage
    # msg = EmailMessage()
    # msg['Subject'] = f'SSID Rotator {level}'
    # msg['From'] = 'ssid-rotator@example.com'
    # msg['To'] = 'admin@example.com'
    # msg.set_content('\n'.join(messages))
    # with smtplib.SMTP('localhost') as s:
    #     s.send_message(msg)
    
    # For now, just log
    print(f"[{datetime.now()}] ALERT ({level}): {messages}")

if __name__ == "__main__":
    try:
        success = check_rotation_health()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"[{datetime.now()}] Health check script failed: {e}")
        sys.exit(2)
```

Make it executable and add to crontab:

```bash
chmod +x ~/ssid_rotator/monitor.py

# Add to crontab for daily health checks
crontab -e

# Add:
0 9 * * * /usr/bin/python3 ~/ssid_rotator/monitor.py >> /var/log/ssid-rotator-health.log 2>&1
```

### Best Practices for Reliability

1. **Always use timeouts** on network operations
2. **Implement retry logic** for transient failures
3. **Use atomic file operations** (write to temp, then rename)
4. **Create backups** before modifying files
5. **Validate input** before processing
6. **Use file locking** to prevent concurrent access
7. **Monitor regularly** with automated health checks
8. **Log comprehensively** with timestamps and context
9. **Test recovery procedures** before problems occur
10. **Document error codes** and their meanings

### Recovery Procedures

**If rotation stops working:**

1. Check logs: `tail -100 /var/log/ssid-rotator.log`
2. Test credentials manually: Try logging into UniFi UI at https://192.168.102.1
3. Check state file: `cat /var/lib/ssid_rotator/state.json`
4. Verify SSID list: `cat /var/lib/ssid_rotator/ssid_list.json`
5. Check active rotation has SSIDs: Look for `"active_rotation": [...]`
6. Test connectivity: `curl -k https://192.168.102.1`
7. Check disk space: `df -h /var/lib/ssid_rotator`
8. Verify cron is running: `systemctl status cron`
9. Check for process lock: `ls -la /var/run/ssid-rotator.pid`

**Emergency manual rotation:**

```bash
# Force rotation immediately
python3 ~/ssid_rotator/src/rotate_ssid.py

# Reset state to start from beginning
echo '{"current_index": 0, "wlan_id": null}' > /var/lib/ssid_rotator/state.json

# Skip to specific SSID (if you know the index)
echo '{"current_index": 3, "wlan_id": "your-wlan-id"}' > /var/lib/ssid_rotator/state.json
```

---

## Credits

Created for managing funny WiFi SSID rotations on UniFi networks. Perfect for entertaining your neighbors and keeping things fresh!
