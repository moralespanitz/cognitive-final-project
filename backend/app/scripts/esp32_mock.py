"""
ESP32-CAM Mock - Simula el envío de imágenes desde el hardware ESP32-CAM
Basado en el código real del ESP32
"""
import time
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import random
from datetime import datetime

# ===== Configuración del endpoint =====
SERVER_URL = "http://localhost:8000/api/v1/video/device/upload"
ROUTE_ID = "taxi-01"  # Identificación del taxista

# ===== Intervalos =====
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


def send_image(route_id: str):
    """Envía una imagen al servidor, simulando el ESP32."""
    try:
        # Generar imagen
        image_bytes = generate_mock_image(route_id)

        # Headers como en el ESP32
        headers = {
            "Content-Type": "image/jpeg",
            "X-Route-ID": route_id
        }

        # Enviar POST
        response = requests.post(
            SERVER_URL,
            data=image_bytes,
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Imagen enviada. Código: {response.status_code}, Size: {result.get('size')} bytes")
        else:
            print(f"❌ Error al enviar: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Loop principal - simula el loop() del ESP32."""
    print("=" * 60)
    print("🎥 ESP32-CAM Mock Simulator")
    print(f"📡 Servidor: {SERVER_URL}")
    print(f"🚕 Route ID: {ROUTE_ID}")
    print(f"⏱️  Intervalo: {SHOT_INTERVAL} segundos")
    print("=" * 60)
    print("\nEnviando imágenes... (Ctrl+C para detener)\n")

    try:
        while True:
            send_image(ROUTE_ID)
            time.sleep(SHOT_INTERVAL)

    except KeyboardInterrupt:
        print("\n\n🛑 Simulador detenido")


if __name__ == "__main__":
    main()
