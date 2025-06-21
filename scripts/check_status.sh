#!/bin/bash
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
# Check status of all Music Analyzer services

echo "================================"
echo "Music Analyzer Services Status"
echo "================================"
echo ""

# Function to check service and port
check_service_port() {
    local name=$1
    local service=$2
    local port=$3
    
    # Check systemd service
    if systemctl is-active --quiet $service 2>/dev/null; then
        service_status="✓ Running"
    else
        service_status="✗ Not running"
    fi
    
    # Check port
    if nc -z localhost $port 2>/dev/null; then
        port_status="✓ Port $port open"
    else
        port_status="✗ Port $port closed"
    fi
    
    echo "$name:"
    echo "  Service: $service_status"
    echo "  Network: $port_status"
}

# Function to check process
check_process() {
    local name=$1
    local process=$2
    local port=$3
    
    # Check process
    if ps aux | grep -q "[${process:0:1}]${process:1}"; then
        process_status="✓ Running"
    else
        process_status="✗ Not running"
    fi
    
    # Check port
    if nc -z localhost $port 2>/dev/null; then
        port_status="✓ Port $port open"
    else
        port_status="✗ Port $port closed"
    fi
    
    echo "$name:"
    echo "  Process: $process_status"
    echo "  Network: $port_status"
}

# Check services
echo "Core Services:"
echo "--------------"
check_service_port "PostgreSQL" "postgresql" 5432
check_service_port "Redis" "redis-server" 6379
check_service_port "MinIO" "minio" 9000
check_process "Music Analyzer API" "music_analyzer_api.py" 8000
check_service_port "Service Monitor" "service-monitor" 0

echo ""
echo "Disk Space:"
echo "-----------"
df -h / /home | grep -E "^/|Filesystem" | awk '{printf "%-20s %5s %5s %5s %5s\n", $1, $2, $3, $4, $5}'

echo ""
echo "API Health Check:"
echo "-----------------"
if curl -s -u parakeet:Q7+vD#8kN$2pL@9 http://localhost:8000/api/v2/health > /tmp/health.json 2>/dev/null; then
    echo "API Status: ✓ Responding"
    cat /tmp/health.json | python3 -m json.tool
else
    echo "API Status: ✗ Not responding"
fi

echo ""
echo "Recent Alerts:"
echo "--------------"
if [ -f "/home/davegornshtein/parakeet-tdt-deployment/src/monitoring/logs/alerts.log" ]; then
    tail -5 /home/davegornshtein/parakeet-tdt-deployment/src/monitoring/logs/alerts.log 2>/dev/null || echo "No recent alerts"
else
    echo "No alerts log found"
fi

echo ""
echo "Access URLs:"
echo "------------"
echo "Frontend: http://localhost:8000/"
echo "API Docs: http://localhost:8000/api"
echo "MinIO Console: http://localhost:9001/"
echo "  Username: minioadmin"
echo "  Password: (see .env file)"
echo ""