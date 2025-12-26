#!/bin/bash
# SSID Rotator Service Control Script
# Provides easy commands to manage the SSID rotator services

set -euo pipefail

# Service names
WEB_SERVICE="ssid-web-manager.service"
TIMER_SERVICE="ssid-rotator.timer"
ROTATION_SERVICE="ssid-rotator.service"
LOG_FILE="/var/log/ssid-rotator.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_usage() {
    cat << EOF
SSID Rotator Service Control

Usage: $0 <command>

Commands:
  start           Start web manager and enable auto-rotation timer
  stop            Stop web manager and disable auto-rotation timer
  restart         Restart web manager service
  status          Show status of all services
  logs            View recent logs (last 50 lines)
  logs-live       Follow logs in real-time
  rotate-now      Manually trigger SSID rotation
  enable-timer    Enable automatic rotation timer (18hr schedule)
  disable-timer   Disable automatic rotation timer
  web-start       Start only the web manager
  web-stop        Stop only the web manager
  web-restart     Restart only the web manager
  help            Show this help message

Examples:
  $0 start        # Start all services
  $0 status       # Check service status
  $0 logs-live    # Watch logs in real-time
  $0 rotate-now   # Run rotation immediately
EOF
}

check_systemd() {
    if ! command -v systemctl &> /dev/null; then
        echo -e "${RED}Error: systemctl not found. This script requires systemd.${NC}"
        exit 1
    fi
}

start_all() {
    echo -e "${BLUE}Starting SSID Rotator services...${NC}"

    echo -e "${YELLOW}Starting web manager...${NC}"
    sudo systemctl start "$WEB_SERVICE"

    echo -e "${YELLOW}Enabling and starting rotation timer...${NC}"
    sudo systemctl enable "$TIMER_SERVICE"
    sudo systemctl start "$TIMER_SERVICE"

    echo -e "${GREEN}✓ Services started successfully${NC}"
    echo ""
    show_status
}

stop_all() {
    echo -e "${BLUE}Stopping SSID Rotator services...${NC}"

    echo -e "${YELLOW}Stopping web manager...${NC}"
    sudo systemctl stop "$WEB_SERVICE"

    echo -e "${YELLOW}Stopping rotation timer...${NC}"
    sudo systemctl stop "$TIMER_SERVICE"

    echo -e "${GREEN}✓ Services stopped${NC}"
}

restart_all() {
    echo -e "${BLUE}Restarting SSID Rotator services...${NC}"

    echo -e "${YELLOW}Restarting web manager...${NC}"
    sudo systemctl restart "$WEB_SERVICE"

    echo -e "${YELLOW}Restarting rotation timer...${NC}"
    sudo systemctl restart "$TIMER_SERVICE"

    echo -e "${GREEN}✓ Services restarted successfully${NC}"
    echo ""
    show_status
}

show_status() {
    echo -e "${BLUE}=== Service Status ===${NC}"
    echo ""

    echo -e "${YELLOW}Web Manager:${NC}"
    systemctl status "$WEB_SERVICE" --no-pager -l || true
    echo ""

    echo -e "${YELLOW}Rotation Timer:${NC}"
    systemctl status "$TIMER_SERVICE" --no-pager -l || true
    echo ""

    echo -e "${YELLOW}Next Scheduled Rotation:${NC}"
    systemctl list-timers "$TIMER_SERVICE" --no-pager || true
    echo ""
}

show_logs() {
    if [[ -f "$LOG_FILE" ]]; then
        echo -e "${BLUE}=== Recent Logs (last 50 lines) ===${NC}"
        tail -n 50 "$LOG_FILE"
    else
        echo -e "${RED}Log file not found: $LOG_FILE${NC}"
        exit 1
    fi
}

follow_logs() {
    if [[ -f "$LOG_FILE" ]]; then
        echo -e "${BLUE}=== Following logs (Ctrl+C to exit) ===${NC}"
        tail -f "$LOG_FILE"
    else
        echo -e "${RED}Log file not found: $LOG_FILE${NC}"
        exit 1
    fi
}

rotate_now() {
    echo -e "${BLUE}Triggering manual SSID rotation...${NC}"
    echo -e "${YELLOW}Running rotation script...${NC}"

    if sudo systemctl start "$ROTATION_SERVICE"; then
        echo -e "${GREEN}✓ Rotation triggered successfully${NC}"
        echo ""
        echo -e "${YELLOW}Checking recent logs:${NC}"
        tail -n 20 "$LOG_FILE"
    else
        echo -e "${RED}✗ Rotation failed${NC}"
        echo ""
        echo -e "${YELLOW}Recent logs:${NC}"
        tail -n 20 "$LOG_FILE"
        exit 1
    fi
}

enable_timer() {
    echo -e "${BLUE}Enabling automatic rotation timer...${NC}"
    sudo systemctl enable "$TIMER_SERVICE"
    sudo systemctl start "$TIMER_SERVICE"
    echo -e "${GREEN}✓ Timer enabled${NC}"
    echo ""
    systemctl list-timers "$TIMER_SERVICE" --no-pager
}

disable_timer() {
    echo -e "${BLUE}Disabling automatic rotation timer...${NC}"
    sudo systemctl stop "$TIMER_SERVICE"
    sudo systemctl disable "$TIMER_SERVICE"
    echo -e "${GREEN}✓ Timer disabled${NC}"
}

web_start() {
    echo -e "${BLUE}Starting web manager...${NC}"
    sudo systemctl start "$WEB_SERVICE"
    echo -e "${GREEN}✓ Web manager started${NC}"
    systemctl status "$WEB_SERVICE" --no-pager -l || true
}

web_stop() {
    echo -e "${BLUE}Stopping web manager...${NC}"
    sudo systemctl stop "$WEB_SERVICE"
    echo -e "${GREEN}✓ Web manager stopped${NC}"
}

web_restart() {
    echo -e "${BLUE}Restarting web manager...${NC}"
    sudo systemctl restart "$WEB_SERVICE"
    echo -e "${GREEN}✓ Web manager restarted${NC}"
    systemctl status "$WEB_SERVICE" --no-pager -l || true
}

# Main script logic
check_systemd

if [[ $# -eq 0 ]]; then
    print_usage
    exit 1
fi

case "$1" in
    start)
        start_all
        ;;
    stop)
        stop_all
        ;;
    restart)
        restart_all
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    logs-live)
        follow_logs
        ;;
    rotate-now)
        rotate_now
        ;;
    enable-timer)
        enable_timer
        ;;
    disable-timer)
        disable_timer
        ;;
    web-start)
        web_start
        ;;
    web-stop)
        web_stop
        ;;
    web-restart)
        web_restart
        ;;
    help|--help|-h)
        print_usage
        ;;
    *)
        echo -e "${RED}Error: Unknown command '$1'${NC}"
        echo ""
        print_usage
        exit 1
        ;;
esac
