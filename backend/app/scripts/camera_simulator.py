"""
Camera Simulator - Sends test video frames to the backend for WebSocket streaming.
This simulates an ESP32-CAM device sending JPEG images.
"""
import asyncio
import aiohttp
import io
from PIL import Image, ImageDraw, ImageFont
import random
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
import os
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
VIDEO_UPLOAD_ENDPOINT = f"{BACKEND_URL}/api/v1/video/device/upload"
# MVP: Only simulate one vehicle
VEHICLES = ["taxi-01"]
FRAME_INTERVAL = 3  # Send frame every 3 seconds


def generate_test_frame(route_id: str) -> bytes:
    """Generate a test JPEG frame with vehicle info."""
    # Create a test image with text
    img = Image.new('RGB', (640, 480), color=(30, 30, 60))  # Dark blue background
    draw = ImageDraw.Draw(img)

    # Add timestamp and vehicle info
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Try to use a default font, fallback to default if not available
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 32)
        small_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    # Draw vehicle info
    draw.text((50, 50), f"Vehicle: {route_id}", fill=(0, 255, 0), font=font)
    draw.text((50, 120), f"Time: {timestamp}", fill=(255, 255, 255), font=small_font)
    draw.text((50, 170), f"Speed: {random.randint(0, 100)} km/h", fill=(255, 200, 0), font=small_font)
    draw.text((50, 220), f"Status: LIVE", fill=(0, 255, 100), font=font)

    # Add a random element to simulate different frames
    for _ in range(5):
        x = random.randint(0, 640)
        y = random.randint(0, 480)
        size = random.randint(5, 20)
        color = (
            random.randint(100, 255),
            random.randint(100, 255),
            random.randint(100, 255)
        )
        draw.ellipse([x, y, x + size, y + size], fill=color)

    # Convert to JPEG bytes
    jpeg_buffer = io.BytesIO()
    img.save(jpeg_buffer, format='JPEG', quality=85)
    return jpeg_buffer.getvalue()


async def send_frame(route_id: str, session: aiohttp.ClientSession) -> bool:
    """Send a test frame to the backend."""
    try:
        frame_data = generate_test_frame(route_id)

        headers = {
            "X-Route-ID": route_id,
            "Content-Type": "image/jpeg"
        }

        async with session.post(
            VIDEO_UPLOAD_ENDPOINT,
            data=frame_data,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=10)
        ) as response:
            if response.status == 200:
                result = await response.json()
                logger.info(f"✅ Frame sent: {route_id} - {result['size']} bytes")
                return True
            else:
                logger.error(f"❌ Failed to send frame: {route_id} - Status {response.status}")
                return False
    except Exception as e:
        logger.error(f"❌ Error sending frame for {route_id}: {e}")
        return False


async def camera_simulator():
    """Continuously send frames for all vehicles."""
    logger.info("🎥 Camera Simulator Started")
    logger.info(f"Sending frames every {FRAME_INTERVAL} seconds to {len(VEHICLES)} vehicles")

    async with aiohttp.ClientSession() as session:
        vehicle_index = 0

        while True:
            try:
                # Cycle through vehicles, sending one frame per cycle
                route_id = VEHICLES[vehicle_index % len(VEHICLES)]
                await send_frame(route_id, session)
                vehicle_index += 1

                # Wait before sending next frame
                await asyncio.sleep(FRAME_INTERVAL)

            except KeyboardInterrupt:
                logger.info("🛑 Camera Simulator Stopped")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                await asyncio.sleep(FRAME_INTERVAL)


if __name__ == "__main__":
    asyncio.run(camera_simulator())
