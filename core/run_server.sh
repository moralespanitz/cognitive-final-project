#!/bin/bash
# TaxiWatch Development Server Launcher

echo "🚀 Starting TaxiWatch Backend Server..."
echo ""
echo "📍 Server will be available at: http://localhost:8000"
echo "🔐 Admin Panel: http://localhost:8000/admin/"
echo ""
echo "Superuser Credentials:"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "Press Ctrl+C to stop the server"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Run the Django development server with uv
DJANGO_SETTINGS_MODULE=taxiwatch.settings_dev uv run python manage.py runserver
