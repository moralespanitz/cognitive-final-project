#!/bin/bash

# GPS Simulator for TaxiWatch (curl-based version)
# Simulates GPS data from 5 vehicles and sends it to the backend API

API_URL="http://localhost:8000/api/v1/tracking/location"
NUM_VEHICLES=5
UPDATE_INTERVAL=5  # seconds

# NYC coordinates
CENTER_LAT=40.7128
CENTER_LNG=-74.0060
RADIUS=0.05

echo "============================================================"
echo "TaxiWatch GPS Simulator"
echo "============================================================"
echo "Simulating $NUM_VEHICLES vehicles"
echo "Update interval: $UPDATE_INTERVAL seconds"
echo "API endpoint: $API_URL"
echo "Center: $CENTER_LAT, $CENTER_LNG"
echo "============================================================"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Initialize vehicle positions
declare -A vehicle_lat
declare -A vehicle_lng
declare -A vehicle_heading
declare -A vehicle_speed

for i in $(seq 1 $NUM_VEHICLES); do
    # Random starting position
    angle=$(awk "BEGIN {print rand() * 6.28318}")  # 2*PI
    distance=$(awk "BEGIN {print rand() * $RADIUS}")

    lat=$(awk "BEGIN {print $CENTER_LAT + $distance * cos($angle)}")
    lng=$(awk "BEGIN {print $CENTER_LNG + $distance * sin($angle)}")
    heading=$(awk "BEGIN {print rand() * 360}")
    speed=$(awk "BEGIN {print 20 + rand() * 40}")

    vehicle_lat[$i]=$lat
    vehicle_lng[$i]=$lng
    vehicle_heading[$i]=$heading
    vehicle_speed[$i]=$speed
done

iteration=0

# Main simulation loop
while true; do
    iteration=$((iteration + 1))
    timestamp=$(date +"%H:%M:%S")

    echo ""
    echo "[$timestamp] Iteration $iteration"
    echo "------------------------------------------------------------"

    for i in $(seq 1 $NUM_VEHICLES); do
        # Get current values
        lat=${vehicle_lat[$i]}
        lng=${vehicle_lng[$i]}
        heading=${vehicle_heading[$i]}
        speed=${vehicle_speed[$i]}

        # Update position
        speed_deg_per_sec=$(awk "BEGIN {print ($speed / 111000) * $UPDATE_INTERVAL}")
        heading_rad=$(awk "BEGIN {print $heading * 0.0174533}")  # degrees to radians

        new_lat=$(awk "BEGIN {print $lat + $speed_deg_per_sec * cos($heading_rad)}")
        new_lng=$(awk "BEGIN {print $lng + $speed_deg_per_sec * sin($heading_rad) / cos($lat * 0.0174533)}")

        # Random turn (30% chance)
        if [ $((RANDOM % 10)) -lt 3 ]; then
            turn=$(awk "BEGIN {print (rand() * 60) - 30}")
            heading=$(awk "BEGIN {h = $heading + $turn; if (h < 0) h += 360; if (h >= 360) h -= 360; print h}")
        fi

        # Random speed change (20% chance)
        if [ $((RANDOM % 10)) -lt 2 ]; then
            speed_change=$(awk "BEGIN {print (rand() * 20) - 10}")
            speed=$(awk "BEGIN {s = $speed + $speed_change; if (s < 10) s = 10; if (s > 80) s = 80; print s}")
        fi

        # Keep within bounds
        if awk "BEGIN {exit !((($new_lat - $CENTER_LAT) > $RADIUS) || (($new_lat - $CENTER_LAT) < -$RADIUS))}"; then
            heading=$(awk "BEGIN {h = $heading + 180; if (h >= 360) h -= 360; print h}")
            new_lat=$CENTER_LAT
        fi

        if awk "BEGIN {exit !((($new_lng - $CENTER_LNG) > $RADIUS) || (($new_lng - $CENTER_LNG) < -$RADIUS))}"; then
            heading=$(awk "BEGIN {h = $heading + 180; if (h >= 360) h -= 360; print h}")
            new_lng=$CENTER_LNG
        fi

        # Update stored values
        vehicle_lat[$i]=$new_lat
        vehicle_lng[$i]=$new_lng
        vehicle_heading[$i]=$heading
        vehicle_speed[$i]=$speed

        # Round values for display
        display_lat=$(printf "%.6f" $new_lat)
        display_lng=$(printf "%.6f" $new_lng)
        display_speed=$(printf "%.1f" $speed)
        display_heading=$(printf "%.1f" $heading)
        accuracy=$(awk "BEGIN {print 5 + rand() * 10}")
        altitude=$(awk "BEGIN {print 10 + rand() * 40}")

        # Send GPS data to API
        json_data=$(cat <<EOF
{
  "vehicle_id": $i,
  "latitude": $display_lat,
  "longitude": $display_lng,
  "speed": $display_speed,
  "heading": $display_heading,
  "accuracy": $accuracy,
  "altitude": $altitude,
  "device_id": "SIM_GPS_$(printf "%03d" $i)"
}
EOF
)

        response=$(curl -s -X POST "$API_URL" \
            -H "Content-Type: application/json" \
            -d "$json_data" \
            -w "\n%{http_code}")

        http_code=$(echo "$response" | tail -n 1)

        if [ "$http_code" = "201" ]; then
            echo "✓ Vehicle $i: $display_lat, $display_lng @ $display_speed km/h"
        else
            echo "✗ Vehicle $i: Error $http_code"
        fi
    done

    # Wait before next update
    sleep $UPDATE_INTERVAL
done
