#!/usr/bin/env python3
from flask import Flask, render_template_string, request, jsonify
import json
import os
import subprocess
import re
from datetime import datetime
from ssid_validator import validate_ssid, get_ssid_byte_length, suggest_ssid_fix

app = Flask(__name__)

CONFIG = {
    "ssid_list_file": "/var/lib/ssid_rotator/ssid_list.json",
    "state_file": "/var/lib/ssid_rotator/state.json",
    "log_file": "/var/log/ssid-rotator.log"
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

def get_rotation_status():
    """
    Get the status of the last rotation attempt.
    Returns: tuple (status, message)
        status: 'success', 'error', or 'unknown'
        message: descriptive message
    """
    if not os.path.exists(CONFIG['log_file']):
        return 'unknown', 'No log file found'

    try:
        # Read last 200 lines of log file
        with open(CONFIG['log_file'], 'r') as f:
            lines = f.readlines()
            last_lines = lines[-200:] if len(lines) > 200 else lines

        # Find the most recent "Starting SSID rotator" to identify the last run
        last_rotation_start_idx = -1
        for i in range(len(last_lines) - 1, -1, -1):
            if 'Starting SSID rotator' in last_lines[i]:
                last_rotation_start_idx = i
                break

        if last_rotation_start_idx == -1:
            return 'unknown', 'No recent rotation found in logs'

        # Look at lines from the last rotation start to end
        rotation_lines = last_lines[last_rotation_start_idx:]

        # Check if this rotation completed successfully
        rotation_complete = False
        error_found = False
        error_msg = None

        for line in rotation_lines:
            if 'Rotation complete' in line or 'Updated SSID from' in line:
                rotation_complete = True
            elif 'ERROR:' in line:
                error_found = True
                error_msg = line.split('ERROR:', 1)[1].strip()

        # Determine status based on findings
        if rotation_complete and not error_found:
            return 'success', 'Last rotation completed successfully'
        elif error_found:
            return 'error', f'Last rotation failed: {error_msg[:100] if error_msg else "Unknown error"}'
        else:
            return 'unknown', 'Rotation in progress or incomplete'

    except Exception as e:
        return 'unknown', f'Could not read log file: {str(e)}'

def get_next_rotation_time():
    """
    Get the next scheduled rotation time from systemd timer.
    Returns: datetime object or None
    """
    try:
        # Run systemctl to get timer info
        result = subprocess.run(
            ['systemctl', 'list-timers', 'ssid-rotator.timer', '--no-pager'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            # Parse output to find the NEXT column
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if 'ssid-rotator.timer' in line:
                    # Extract date/time from the line
                    # Format: "Thu 2025-12-18 19:46:39 MST"
                    match = re.search(r'(\w{3} \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                    if match:
                        time_str = match.group(1)
                        # Parse: "Thu 2025-12-18 19:46:39"
                        dt = datetime.strptime(time_str, '%a %Y-%m-%d %H:%M:%S')
                        return dt

        return None

    except Exception as e:
        return None

def format_datetime(dt_str):
    """
    Format datetime string to yyyy-mm-dd hh:mm
    Args:
        dt_str: ISO format datetime string (e.g., "2025-12-18T08:28:35.795344")
    Returns:
        Formatted string (e.g., "2025-12-18 08:28")
    """
    if not dt_str:
        return 'Never'

    try:
        # Parse ISO format datetime
        if isinstance(dt_str, str):
            dt = datetime.fromisoformat(dt_str)
        elif isinstance(dt_str, datetime):
            dt = dt_str
        else:
            return str(dt_str)

        # Format as yyyy-mm-dd hh:mm
        return dt.strftime('%Y-%m-%d %H:%M')
    except Exception:
        return str(dt_str)

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
            align-items: center;
            margin: 8px 0;
            font-size: 14px;
        }
        .status-label {
            color: #666;
        }
        .status-value {
            font-weight: bold;
            color: #333;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        /* Stoplight status indicators */
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 6px;
            box-shadow: 0 0 4px rgba(0,0,0,0.3);
        }
        .status-indicator.success {
            background: #28a745;
            box-shadow: 0 0 8px rgba(40, 167, 69, 0.6);
        }
        .status-indicator.error {
            background: #dc3545;
            box-shadow: 0 0 8px rgba(220, 53, 69, 0.6);
        }
        .status-indicator.unknown {
            background: #ffc107;
            box-shadow: 0 0 8px rgba(255, 193, 7, 0.6);
        }
        /* Auto-refresh indicator */
        .refresh-indicator {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: rgba(0, 0, 0, 0.7);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
            z-index: 1000;
            transition: opacity 0.3s;
        }
        .refresh-indicator:hover {
            background: rgba(0, 0, 0, 0.85);
        }
        .refresh-pause-btn {
            background: transparent;
            border: 1px solid rgba(255, 255, 255, 0.5);
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 11px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .refresh-pause-btn:hover {
            background: rgba(255, 255, 255, 0.2);
            border-color: white;
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
        .btn-make-next {
            background: #28a745;
            color: white;
            border: none;
            padding: 8px 14px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
        }
        .btn-make-next:hover:not(:disabled) {
            background: #218838;
        }
        .btn-make-next:disabled {
            background: #6c757d;
            cursor: not-allowed;
            opacity: 0.7;
        }
        .btn-rotate {
            background: #007bff;
            color: white;
            border: none;
            padding: 14px 28px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            width: 100%;
            transition: background 0.2s;
        }
        .btn-rotate:hover:not(:disabled) {
            background: #0056b3;
        }
        .btn-rotate:disabled {
            background: #6c757d;
            cursor: not-allowed;
            opacity: 0.7;
        }
        .rotate-status {
            margin-top: 10px;
            padding: 12px;
            border-radius: 4px;
            display: none;
            font-size: 14px;
        }
        .rotate-status.show {
            display: block;
        }
        .rotate-status.loading {
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffc107;
        }
        .rotate-status.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .rotate-status.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .ssid-item.next-item {
            border-left: 4px solid #ffc107;
            background: #fffbf0;
        }
        .tag.next {
            background: #ffc107;
            color: #000;
        }
        .tag.current {
            background: #007bff;
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
                <span class="status-label">Next Rotation SSID:</span>
                <span class="status-value">{{ active[(state.current_index + 1) % active|length] if active else 'N/A' }}</span>
            </div>
            <div class="status-row">
                <span class="status-label">Next Scheduled Rotation:</span>
                <span class="status-value">{{ next_rotation_formatted }}</span>
            </div>
            <div class="status-row">
                <span class="status-label">Last Rotation:</span>
                <span class="status-value">
                    <span class="status-indicator {{ rotation_status }}"></span>
                    {{ last_rotation_formatted }}
                </span>
            </div>
            <div class="status-row">
                <span class="status-label">Position in Cycle:</span>
                <span class="status-value">{{ state.current_index + 1 }} of {{ active|length }}</span>
            </div>
            <div class="status-row">
                <span class="status-label">Full Cycle Time:</span>
                <span class="status-value">{{ ((active|length * 18) / 24)|round(1) }} days</span>
            </div>
            
            <div class="status-row" style="margin-top: 20px;">
                <button onclick="rotateNow()" id="rotateBtn" class="btn-rotate">
                    🔄 Rotate SSID Now
                </button>
            </div>
            <div id="rotateStatus" class="rotate-status"></div>
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
                    <div class="ssid-item {% if state and loop.index0 == state.current_index %}current{% endif %} {% if state and loop.index0 == (state.current_index + 1) % active|length %}next-item{% endif %}">
                        <div class="ssid-name">
                            <span class="ssid-index">{{ loop.index }}</span>
                            <span>{{ ssid }}</span>
                            {% if state and loop.index0 == state.current_index %}
                                <span class="tag current">CURRENT</span>
                            {% elif state and loop.index0 == (state.current_index + 1) % active|length %}
                                <span class="tag next">NEXT</span>
                            {% endif %}
                        </div>
                        <div class="button-group">
                            {% if state and loop.index0 == (state.current_index + 1) % active|length %}
                                <button class="btn btn-make-next" disabled>✓ Next</button>
                            {% else %}
                                <button class="btn btn-make-next" onclick='makeNext({{ loop.index0 }}, {{ ssid|tojson }})'>Make Next</button>
                            {% endif %}
                            <button class="btn btn-secondary" onclick='moveToReserve({{ ssid|tojson }})'>→ Reserve</button>
                            <button class="btn btn-delete" onclick='deleteSSID({{ ssid|tojson }}, "active")'>Delete</button>
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
                            <button class="btn btn-success" onclick='moveToActive({{ ssid|tojson }})'>⚡ Activate</button>
                            <button class="btn btn-delete" onclick='deleteSSID({{ ssid|tojson }}, "reserve")'>Delete</button>
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
                        <button class="btn btn-delete" onclick='deleteSSID({{ ssid|tojson }}, "protected")'>Remove</button>
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

        function makeNext(targetIndex, ssidName) {
            if (!confirm(`Make "${ssidName}" the next SSID to rotate to?`)) {
                return;
            }
            
            fetch(`/api/set_next/${targetIndex}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    alert(data.message);
                    // Reload to show updated "NEXT" badge
                    setTimeout(() => window.location.reload(), 500);
                } else {
                    alert('Error: ' + data.message);
                }
            })
            .catch(error => {
                alert('Network error: ' + error);
            });
        }

        function rotateNow() {
            const btn = document.getElementById('rotateBtn');
            const statusDiv = document.getElementById('rotateStatus');
            
            if (!confirm('Push the staged SSID live to UniFi now?')) {
                return;
            }
            
            // Disable button and show loading
            btn.disabled = true;
            btn.innerHTML = '⏳ Rotating...';
            statusDiv.className = 'rotate-status show loading';
            statusDiv.innerHTML = 'Pushing SSID to UniFi...';
            
            fetch('/api/rotate_now', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    statusDiv.className = 'rotate-status show success';
                    statusDiv.innerHTML = '✅ ' + data.message;
                    
                    // Reload page after 2 seconds to show new SSID
                    setTimeout(() => {
                        window.location.reload();
                    }, 2000);
                } else {
                    statusDiv.className = 'rotate-status show error';
                    statusDiv.innerHTML = '❌ ' + data.message;
                    if (data.error) {
                        statusDiv.innerHTML += '<br><small>' + data.error + '</small>';
                    }
                    btn.disabled = false;
                    btn.innerHTML = '🔄 Rotate SSID Now';
                }
            })
            .catch(error => {
                statusDiv.className = 'rotate-status show error';
                statusDiv.innerHTML = '❌ Network error: ' + error;
                btn.disabled = false;
                btn.innerHTML = '🔄 Rotate SSID Now';
            });
        }

        // Auto-refresh functionality
        let refreshInterval = 60; // seconds
        let refreshCountdown = refreshInterval;
        let refreshTimer = null;
        let isPaused = false;

        function updateRefreshIndicator() {
            const indicator = document.getElementById('refreshCountdown');
            if (indicator) {
                if (isPaused) {
                    indicator.textContent = 'Paused';
                } else {
                    indicator.textContent = `Refreshing in ${refreshCountdown}s`;
                }
            }
        }

        function startRefreshTimer() {
            refreshTimer = setInterval(() => {
                if (!isPaused) {
                    refreshCountdown--;
                    updateRefreshIndicator();

                    if (refreshCountdown <= 0) {
                        window.location.reload();
                    }
                }
            }, 1000);
        }

        function toggleRefreshPause() {
            isPaused = !isPaused;
            const btn = document.getElementById('pauseRefreshBtn');
            if (btn) {
                btn.textContent = isPaused ? 'Resume' : 'Pause';
            }
            updateRefreshIndicator();
        }

        // Start the refresh timer when page loads
        window.addEventListener('DOMContentLoaded', function() {
            updateRefreshIndicator();
            startRefreshTimer();
        });
    </script>

    <!-- Auto-refresh indicator -->
    <div class="refresh-indicator">
        <span id="refreshCountdown">Refreshing in 60s</span>
        <button class="refresh-pause-btn" id="pauseRefreshBtn" onclick="toggleRefreshPause()">Pause</button>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    data = load_ssid_data()
    state = load_state()

    # Get rotation status and next scheduled time
    rotation_status, rotation_message = get_rotation_status()
    next_rotation_time = get_next_rotation_time()

    # Format timestamps
    last_rotation_formatted = format_datetime(state.get('last_rotation')) if state else 'Never'
    next_rotation_formatted = format_datetime(next_rotation_time) if next_rotation_time else 'Unknown'
    last_updated_formatted = format_datetime(data.get('last_updated'))

    return render_template_string(
        HTML_TEMPLATE,
        active=data.get('active_rotation', []),
        reserve=data.get('reserve_pool', []),
        protected=data.get('protected_ssids', []),
        last_updated=last_updated_formatted,
        state=state,
        rotation_status=rotation_status,
        rotation_message=rotation_message,
        last_rotation_formatted=last_rotation_formatted,
        next_rotation_formatted=next_rotation_formatted
    )

@app.route('/api/add', methods=['POST'])
def add_ssid():
    req_data = request.json
    ssid = req_data.get('ssid', '').strip()
    list_type = req_data.get('list_type', 'active')  # 'active', 'reserve', or 'protected'

    if not ssid:
        return jsonify({'success': False, 'error': 'SSID name is required'})

    # Validate SSID name according to 802.11 standards
    is_valid, error_msg = validate_ssid(ssid, strict=True)
    if not is_valid:
        # Try to suggest a fix
        suggested = suggest_ssid_fix(ssid)
        if suggested:
            return jsonify({
                'success': False,
                'error': error_msg,
                'suggestion': suggested,
                'byte_length': get_ssid_byte_length(ssid)
            })
        else:
            return jsonify({
                'success': False,
                'error': error_msg,
                'byte_length': get_ssid_byte_length(ssid)
            })

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

    return jsonify({'success': True, 'byte_length': get_ssid_byte_length(ssid)})

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

@app.route('/api/set_next/<int:target_index>', methods=['POST'])
def set_next(target_index):
    """Set which SSID should be next in rotation"""
    try:
        ssid_data = load_ssid_data()
        state = load_state()
        
        if state is None:
            return jsonify({
                'status': 'error',
                'message': 'No state file found. Run rotation script first.'
            }), 400
        
        active_list = ssid_data.get('active_rotation', [])
        
        # Validate target index
        if target_index < 0 or target_index >= len(active_list):
            return jsonify({
                'status': 'error',
                'message': f'Invalid index. Must be 0-{len(active_list)-1}'
            }), 400
        
        # Calculate what current_index should be to make target_index next
        # If next rotation is (current + 1) % len, then:
        # current = (target - 1 + len) % len
        new_current = (target_index - 1 + len(active_list)) % len(active_list)
        
        # Update state
        state['current_index'] = new_current
        state['staged_by_user'] = True  # Flag to indicate manual staging
        state['staged_at'] = datetime.now().isoformat()
        
        # Save state
        with open(CONFIG['state_file'], 'w') as f:
            json.dump(state, f, indent=2)
        
        return jsonify({
            'status': 'success',
            'message': f'Next rotation will use: {active_list[target_index]}',
            'next_ssid': active_list[target_index],
            'next_index': target_index
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/rotate_now', methods=['POST'])
def rotate_now():
    """Manually trigger SSID rotation"""
    try:
        import subprocess

        # Run the rotation script and append output to log file
        with open(CONFIG['log_file'], 'a') as log:
            result = subprocess.run(
                ['/usr/bin/python3', '/home/pi/ssid_rotator/src/rotate_ssid.py'],
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=30
            )

        # Read the last few lines of the log to show in the response
        with open(CONFIG['log_file'], 'r') as log:
            lines = log.readlines()
            last_output = ''.join(lines[-15:])  # Last 15 lines

        if result.returncode == 0:
            return jsonify({
                'status': 'success',
                'message': 'SSID rotation completed successfully',
                'output': last_output
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Rotation script failed',
                'error': last_output
            }), 500

    except subprocess.TimeoutExpired:
        return jsonify({
            'status': 'error',
            'message': 'Rotation script timed out (>30s)'
        }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    import ssl
    import os
    
    # SSL certificate paths
    cert_dir = os.path.expanduser('~/certs')
    cert_path = os.path.join(cert_dir, 'fullchain.pem')
    key_path = os.path.join(cert_dir, 'privkey.pem')
    
    # Check if certificates exist
    if os.path.exists(cert_path) and os.path.exists(key_path):
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(cert_path, key_path)
        print(f"Starting HTTPS server on port 5000 with SSL certificates from {cert_dir}")
        app.run(host='0.0.0.0', port=5000, ssl_context=ssl_context, debug=False)
    else:
        print(f"SSL certificates not found in {cert_dir}, starting HTTP server on port 5000")
        app.run(host='0.0.0.0', port=5000, debug=False)
