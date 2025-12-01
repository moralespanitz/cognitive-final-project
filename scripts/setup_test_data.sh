#!/bin/bash
# Setup test data for TaxiWatch

API_URL="http://localhost:8000/api/v1"

echo "=================================="
echo "TaxiWatch - Setup Test Data"
echo "=================================="

# Register admin user
echo -e "\n1. Registering admin user..."
curl -s -X POST "$API_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testadmin",
    "email": "testadmin@taxiwatch.com",
    "password": "Admin123!",
    "first_name": "Test",
    "last_name": "Admin",
    "role": "ADMIN"
  }' > /dev/null

# Login and get token
echo "2. Logging in..."
TOKEN=$(curl -s -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"testadmin","password":"Admin123!"}' | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo "✗ Failed to authenticate"
    exit 1
fi

echo "✓ Authenticated successfully"

# Create 5 vehicles
echo -e "\n3. Creating test vehicles..."
echo "=================================="

for i in {1..5}; do
    case $i in
        1) MAKE="Toyota"; MODEL="Camry"; YEAR=2022 ;;
        2) MAKE="Honda"; MODEL="Accord"; YEAR=2023 ;;
        3) MAKE="Ford"; MODEL="Fusion"; YEAR=2021 ;;
        4) MAKE="Chevrolet"; MODEL="Malibu"; YEAR=2022 ;;
        5) MAKE="Nissan"; MODEL="Altima"; YEAR=2023 ;;
    esac
    
    RESPONSE=$(curl -s -X POST "$API_URL/vehicles" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"license_plate\": \"NYC-00$i\",
        \"make\": \"$MAKE\",
        \"model\": \"$MODEL\",
        \"year\": $YEAR,
        \"color\": \"Yellow\",
        \"vin\": \"1HGCM82633A12345$i\",
        \"capacity\": 4,
        \"status\": \"ACTIVE\"
      }")
    
    ID=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', 'ERROR'))" 2>/dev/null)
    
    if [ "$ID" != "ERROR" ] && [ -n "$ID" ]; then
        echo "✓ Created: NYC-00$i ($MAKE $MODEL) - ID: $ID"
    else
        echo "✗ Failed to create NYC-00$i"
    fi
done

echo "=================================="
echo -e "\n✓ Setup complete!"
echo "You can now run: python3 hardware/gps_simulator.py"
