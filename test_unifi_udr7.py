#!/usr/bin/env python3
"""
UniFi UDR7 API Test Script
Tests connectivity, authentication, and SSID listing
Configured for UDR7 at 192.168.102.1
"""

import requests
import urllib3
import json

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================
# CONFIGURATION - UPDATE PASSWORD IF NEEDED
# ============================================
UDR_HOST = "192.168.102.1"
USERNAME = "admin"
PASSWORD = "C0,5prings@@@"  # Your actual password
# UDR7 requires /proxy/network prefix
BASE_URL = f"https://{UDR_HOST}/proxy/network"

def test_connection():
    """Run comprehensive API tests"""
    print("=" * 50)
    print("UniFi UDR7 API Connection Test")
    print("=" * 50)
    print()
    
    # Test 1: Connectivity
    print("Test 1: Checking connectivity...")
    try:
        requests.get(f"https://{UDR_HOST}", verify=False, timeout=5)
        print("   ✓ Router is reachable")
        print()
    except Exception as e:
        print(f"   ✗ Cannot reach router: {e}")
        print()
        return False
    
    # Test 2: Login
    print("Test 2: Testing authentication...")
    session = requests.Session()
    try:
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": USERNAME, "password": PASSWORD},
            verify=False,
            timeout=10
        )
        if response.status_code == 200:
            print("   ✓ Login successful")
            print()
        else:
            print(f"   ✗ Login failed (HTTP {response.status_code})")
            print(f"   Response: {response.text}")
            print()
            return False
    except Exception as e:
        print(f"   ✗ Login error: {e}")
        print()
        return False
    
    # Test 3: List SSIDs
    print("Test 3: Fetching WiFi networks...")
    try:
        response = session.get(
            f"{BASE_URL}/api/s/default/rest/wlanconf",
            verify=False,
            timeout=10
        )
        data = response.json()
        
        if data['meta']['rc'] == 'ok':
            print(f"   ✓ Successfully retrieved {len(data['data'])} WiFi networks")
            print()
            print("WiFi Networks Found:")
            print("-" * 50)
            
            # Highlight the rotation target
            target_id = "69363fd4005cd02fa28ab902"
            
            for i, wlan in enumerate(data['data'], 1):
                status = "✓ Enabled" if wlan.get('enabled') else "✗ Disabled"
                is_target = wlan['_id'] == target_id
                
                if is_target:
                    print(f"\n>>> TARGET FOR ROTATION <<<")
                
                print(f"\n{i}. {wlan['name']}")
                print(f"   Status: {status}")
                print(f"   ID: {wlan['_id']}")
                print(f"   Security: {wlan.get('security', 'N/A')}")
                print(f"   Hidden: {'Yes' if wlan.get('hide_ssid') else 'No'}")
                
                if is_target:
                    print(f"   >>> THIS SSID WILL BE ROTATED <<<")
            
            print()
        else:
            print("   ✗ API returned error")
            print(f"   Response: {json.dumps(data, indent=2)}")
            return False
            
    except Exception as e:
        print(f"   ✗ Error fetching SSIDs: {e}")
        print()
        return False
    
    # Test 4: Get System Info
    print("Test 4: Fetching system information...")
    try:
        response = session.get(
            f"{BASE_URL}/api/s/default/stat/sysinfo",
            verify=False,
            timeout=10
        )
        data = response.json()
        
        if data['meta']['rc'] == 'ok':
            sysinfo = data['data'][0]
            print(f"   ✓ Controller Version: {sysinfo.get('version', 'N/A')}")
            print(f"   ✓ Hostname: {sysinfo.get('hostname', 'N/A')}")
            print(f"   ✓ Uptime: {sysinfo.get('uptime', 0) / 3600:.1f} hours")
            print()
        
    except Exception as e:
        print(f"   ⚠ Could not fetch system info: {e}")
        print()
    
    print("=" * 50)
    print("All Tests Passed! ✓")
    print("=" * 50)
    print()
    print("Protected SSIDs (will NOT be modified):")
    print("  - 7Oaks")
    print("  - 7Oaks-IOT")
    print("  - newnative")
    print("  - 7Oaks-Work")
    print()
    print("Target SSID (will be rotated):")
    print("  - Fuck the orange turd (ID: 69363fd4005cd02fa28ab902)")
    print()
    return True

if __name__ == "__main__":
    success = test_connection()
    exit(0 if success else 1)
