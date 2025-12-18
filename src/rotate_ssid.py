#!/usr/bin/env python3
import requests
import urllib3
import json
import os
from datetime import datetime
from ssid_validator import validate_ssid, validate_ssid_list, get_ssid_byte_length

# Disable SSL warnings for self-signed cert
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
CONFIG = {
    "unifi_host": "192.168.102.1",  # Your UDR IP
    "username": "admin",
    "password": "C0,5prings@@@",  # Your actual admin password
    "current_ssid_name": "Fuck the orange turd",  # Initial SSID name to find
    "target_wlan_id": "69363fd4005cd02fa28ab902",  # The WLAN ID to rotate (optional, will auto-discover if not set)
    "state_file": "/var/lib/ssid_rotator/state.json",
    "ssid_list_file": "/var/lib/ssid_rotator/ssid_list.json"
}

class UniFiAPI:
    def __init__(self, host, username, password):
        self.host = host
        # UDR7 uses different endpoints for OS vs Network Controller
        self.os_url = f"https://{host}"  # UniFi OS API (for login)
        self.network_url = f"https://{host}/proxy/network"  # Network Controller API (for WLAN operations)
        self.session = requests.Session()
        self.csrf_token = None
        self.login(username, password)
    
    def login(self, username, password):
        # Login uses UniFi OS API (no /proxy/network prefix)
        url = f"{self.os_url}/api/auth/login"
        data = {"username": username, "password": password}
        response = self.session.post(url, json=data, verify=False)
        response.raise_for_status()
        
        # Extract CSRF token from response headers (required for write operations)
        self.csrf_token = response.headers.get('X-Csrf-Token') or response.headers.get('x-csrf-token')
        if self.csrf_token:
            print(f"[{datetime.now()}] Logged in successfully (CSRF token acquired)")
        else:
            print(f"[{datetime.now()}] Logged in successfully (no CSRF token found)")
    
    def get_wlan_configs(self):
        # WLAN operations use Network Controller API (with /proxy/network prefix)
        url = f"{self.network_url}/api/s/default/rest/wlanconf"
        response = self.session.get(url, verify=False)
        return response.json()['data']
    
    def get_wlan_by_id(self, wlan_id):
        url = f"{self.network_url}/api/s/default/rest/wlanconf/{wlan_id}"
        response = self.session.get(url, verify=False)
        return response.json()['data'][0]
    
    def get_wlan_by_name(self, ssid_name):
        wlans = self.get_wlan_configs()
        for wlan in wlans:
            if wlan.get('name') == ssid_name:
                return wlan
        return None
    
    def update_ssid(self, wlan_id, new_ssid):
        url = f"{self.network_url}/api/s/default/rest/wlanconf/{wlan_id}"
        
        # Get current config
        current_config = self.get_wlan_by_id(wlan_id)
        
        # Update the SSID name
        old_name = current_config['name']
        current_config['name'] = new_ssid
        
        # Prepare headers with CSRF token (required for write operations)
        headers = {}
        if self.csrf_token:
            headers['X-Csrf-Token'] = self.csrf_token
        
        # Send the update
        response = self.session.put(url, json=current_config, headers=headers, verify=False)
        response.raise_for_status()
        
        # Verify the change actually took effect (atomicity check)
        import time
        time.sleep(1)  # Brief delay to allow UniFi to apply change
        updated_wlan = self.get_wlan_by_id(wlan_id)
        if updated_wlan['name'] != new_ssid:
            raise Exception(
                f"SSID update verification failed: expected '{new_ssid}', "
                f"but UniFi shows '{updated_wlan['name']}'"
            )
        
        print(f"[{datetime.now()}] Updated SSID from '{old_name}' to '{new_ssid}' (verified)")
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

        # Basic validation
        if not self.ssid_list:
            raise Exception("Active rotation list is empty - add SSIDs before rotating")

        if len(self.ssid_list) < 2:
            print(f"[{datetime.now()}] Warning: Only 1 SSID in active rotation - rotation will have no effect")

        # Check for duplicates in active rotation
        if len(self.ssid_list) != len(set(self.ssid_list)):
            print(f"[{datetime.now()}] Warning: Duplicate SSIDs in active rotation")

        # SSID name validation - check all lists
        validation_errors = []

        # Validate active rotation SSIDs
        all_valid, errors = validate_ssid_list(self.ssid_list, "Active rotation", strict=True)
        if not all_valid:
            validation_errors.extend(errors)

        # Validate reserve pool SSIDs
        all_valid, errors = validate_ssid_list(self.reserve_pool, "Reserve pool", strict=True)
        if not all_valid:
            validation_errors.extend(errors)

        # Validate protected SSIDs (less strict since we don't control them)
        all_valid, errors = validate_ssid_list(self.protected_ssids, "Protected SSIDs", strict=False)
        if not all_valid:
            validation_errors.extend(errors)

        # If there are validation errors, log them and raise exception
        if validation_errors:
            print(f"[{datetime.now()}] SSID VALIDATION ERRORS:")
            for error in validation_errors:
                print(f"[{datetime.now()}]   - {error}")
            raise Exception(
                f"SSID validation failed with {len(validation_errors)} error(s). "
                f"Please fix invalid SSID names in {self.ssid_list_file}. "
                f"See log for details."
            )

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
