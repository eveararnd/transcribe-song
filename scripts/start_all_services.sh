#!/bin/bash
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
# Start all Music Analyzer services

echo "Starting Music Analyzer services..."

# Function to check if service is active
check_service() {
    local service=$1
    systemctl is-active --quiet $service
    return $?
}

# Function to wait for port
wait_for_port() {
    local port=$1
    local timeout=30
    local elapsed=0
    
    echo "Waiting for port $port to be available..."
    while ! nc -z localhost $port 2>/dev/null; do
        if [ $elapsed -ge $timeout ]; then
            echo "Timeout waiting for port $port"
            return 1
        fi
        sleep 1
        elapsed=$((elapsed + 1))
    done
    echo "Port $port is available"
    return 0
}

# Start PostgreSQL
echo "Starting PostgreSQL..."
sudo systemctl start postgresql
if ! check_service postgresql; then
    echo "Failed to start PostgreSQL"
    exit 1
fi
wait_for_port 5432

# Start Redis
echo "Starting Redis..."
sudo systemctl start redis-server
if ! check_service redis-server; then
    echo "Failed to start Redis"
    exit 1
fi
wait_for_port 6379

# Start MinIO
echo "Starting MinIO..."
sudo systemctl start minio
if ! check_service minio; then
    echo "Failed to start MinIO"
    exit 1
fi
wait_for_port 9000

# Create MinIO bucket if it doesn't exist
echo "Ensuring MinIO bucket exists..."
source /home/davegornshtein/parakeet-tdt-deployment/.env
export MC_HOST_local=http://$MINIO_ROOT_USER:$MINIO_ROOT_PASSWORD@localhost:9000

# Install mc (MinIO client) if not available
if ! command -v mc &> /dev/null; then
    wget -q https://dl.min.io/client/mc/release/linux-amd64/mc
    chmod +x mc
    sudo mv mc /usr/local/bin/
fi

# Create bucket
mc mb local/music-analyzer --ignore-existing

# Start Music Analyzer API
echo "Starting Music Analyzer API..."
cd /home/davegornshtein/parakeet-tdt-deployment
source /home/davegornshtein/parakeet-env/bin/activate

# Kill any existing API process
pkill -f music_analyzer_api.py || true
sleep 2

# Start API in background
export USE_TF=0
export PYTHONPATH=/home/davegornshtein/parakeet-tdt-deployment
nohup python src/api/music_analyzer_api.py > logs/api.log 2>&1 &
API_PID=$!
echo "Started Music Analyzer API with PID $API_PID"

# Wait for API to be ready
wait_for_port 8000

# Start Service Monitor
echo "Starting Service Monitor..."
sudo systemctl start service-monitor
if ! check_service service-monitor; then
    echo "Failed to start Service Monitor"
fi

echo ""
echo "All services started successfully!"
echo ""
echo "Service Status:"
echo "---------------"
systemctl is-active postgresql && echo "✓ PostgreSQL: Running" || echo "✗ PostgreSQL: Not running"
systemctl is-active redis-server && echo "✓ Redis: Running" || echo "✗ Redis: Not running"
systemctl is-active minio && echo "✓ MinIO: Running" || echo "✗ MinIO: Not running"
ps aux | grep -q "[m]usic_analyzer_api.py" && echo "✓ Music Analyzer API: Running" || echo "✗ Music Analyzer API: Not running"
systemctl is-active service-monitor && echo "✓ Service Monitor: Running" || echo "✗ Service Monitor: Not running"

echo ""
echo "Access Points:"
echo "--------------"
echo "Frontend: http://localhost:8000/"
echo "API: http://localhost:8000/api"
echo "MinIO Console: http://localhost:9001/"
echo ""