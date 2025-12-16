# SSL Certificate Setup

The web interface supports HTTPS using SSL/TLS certificates.

## Certificate Location

Place your SSL certificates in the `~/certs/` directory on the Raspberry Pi:

```
~/certs/
  ├── fullchain.pem  (public certificate + intermediate chain)
  └── privkey.pem    (private key)
```

## Installation

### 1. Create Certificate Directory

```bash
mkdir -p ~/certs
```

### 2. Copy Certificates from PC

From your PC, run:

```bash
# Copy private key
scp wildcard-local-privkey.pem pi@rotator.local:~/certs/privkey.pem

# Copy full chain certificate
scp wildcard-local-fullchain.pem pi@rotator.local:~/certs/fullchain.pem

# Set correct permissions
ssh pi@rotator.local "chmod 600 ~/certs/privkey.pem && chmod 644 ~/certs/fullchain.pem"
```

### 3. Restart Web Service

```bash
ssh pi@rotator.local
sudo systemctl restart ssid-web-manager
```

## Verification

### Check Service Logs

```bash
sudo journalctl -u ssid-web-manager -n 20
```

You should see:
```
Starting HTTPS server on port 5000 with SSL certificates from /home/pi/certs
```

### Access Web Interface

- **HTTPS**: https://rotator.local:5000
- **Alt**: https://192.168.102.205:5000

## Fallback Behavior

If certificates are **not found**, the service automatically falls back to HTTP:

```
SSL certificates not found in /home/pi/certs, starting HTTP server on port 5000
```

Access via: http://rotator.local:5000

## Certificate Renewal

When certificates are renewed, simply:

1. Copy new certificates to `~/certs/`
2. Restart service: `sudo systemctl restart ssid-web-manager`

No configuration changes needed!

## Troubleshooting

### Service won't start after adding certificates

Check certificate permissions:
```bash
ls -la ~/certs/
# Should show:
# -rw------- 1 pi pi ... privkey.pem
# -rw-r--r-- 1 pi pi ... fullchain.pem
```

### Browser shows "Certificate Not Trusted"

- Wildcard cert domain must match access URL
- For `*.local` certs, use `rotator.local`, not IP address
- Add CA certificate to browser trusted roots if using self-signed

### Check which mode is running

```bash
# View service logs
sudo journalctl -u ssid-web-manager -n 5 | grep "Starting"

# Test connection
curl -k https://rotator.local:5000  # HTTPS
curl http://rotator.local:5000      # HTTP (fallback)
```

## Security Notes

- **Private key** (`privkey.pem`) should be mode `600` (owner read/write only)
- **Certificate** (`fullchain.pem`) can be mode `644` (world-readable)
- Service runs as user `pi`, so certificates must be readable by `pi`
- Port 5000 doesn't require root/sudo (unlike port 443)
