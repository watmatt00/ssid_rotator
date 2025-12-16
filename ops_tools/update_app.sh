#!/bin/bash
set -euo pipefail

LOG_FILE="/var/log/ssid-rotator.log"
REPO_DIR="$HOME/ssid_rotator"

log_message() {
    local message="$1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') update_app.sh - $message" | tee -a "$LOG_FILE" >&2
}

cleanup_pycache() {
    local target_dir="$REPO_DIR/src"
    
    if [[ -d "$target_dir" ]]; then
        log_message "Removing Python __pycache__ directories under $target_dir"
        find "$target_dir" -type d -name "__pycache__" -print -exec rm -rf {} + 2>/dev/null || true
        find "$target_dir" -type f -name "*.pyc" -delete 2>/dev/null || true
    else
        log_message "src directory not found at $target_dir (skipping __pycache__ cleanup)"
    fi
}

log_message "===== Starting SSID Rotator update ====="

# Verify git repo
if [[ ! -d "$REPO_DIR/.git" ]]; then
    log_message "Repository directory $REPO_DIR does not look like a git repo. Aborting."
    exit 1
fi

cd "$REPO_DIR"

# Fetch from GitHub
log_message "Fetching latest changes from origin..."
if git fetch --all >>"$LOG_FILE" 2>&1; then
    log_message "git fetch completed."
else
    log_message "git fetch failed."
    exit 1
fi

# Reset to origin/main (discard any local changes)
log_message "Resetting local branch to origin/main..."
if git reset --hard origin/main >>"$LOG_FILE" 2>&1; then
    log_message "git reset --hard origin/main completed."
else
    log_message "git reset --hard origin/main failed."
    exit 1
fi

# Clean up stale Python bytecode
cleanup_pycache

# Ensure Python scripts are executable
log_message "Setting execute permissions on Python scripts..."
if chmod +x "$REPO_DIR"/src/*.py 2>>"$LOG_FILE"; then
    log_message "Python scripts are now executable."
else
    log_message "WARNING: chmod failed on Python scripts"
fi

# Restart web interface service
log_message "Restarting web interface..."
if sudo systemctl restart ssid-web-manager 2>>"$LOG_FILE"; then
    log_message "Web interface restarted successfully."
else
    log_message "WARNING: Web interface restart failed (may not be installed yet)"
fi

log_message "===== SSID Rotator update completed successfully ====="
exit 0
