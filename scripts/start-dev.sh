#!/bin/bash

# Start Development Environment
# This script starts both backend and frontend services

echo "🚀 Starting Wellnest Development Environment..."

# Function to cleanup on exit
cleanup() {
    echo "🛑 Stopping all services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}

trap cleanup EXIT

# Start Backend
echo "📦 Starting Backend API..."
cd /Users/shwethanarayanan/Wellnest
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to be ready
echo "⏳ Waiting for backend to start..."
sleep 5

# Start Frontend
echo "🎨 Starting Dashboard Frontend..."
cd /Users/shwethanarayanan/Wellnest/dashboard
npm run dev &
FRONTEND_PID=$!

echo "✅ Development environment started!"
echo ""
echo "📍 Services:"
echo "   Backend API: http://localhost:8000"
echo "   Dashboard:   http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all services"

# Keep script running
wait