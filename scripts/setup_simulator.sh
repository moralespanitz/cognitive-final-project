#!/bin/bash

API_URL="http://localhost:8000/api/v1"

echo "============================================================"
echo "TaxiWatch - GPS Simulator Setup"
echo "============================================================"

# Step 1: Register admin user
echo -e "\n1. Creating admin user..."

REGISTER=$(cat <<'EOF'
{
  "username": "admin",
  "email": "admin@taxiwatch.com",
  "password": "Admin123!",
  "first_name": "Admin",
  "last_name": "User",
  "role": "ADMIN"
}
EOF
)

curl -s -X POST "$API_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d "$REGISTER" > /dev/null 2>&1

# Step 2: Login
echo "2. Logging in..."

LOGIN=$(cat <<'EOF'
{
  "username": "admin",
  "password": "Admin123!"
}
EOF
)

LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "$LOGIN")

TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "   ✗ Login failed. Checking response..."
  echo "$LOGIN_RESPONSE"
  exit 1
fi

echo "   ✓ Login successful"

# Step 3: Create 5 test vehicles
echo -e "\n3. Creating test vehicles..."
echo "------------------------------------------------------------"

# Vehicle 1
VEHICLE1=$(cat <<'EOF'
{
  "license_plate": "NYC-001",
  "make": "Toyota",
  "model": "Camry",
  "year": 2022,
  "color": "Yellow",
  "vin": "1HGCM82633A123456",
  "capacity": 4,
  "status": "ACTIVE"
}
EOF
)

RESPONSE=$(curl -s -X POST "$API_URL/vehicles/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "$VEHICLE1")

if echo "$RESPONSE" | grep -q '"id"'; then
  echo "   ✓ Created: NYC-001"
else
  echo "   ℹ NYC-001 may already exist"
fi

# Vehicle 2
VEHICLE2=$(cat <<'EOF'
{
  "license_plate": "NYC-002",
  "make": "Honda",
  "model": "Accord",
  "year": 2023,
  "color": "Yellow",
  "vin": "1HGCM82633A123457",
  "capacity": 4,
  "status": "ACTIVE"
}
EOF
)

curl -s -X POST "$API_URL/vehicles/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "$VEHICLE2" > /dev/null 2>&1
echo "   ✓ Created: NYC-002"

# Vehicle 3
VEHICLE3=$(cat <<'EOF'
{
  "license_plate": "NYC-003",
  "make": "Ford",
  "model": "Fusion",
  "year": 2021,
  "color": "Yellow",
  "vin": "1HGCM82633A123458",
  "capacity": 4,
  "status": "ACTIVE"
}
EOF
)

curl -s -X POST "$API_URL/vehicles/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "$VEHICLE3" > /dev/null 2>&1
echo "   ✓ Created: NYC-003"

# Vehicle 4
VEHICLE4=$(cat <<'EOF'
{
  "license_plate": "NYC-004",
  "make": "Chevrolet",
  "model": "Malibu",
  "year": 2022,
  "color": "Yellow",
  "vin": "1HGCM82633A123459",
  "capacity": 4,
  "status": "ACTIVE"
}
EOF
)

curl -s -X POST "$API_URL/vehicles/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "$VEHICLE4" > /dev/null 2>&1
echo "   ✓ Created: NYC-004"

# Vehicle 5
VEHICLE5=$(cat <<'EOF'
{
  "license_plate": "NYC-005",
  "make": "Nissan",
  "model": "Altima",
  "year": 2023,
  "color": "Yellow",
  "vin": "1HGCM82633A123460",
  "capacity": 4,
  "status": "ACTIVE"
}
EOF
)

curl -s -X POST "$API_URL/vehicles/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "$VEHICLE5" > /dev/null 2>&1
echo "   ✓ Created: NYC-005"

echo "------------------------------------------------------------"
echo -e "\n✓ Setup complete!"
echo ""
echo "You can now run the GPS simulator:"
echo "  python3 hardware/gps_simulator.py"
echo ""
echo "Or use the enhanced version with better output:"
echo "  python3 scripts/run_simulator.py"
echo "============================================================"
