# UniFi SSID Rotator

Automatically rotate a WiFi SSID through a list of funny names every 18 hours on your UniFi network. Perfect for entertaining neighbors while keeping your production networks completely protected.

## Features

- 🔄 **Automatic rotation** every 18 hours
- 🌐 **Web interface** for easy SSID management
- 🔒 **Protected networks** - production SSIDs are never modified
- 📊 **Two-stage lists** - active rotation + reserve pool for better control
- ✅ **Multiple safety checks** prevent accidental modifications
- 🛡️ **State backups** with atomic file operations
- 📝 **Comprehensive logging** for monitoring and debugging

## Quick Start

### Requirements

- UniFi Dream Router (UDR) Pro 7 or compatible UniFi controller
- Raspberry Pi (Zero W or better) or any Linux machine
- Python 3.7+
- Network access to your UniFi controller

### Installation

```bash
# Clone the repository
git clone https://github.com/watmatt00/ssid_rotator.git
cd ssid_rotator

# Install dependencies
pip3 install flask requests --break-system-packages

# Follow the detailed setup in ssid-rotator-guide.md
```

### Configuration

See [`PROJECT_RULES.md`](PROJECT_RULES.md) for complete configuration details including:
- UniFi API endpoints (UDR7 requires `/proxy/network` prefix)
- Protected SSID configuration
- Target SSID setup
- Hardware specifications

## Documentation

- **[Complete Setup Guide](ssid-rotator-guide.md)** - Step-by-step installation and configuration
- **[Project Rules](PROJECT_RULES.md)** - Technical specifications, constraints, and architecture
- **[Test Script](test_unifi_udr7.py)** - API connectivity verification

## How It Works

```
┌─────────────────────┐
│  Web Interface      │  ← Manage SSID lists via browser
│  (Flask App)        │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│  ssid_list.json     │  ← Active rotation + reserve pool
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

## Two-Stage List System

### Active Rotation (5-7 SSIDs)
- Currently rotating names
- Fast cycle time (3.75-5.25 days)
- What your neighbors see

### Reserve Pool (unlimited)
- Storage for SSIDs not currently active
- Easy promotion/demotion via web UI
- Perfect for seasonal or themed SSIDs

### Protected SSIDs
- Your production networks
- **Never modified** by the rotation script
- Multiple safety validations

## Safety Features

✅ Protected SSID validation before every operation  
✅ Process locking prevents concurrent rotations  
✅ Atomic file writes with automatic backups  
✅ WLAN ID verification and auto-recovery  
✅ API retry logic with timeout protection  
✅ State corruption detection and recovery  

## Usage

### Test API Connection
```bash
python3 test_unifi_udr7.py
```

### Manual Rotation
```bash
python3 /opt/ssid-rotator/rotate_ssid.py
```

### Web Interface
```bash
python3 /opt/ssid-rotator/web_manager.py
# Open browser to http://your-server-ip:5000
```

## Project Status

- ✅ **Phase 1**: API testing and verification (Complete)
- 🔲 **Phase 2**: Deployment to Raspberry Pi Zero W (Planned: Week of Dec 23, 2024)
- 🔲 **Phase 3**: Production monitoring (Ongoing)

## Hardware

**Tested on:**
- UniFi Dream Router (UDR) Pro 7
- Raspberry Pi Zero W v1.1 (planned deployment)

## Contributing

This is a personal project, but suggestions and improvements are welcome. See [`CONTRIBUTING.md`](CONTRIBUTING.md) for guidelines.

## License

MIT License - See LICENSE file for details

## Credits

Created by Matt (@watmatt00) for managing entertaining WiFi SSID rotations on UniFi networks.

## Support

For issues or questions:
- Check the [Complete Guide](ssid-rotator-guide.md)
- Review [Project Rules](PROJECT_RULES.md)
- Run the test script to verify connectivity

---

**⚠️ Important**: Always ensure your protected SSIDs are properly configured before running the rotation script. The system includes multiple safety checks, but configuration validation is essential.
