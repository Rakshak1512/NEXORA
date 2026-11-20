#!/bin/bash
echo "===================================================================="
echo "Starting CICADA OBSERVE Platform (Backend, Frontend, Collector)"
echo "===================================================================="

cd "$(dirname "$0")/../backend" && python run.py &
BACKEND_PID=$!
sleep 2

cd "$(dirname "$0")/../frontend" && npm run dev &
FRONTEND_PID=$!
sleep 2

cd "$(dirname "$0")/../collector" && python run.py &
COLLECTOR_PID=$!

echo "All services running:"
echo "- Frontend: http://localhost:3000"
echo "- Backend:  http://127.0.0.1:8000 (Docs at /docs)"
echo "- Collector: PID $COLLECTOR_PID"

wait $BACKEND_PID $FRONTEND_PID $COLLECTOR_PID

