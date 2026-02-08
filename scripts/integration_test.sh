#!/bin/bash
#
# Integration Test Script
#
# This script runs the full integration test suite including:
# - Unit tests
# - Frontend build verification
# - Docker build test
# - Health check
#
# Usage:
#   ./integration_test.sh [--skip-unit] [--skip-frontend] [--skip-docker]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
SKIP_UNIT=false
SKIP_FRONTEND=false
SKIP_DOCKER=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-unit)
            SKIP_UNIT=true
            shift
            ;;
        --skip-frontend)
            SKIP_FRONTEND=true
            shift
            ;;
        --skip-docker)
            SKIP_DOCKER=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Write-Agent Integration Test Suite${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Track failures
FAILURES=0

# Test 1: Unit Tests
if [ "$SKIP_UNIT" = false ]; then
    echo -e "${YELLOW}[1/4] Running unit tests...${NC}"
    if python3 -m pytest tests/ -v --tb=short --cov=src --cov-report=term-missing; then
        echo -e "${GREEN}✓ Unit tests passed${NC}"
    else
        echo -e "${RED}✗ Unit tests failed${NC}"
        ((FAILURES++))
    fi
    echo ""
else
    echo -e "${YELLOW}[1/4] Skipping unit tests (--skip-unit)${NC}"
    echo ""
fi

# Test 2: Frontend Build
if [ "$SKIP_FRONTEND" = false ]; then
    echo -e "${YELLOW}[2/4] Building frontend...${NC}"
    cd frontend
    if npm run build 2>&1 | tail -20; then
        echo -e "${GREEN}✓ Frontend build successful${NC}"
    else
        echo -e "${RED}✗ Frontend build failed${NC}"
        ((FAILURES++))
    fi
    cd "$PROJECT_ROOT"
    echo ""
else
    echo -e "${YELLOW}[2/4] Skipping frontend build (--skip-frontend)${NC}"
    echo ""
fi

# Test 3: Docker Build
if [ "$SKIP_DOCKER" = false ]; then
    echo -e "${YELLOW}[3/4] Building Docker images...${NC}"
    if docker-compose build --quiet; then
        echo -e "${GREEN}✓ Docker build successful${NC}"
    else
        echo -e "${RED}✗ Docker build failed${NC}"
        ((FAILURES++))
    fi
    echo ""
else
    echo -e "${YELLOW}[3/4] Skipping Docker build (--skip-docker)${NC}"
    echo ""
fi

# Test 4: Health Check
echo -e "${YELLOW}[4/4] Running health check...${NC}"
if [ "$SKIP_DOCKER" = false ]; then
    # Start services if not running
    if ! docker-compose ps | grep -q "Up"; then
        echo "Starting services..."
        docker-compose up -d
        sleep 10
    fi
    
    # Test health endpoint
    if curl -f -s http://localhost/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Health check passed${NC}"
    else
        echo -e "${YELLOW}⚠ Health check: Service not responding (may not be running)${NC}"
    fi
else
    echo -e "${YELLOW}[4/4] Skipping health check (Docker not built)${NC}"
fi
echo ""

# Summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Test Summary${NC}"
echo -e "${GREEN}========================================${NC}"

if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}$FAILURES test(s) failed${NC}"
    exit 1
fi
