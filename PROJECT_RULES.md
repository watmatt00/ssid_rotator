# SSID Rotation Project - Canon Rules

**Project Name:** UniFi SSID Rotator  
**Created:** December 16, 2024  
**Status:** Planning/Implementation Phase  
**Target Deployment:** Week of December 23, 2024  

---

## Hardware Configuration

### Network Equipment
- **Router:** UniFi Dream Router (UDR) Pro 7
- **Router IP:** `192.168.102.1`
- **Network Subnet:** `192.168.102.0/24`

### Host System
- **Device:** Raspberry Pi Zero W (version 1.1)
- **OS:** Raspberry Pi OS Lite (64-bit recommended, 32-bit acceptable)
- **Access:** Headless via SSH
- **Power:** 5V 2A+ USB power supply
- **Network:** WiFi (2.4GHz only) or USB Ethernet adapter
- **Hostname:** `rotator`
- **Username:** `pi`
- **Password:** `rotator`
- **IP Address:** `192.168.102.205` (static)
- **DNS Name:** `rotator.local`

---

## UniFi API Configuration

### API Endpoints
**CRITICAL:** UDR7 requires `/proxy/network` prefix for all network controller API calls.

**Base URL Pattern:**
```
https://192.168.102.1/proxy/network/api/...
```

**Key Endpoints:**
- **Login:** `https://192.168.102.1/proxy/network/api/auth/login`
- **List WLANs:** `https://192.168.102.1/proxy/network/api/s/default/rest/wlanconf`
- **Get WLAN by ID:** `https://192.168.102.1/proxy/network/api/s/default/rest/wlanconf/{wlan_id}`
- **Update WLAN:** `https://192.168.102.1/proxy/network/api/s/default/rest/wlanconf/{wlan_id}` (PUT)

### Authentication
- **Method:** Cookie-based session (TOKEN)
- **Username:** `admin`
- **Password:** `C0,5prings@@@`
- **Session Duration:** ~2 hours
- **Verification:** Self-signed SSL certificate (use `verify=False` in Python)

---

## Network Configuration

### Protected SSIDs (NEVER MODIFY)
These are production networks that must NEVER be touched by the rotation script:

1. **7Oaks**
   - ID: `692e47980f81923534aec614`
   - Type: Main network (5GHz, hidden)
   - Security: WPA2

2. **7Oaks-IOT**
   - ID: `692e4c4b0f81923534aec68a`
   - Type: IoT network (2.4GHz, hidden)
   - Security: WPA2
   - L2 Isolation: Enabled

3. **newnative**
   - ID: `692e4dc40f81923534aec6d4`
   - Type: Secondary network (5GHz, hidden)
   - Security: WPA2

4. **7Oaks-Work**
   - ID: `6935e0c5005cd02fa28aa8bf`
   - Type: Work network (both bands, hidden)
   - Security: WPA2

### Target SSID (ROTATION ENABLED)
**Name:** "Fuck the orange turd"  
**WLAN ID:** `69363fd4005cd02fa28ab902`  
**Type:** Visible network (2.4GHz, open)  
**Security:** Open (no password)  
**Purpose:** Entertainment/political commentary  
**Visibility:** Broadcast (hidden = false)  
**L2 Isolation:** False  
**AP Group:** `6940ace3f338a319aab4b25b` (specific group)  

---

## Rotation System Architecture

### Two-Stage List System
The system uses a two-stage approach for managing SSID names:

#### Active Rotation List
- **Size:** 5-7 SSIDs recommended
- **Purpose:** SSIDs currently in rotation
- **Cycle Time:** 
  - 5 SSIDs × 18 hours = 3.75 days per full cycle
  - 7 SSIDs × 18 hours = 5.25 days per full cycle

#### Reserve Pool
- **Size:** 5-15 SSIDs recommended
- **Purpose:** Storage for SSIDs not currently rotating
- **Management:** Web UI for promoting/demoting between active and reserve

#### Protected List
- **Size:** 4 networks (listed above)
- **Purpose:** Production networks that will never be modified
- **Enforcement:** Multiple safety checks in code

### Rotation Timing
- **Interval:** 18 hours (FIXED, NON-NEGOTIABLE)
- **Method:** Cron job or systemd timer
- **Schedule:** `0 */18 * * *` (every 18 hours at :00 minutes)
- **Pattern:** Sequential (in-line) rotation through active list

### File Locations
```
/opt/ssid-rotator/
├── rotate_ssid.py          # Main rotation script
└── web_manager.py          # Flask web interface

/var/lib/ssid_rotator/
├── ssid_list.json          # Active, reserve, and protected lists
├── ssid_list.json.backup   # Automatic backup
└── state.json              # Current rotation state
└── state.json.backup       # Automatic backup

/var/log/
└── ssid-rotator.log        # Rotation activity log

/var/run/
└── ssid-rotator.pid        # Process lock file
```

---

## Technical Requirements

### Python Dependencies
```
flask
requests
urllib3
```

**Installation:**
```bash
pip3 install flask requests --break-system-packages
```

### System Requirements
- **Python:** 3.7+
- **Disk Space:** ~200MB for OS + Python + scripts + logs
- **RAM:** ~150MB total usage
- **Network:** Reliable connection to 192.168.102.1

### Port Usage
- **Web Interface:** Port 5000 (HTTP)
- **API Calls:** Port 443 (HTTPS to router)

---

## Safety & Reliability

### Safety Mechanisms
1. **Protected SSID Validation:** Script refuses to run if target WLAN ID matches any protected network
2. **State File Backups:** Atomic writes with backup files
3. **Process Locking:** Prevents multiple concurrent rotations
4. **WLAN ID Verification:** Validates target still exists before every rotation
5. **List Overlap Detection:** Prevents SSIDs from being in both active and protected lists

### Error Handling
- API connection retries (up to 3 attempts)
- Timeout protection (10 second max per API call)
- State file corruption recovery (fallback to backup)
- Graceful degradation on errors

### Monitoring
- Log rotation (weekly, keep 4 weeks)
- Health check script (optional, runs daily)
- State file timestamp checking

---

## Constraints & Rules

### Non-Negotiable Requirements
1. ✅ **18-hour rotation interval** - Must not change
2. ✅ **4 Protected SSIDs** - Must never be modified under any circumstances
3. ✅ **Sequential rotation** - Predictable order through active list
4. ✅ **UDR7 API paths** - Must use `/proxy/network` prefix
5. ✅ **Raspberry Pi Zero W** - Target hardware platform

### Flexible Parameters
- Number of SSIDs in active rotation (5-7 recommended)
- Number of SSIDs in reserve pool (no hard limit)
- SSID naming (user's choice)
- Log retention period
- Web interface port (5000 default, changeable)

### Prohibited Actions
- ❌ Never modify any of the 4 protected SSIDs
- ❌ Never use rotation interval shorter than 18 hours
- ❌ Never hardcode passwords in non-config files
- ❌ Never disable safety checks
- ❌ Never run multiple rotation instances simultaneously

---

## Implementation Phases

### Phase 1: Testing (Current)
- ✅ API connectivity verified
- ✅ WLAN listing working
- ✅ Target SSID identified
- ✅ Protected SSIDs documented
- 🔲 Test manual SSID update via API

### Phase 2: Deployment (Week of Dec 23)
1. Set up Raspberry Pi Zero W
2. Install dependencies
3. Deploy rotation script
4. Deploy web interface
5. Test manual rotation
6. Configure cron job
7. Monitor first 3 rotations

### Phase 3: Production (Ongoing)
- Monitor logs weekly
- Backup state files monthly
- Update SSID lists as desired via web UI
- Seasonal SSID themes (holidays, events)

---

## Future Enhancements (Documented, Not Implemented)

### Rotation Strategies (Optional)
These are documented but NOT implemented in the initial version:
- Random rotation (vs. sequential)
- Weighted rotation (favorites appear more often)
- Time-based rotation (different SSIDs by time of day)
- Shuffle rotation (no repeats until all shown)

### Additional Features (Optional)
- Email/webhook notifications on rotation
- Statistics tracking (which SSIDs shown when)
- Web UI for viewing rotation history
- API endpoint for external control
- Multiple rotating SSIDs (currently only supports one)

---

## Network Topology

```
Internet
    ↓
UniFi Dream Router Pro 7 (192.168.102.1)
    ├── 7Oaks (5GHz, hidden) [PROTECTED]
    ├── 7Oaks-IOT (2.4GHz, hidden) [PROTECTED]
    ├── newnative (5GHz, hidden) [PROTECTED]
    ├── 7Oaks-Work (both bands, hidden) [PROTECTED]
    └── Fuck the orange turd (2.4GHz, visible) [ROTATING]
             ↑
             Managed by
             ↓
    Raspberry Pi Zero W (192.168.102.205)
         ├── Hostname: rotator / rotator.local
         ├── Username: pi
         ├── Running: rotate_ssid.py (cron)
         └── Running: web_manager.py (systemd)
```

---

## Raspberry Pi Zero W Considerations

### Known Limitations
- **Single-core CPU:** Slower than Pi Zero 2 W, but adequate for this task
- **512MB RAM:** Sufficient for OS + Python + Flask
- **2.4GHz WiFi only:** No 5GHz support
- **No Ethernet:** Requires USB adapter for wired connection

### Reliability Measures
1. **Use quality SD card** (SanDisk, Samsung)
2. **Enable log2ram** to reduce SD card writes (optional)
3. **Static IP or .local hostname** for easy SSH access
4. **Watchdog timer** for auto-recovery if system hangs (optional)
5. **Weekly backups** of state files to separate system

### Performance Expectations
- **Rotation time:** ~2-3 seconds per execution
- **Web UI response:** ~500ms for page load
- **CPU usage:** <1% idle, ~20% during rotation
- **Network latency:** <10ms to router on local network

---

## Contact Information

**Project Owner:** Matt  
**Email:** watmatt@txphipps.com  
**Network Location:** Colorado Springs, Colorado, US  
**Time Zone:** MST (UTC-7)  

---

## Change Log

### v1.1 - December 16, 2024
- Raspberry Pi host configuration documented
  - Hostname: rotator (rotator.local)
  - IP: 192.168.102.205
  - Credentials: pi / rotator

### v1.0 - December 16, 2024
- Initial project rules document created
- API endpoints verified and documented
- Protected networks identified
- Target SSID confirmed
- Hardware platform specified (Raspberry Pi Zero W 1.1)
- Two-stage list architecture defined

---

## References

- **Primary Documentation:** `ssid-rotator-guide.md`
- **Test Script:** `test_unifi_udr7.py`
- **UniFi API Documentation:** https://ubntwiki.com/products/software/unifi-controller/api
- **UDR7 Product Page:** https://store.ui.com/us/en/category/cloud-gateways-dream-router

---

**Last Updated:** December 16, 2024  
**Document Version:** 1.1  
**Status:** Canonical - All information in this document is authoritative for the project
