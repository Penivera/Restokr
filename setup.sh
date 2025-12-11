#!/bin/bash

# ReStockr API Setup Script

set -e

echo "🚀 ReStockr Early Access API Setup"
echo "=================================="
echo ""

# Install dependencies
echo "📦 Installing Python dependencies..."
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

echo ""
echo "✅ Dependencies installed!"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created. Please update with your credentials!"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🗄️  Database Setup Instructions:"
echo "=================================="
echo ""
echo "1. Make sure PostgreSQL is running"
echo "2. Create the database:"
echo "   psql -U postgres"
echo "   CREATE DATABASE restokr;"
echo "   \\c restokr"
echo "   CREATE EXTENSION postgis;"
echo "   \\q"
echo ""
echo "3. Run migrations:"
echo "   ./venv/bin/alembic revision --autogenerate -m 'Initial migration'"
echo "   ./venv/bin/alembic upgrade head"
echo ""
echo "4. Start the server:"
echo "   ./venv/bin/uvicorn app.main:app --reload"
echo ""
echo "📚 Access the API:"
echo "   - Docs: http://localhost:8000/docs"
echo "   - Health: http://localhost:8000/api/v1/health"
echo ""
echo "🔐 Default Admin Credentials:"
echo "   - Username: admin"
echo "   - Password: changeme123"
echo ""
echo "✅ Setup complete! Follow the instructions above to get started."
