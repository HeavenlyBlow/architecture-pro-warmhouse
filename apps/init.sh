#!/bin/bash

set -e

echo "=========================================="
echo "  SmartHome Platform - Initialization"
echo "=========================================="

cd "$(dirname "$0")"

echo ""
echo "[1/3] Building services..."
docker-compose build

echo ""
echo "[2/3] Starting services..."
docker-compose up -d

echo ""
echo "[3/3] Waiting for services to be ready..."
sleep 10

echo ""
echo "=========================================="
echo "  Services Started Successfully!"
echo "=========================================="
echo ""
echo "Endpoints:"
echo "  - Gateway:          http://localhost:8080"
echo "  - Smart Home API:   http://localhost:8080/api/v1/sensors"
echo "  - Smart Home v2:    http://localhost:8080/api/v2/"
echo "  - Telemetry:        http://localhost:8080/api/v1/telemetry"
echo "  - Commands:         http://localhost:8080/api/v1/commands"
echo "  - Simulator:        http://localhost:8080/api/v1/simulator"
echo ""
echo "Swagger UI:"
echo "  - Smart Home:       http://localhost:8081/swagger/index.html"
echo "  - Telemetry:        http://localhost:8082/swagger/index.html"
echo "  - Commands:         http://localhost:8083/docs"
echo "  - Simulator:        http://localhost:8084/docs"
