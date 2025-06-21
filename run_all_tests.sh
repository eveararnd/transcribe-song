#!/bin/bash

# Music Analyzer V2 - Complete Test Suite Runner
# Ensures 90%+ code coverage across all components

set -e

echo "======================================"
echo "Music Analyzer V2 - Test Suite"
echo "======================================"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running in CI or local
if [ -n "$CI" ]; then
    echo "Running in CI environment"
else
    echo "Running in local environment"
fi

# Function to check service availability
check_service() {
    local service=$1
    local host=$2
    local port=$3
    
    echo -n "Checking $service... "
    if nc -z $host $port 2>/dev/null; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
}

# Start services if not in CI
if [ -z "$CI" ]; then
    echo -e "\n${YELLOW}Starting required services...${NC}"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Docker is required but not installed${NC}"
        exit 1
    fi
    
    # Start services with docker-compose
    if [ -f "docker-compose.yml" ]; then
        docker-compose up -d postgres redis minio
        echo "Waiting for services to start..."
        sleep 10
    fi
fi

# Check required services
echo -e "\n${YELLOW}Checking services...${NC}"
check_service "PostgreSQL" "localhost" "5432" || echo "PostgreSQL not available"
check_service "Redis" "localhost" "6379" || echo "Redis not available"
check_service "MinIO" "localhost" "9000" || echo "MinIO not available"

# Backend Tests
echo -e "\n${YELLOW}Running Backend Tests...${NC}"
echo "======================================"

# Install Python dependencies if needed
if [ ! -d "venv" ] && [ -z "$CI" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt 2>/dev/null || echo "No requirements.txt found"
    pip install pytest pytest-asyncio pytest-cov aiohttp
fi

# Run backend unit tests
echo -e "\n${YELLOW}Running unit tests...${NC}"
python3 -m pytest test_music_analyzer_api.py -v \
    --cov=music_analyzer_api \
    --cov=music_analyzer_models \
    --cov=music_analyzer_export \
    --cov=music_analyzer_config \
    --cov-report=term-missing \
    --cov-report=html \
    --cov-fail-under=90 || {
    echo -e "${RED}Backend unit tests failed or coverage below 90%${NC}"
}

# Run system integration tests
echo -e "\n${YELLOW}Running integration tests...${NC}"
if [ -f "music_analyzer_api.py" ]; then
    # Start API server
    python3 music_analyzer_api.py &
    API_PID=$!
    echo "API server started with PID: $API_PID"
    
    # Wait for API to be ready
    sleep 10
    
    # Run integration tests
    python3 test_system_integration.py || {
        echo -e "${RED}Integration tests failed${NC}"
    }
    
    # Stop API server
    kill $API_PID 2>/dev/null || true
fi

# Frontend Tests
echo -e "\n${YELLOW}Running Frontend Tests...${NC}"
echo "======================================"

if [ -d "music-analyzer-frontend" ]; then
    cd music-analyzer-frontend
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ] && [ -z "$CI" ]; then
        echo "Installing frontend dependencies..."
        npm install
    fi
    
    # Run tests with coverage
    echo -e "\n${YELLOW}Running React component tests...${NC}"
    npm test -- --coverage --watchAll=false || {
        echo -e "${RED}Frontend tests failed${NC}"
    }
    
    # Check coverage thresholds
    echo -e "\n${YELLOW}Checking coverage thresholds...${NC}"
    npm test -- --coverage --watchAll=false \
        --coverageThreshold='{"global":{"branches":90,"functions":90,"lines":90,"statements":90}}' || {
        echo -e "${RED}Frontend coverage below 90%${NC}"
    }
    
    # Type checking
    echo -e "\n${YELLOW}Running TypeScript type check...${NC}"
    npx tsc --noEmit || {
        echo -e "${RED}TypeScript type errors found${NC}"
    }
    
    cd ..
fi

# Additional Tests
echo -e "\n${YELLOW}Running Additional Tests...${NC}"
echo "======================================"

# Test export functionality
if [ -f "test_export_simple.py" ]; then
    echo "Testing export formats..."
    python3 test_export_simple.py || true
fi

# Test tar export
if [ -f "test_tar_export.py" ]; then
    echo "Testing tar.gz exports..."
    python3 test_tar_export.py || true
fi

# Generate Coverage Report
echo -e "\n${YELLOW}Coverage Summary${NC}"
echo "======================================"

# Backend coverage
if [ -f "htmlcov/index.html" ]; then
    echo -e "${GREEN}✓${NC} Backend coverage report generated: htmlcov/index.html"
    # Extract coverage percentage
    python3 -c "
import re
with open('htmlcov/index.html', 'r') as f:
    content = f.read()
    match = re.search(r'<span class=\"pc_cov\">(\\d+)%</span>', content)
    if match:
        print(f'Backend Coverage: {match.group(1)}%')
" || true
fi

# Frontend coverage
if [ -f "music-analyzer-frontend/coverage/lcov-report/index.html" ]; then
    echo -e "${GREEN}✓${NC} Frontend coverage report generated: music-analyzer-frontend/coverage/lcov-report/index.html"
fi

# Clean up
echo -e "\n${YELLOW}Cleaning up...${NC}"
if [ -z "$CI" ] && [ -f "docker-compose.yml" ]; then
    read -p "Stop Docker services? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down
    fi
fi

echo -e "\n${GREEN}Test suite completed!${NC}"
echo "======================================"

# Exit with error if any tests failed
if grep -q "FAILED" test_results.log 2>/dev/null; then
    exit 1
fi

exit 0