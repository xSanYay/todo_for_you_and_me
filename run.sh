#!/bin/bash

# Clean Todo App - Startup Script
echo "🚀 Starting Clean Todo App with modular architecture..."

# Create virtual environment if it doesn't exist
if [ ! -d ".todo" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .todo
fi

# Activate virtual environment
source .todo/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
mkdir -p app/static/{css,js}
mkdir -p templates

# Run the FastAPI application with the new structure
echo "✨ Starting Clean Todo App..."
echo "🌐 Access the app at: http://localhost:8000"
echo "📊 Health check at: http://localhost:8000/health"
echo "🔧 Using enhanced theming with Froala Design Blocks"

# Use the main file (not main_new since it doesn't exist)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
