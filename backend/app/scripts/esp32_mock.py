"""
ESP32-CAM Mock - Simula el envío de imágenes desde el hardware ESP32-CAM
Basado en el código real del ESP32

Usage:
    # Local development
    python esp32_mock.py

    # Production (AWS EC2)
    python esp32_mock.py --server http://98.92.214.232:8000 --route taxi-01

    # With trip association
    python esp32_mock.py --server http://98.92.214.232:8000 --route taxi-01 --trip 5
"""
import time
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import random
from datetime import datetime
import argparse
import sys

# ===== Default Configuration =====
DEFAULT_SERVER_URL = "http://98.92.214.232:8000/api/v1/video/device/upload"
DEFAULT_ROUTE_ID = "taxi-01"
DEFAULT_TRIP_ID = None
SHOT_INTERVAL = 3  # 3 segundos entre capturas


def generate_mock_image(route_id: str) -> bytes:
    """Genera una imagen JPEG de prueba simulando la cámara ESP32-CAM."""
    # Crear imagen de 640x480 (VGA)
    img = Image.new('RGB', (640, 480), color=(20, 40, 80))
    draw = ImageDraw.Draw(img)

    # Fuente
    try:
        font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
        font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Información del taxi
    timestamp = datetime.now().strftime("%H:%M:%S")
    draw.text((30, 40), f"🚕 {route_id}", fill=(255, 255, 0), font=font_large)
    draw.text((30, 120), f"Tiempo: {timestamp}", fill=(255, 255, 255), font=font_small)
    draw.text((30, 170), f"Velocidad: {random.randint(20, 80)} km/h", fill=(0, 255, 150), font=font_small)
    draw.text((30, 220), "EN VIVO", fill=(255, 50, 50), font=font_large)

    # Simular "ruido" de cámara
    for _ in range(8):
        x, y = random.randint(0, 600), random.randint(300, 450)
        size = random.randint(3, 12)
        color = (random.randint(80, 200), random.randint(80, 200), random.randint(80, 200))
        draw.ellipse([x, y, x + size, y + size], fill=color)

    # Convertir a JPEG con calidad similar al ESP32
    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=20)  # Calidad baja como en ESP32
    return buffer.getvalue()


def send_image(server_url: str, route_id: str, trip_id: str = None):
    """Envía una imagen al servidor, simulando el ESP32."""
    try:
        # Generar imagen
        image_bytes = generate_mock_image(route_id)

        # Headers como en el ESP32
        headers = {
            "Content-Type": "image/jpeg",
            "X-Route-ID": route_id
        }

        # Add trip ID if provided
        if trip_id:
            headers["X-Trip-ID"] = trip_id

        # Enviar POST
        response = requests.post(
            server_url,
            data=image_bytes,
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            trip_info = f", Trip: {trip_id}" if trip_id else ""
            print(f"✅ Frame sent - {route_id}{trip_info} | Size: {result.get('size')} bytes | {datetime.now().strftime('%H:%M:%S')}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)

    except requests.exceptions.ConnectionError:
        print(f"❌ Connection error - Server not reachable at {server_url}")
    except Exception as e:
        print(f"❌ Error: {e}")


def verify_connection(server_url: str):
    """Verify that the server is reachable and the endpoint exists."""
    try:
        # Check device list endpoint
        base_url = server_url.replace("/device/upload", "")
        response = requests.get(f"{base_url}/device/list", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server connected! Active devices: {data.get('count', 0)}")
            if data.get('devices'):
                print(f"   Current devices: {', '.join(data['devices'])}")
            return True
        else:
            print(f"⚠️  Server returned: {response.status_code}")
            return True  # Server is reachable
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to server: {server_url}")
        return False
    except Exception as e:
        print(f"⚠️  Verification error: {e}")
        return True  # Continue anyway


def main():
    """Loop principal - simula el loop() del ESP32."""
    parser = argparse.ArgumentParser(description="ESP32-CAM Mock Simulator")
    parser.add_argument("--server", "-s", default=DEFAULT_SERVER_URL,
                        help=f"Server URL (default: {DEFAULT_SERVER_URL})")
    parser.add_argument("--route", "-r", default=DEFAULT_ROUTE_ID,
                        help=f"Route/Device ID (default: {DEFAULT_ROUTE_ID})")
    parser.add_argument("--trip", "-t", default=DEFAULT_TRIP_ID,
                        help="Trip ID to associate frames with (optional)")
    parser.add_argument("--interval", "-i", type=int, default=SHOT_INTERVAL,
                        help=f"Seconds between frames (default: {SHOT_INTERVAL})")
    parser.add_argument("--count", "-c", type=int, default=0,
                        help="Number of frames to send (0 = infinite)")

    args = parser.parse_args()

    server_url = args.server
    if not server_url.endswith("/device/upload"):
        server_url = server_url.rstrip("/") + "/api/v1/video/device/upload"

    print("=" * 60)
    print("🎥 ESP32-CAM Mock Simulator")
    print("=" * 60)
    print(f"📡 Server:   {server_url}")
    print(f"🚕 Route ID: {args.route}")
    if args.trip:
        print(f"🎫 Trip ID:  {args.trip}")
    print(f"⏱️  Interval: {args.interval} seconds")
    if args.count > 0:
        print(f"🔢 Count:    {args.count} frames")
    print("=" * 60)

    # Verify connection first
    print("\n🔍 Verifying server connection...")
    if not verify_connection(server_url):
        print("\n❌ Cannot reach server. Please check:")
        print("   1. Server is running")
        print("   2. URL is correct")
        print("   3. Network/firewall allows connection")
        sys.exit(1)

    print(f"\n📸 Starting stream... (Ctrl+C to stop)\n")

    frames_sent = 0
    try:
        while True:
            send_image(server_url, args.route, args.trip)
            frames_sent += 1

            if args.count > 0 and frames_sent >= args.count:
                print(f"\n✅ Completed! Sent {frames_sent} frames.")
                break

            time.sleep(args.interval)

    except KeyboardInterrupt:
        print(f"\n\n🛑 Stopped. Total frames sent: {frames_sent}")


if __name__ == "__main__":
    main()
