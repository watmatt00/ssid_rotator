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
