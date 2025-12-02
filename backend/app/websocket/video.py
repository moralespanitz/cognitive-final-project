"""
WebSocket for real-time video streaming from ESP32-CAM devices.
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import asyncio
import logging

logger = logging.getLogger(__name__)


class VideoStreamManager:
    """Manages WebSocket connections for video streaming."""

    def __init__(self):
        self.connections: Dict[str, Set[WebSocket]] = {}  # route_id -> connections

    async def connect(self, websocket: WebSocket, route_id: str):
        """Accept connection and subscribe to route."""
        await websocket.accept()
        if route_id not in self.connections:
            self.connections[route_id] = set()
        self.connections[route_id].add(websocket)
        logger.info(f"Client connected to stream: {route_id}")

    def disconnect(self, websocket: WebSocket, route_id: str):
        """Remove connection."""
        if route_id in self.connections:
            self.connections[route_id].discard(websocket)
            if not self.connections[route_id]:
                del self.connections[route_id]
        logger.info(f"Client disconnected from stream: {route_id}")

    async def broadcast_frame(self, route_id: str, frame_data: dict):
        """Send frame to all clients watching this route."""
        if route_id not in self.connections:
            return

        disconnected = set()
        for ws in self.connections[route_id]:
            try:
                await ws.send_json(frame_data)
            except Exception:
                disconnected.add(ws)

        for ws in disconnected:
            self.disconnect(ws, route_id)


# Global instance
video_manager = VideoStreamManager()
