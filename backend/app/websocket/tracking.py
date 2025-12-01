"""
WebSocket consumer for real-time GPS tracking.
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for tracking updates."""

    def __init__(self):
        # Store active connections
        self.active_connections: Set[WebSocket] = set()
        # Store connections by vehicle_id
        self.vehicle_subscribers: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"New WebSocket connection. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        self.active_connections.discard(websocket)
        # Remove from vehicle subscriptions
        for vehicle_id, subscribers in list(self.vehicle_subscribers.items()):
            subscribers.discard(websocket)
            if not subscribers:
                del self.vehicle_subscribers[vehicle_id]
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    async def send_to_vehicle_subscribers(self, vehicle_id: int, message: dict):
        """Send message to clients subscribed to specific vehicle."""
        if vehicle_id not in self.vehicle_subscribers:
            return

        disconnected = set()
        for connection in self.vehicle_subscribers[vehicle_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to subscriber: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    def subscribe_to_vehicle(self, websocket: WebSocket, vehicle_id: int):
        """Subscribe a WebSocket to updates for a specific vehicle."""
        if vehicle_id not in self.vehicle_subscribers:
            self.vehicle_subscribers[vehicle_id] = set()
        self.vehicle_subscribers[vehicle_id].add(websocket)


# Global connection manager instance
tracking_manager = ConnectionManager()


async def broadcast_location_update(location_data: dict):
    """
    Broadcast GPS location update to all connected clients.
    Called when new GPS data is received.
    """
    message = {
        "type": "location_update",
        "data": location_data
    }
    await tracking_manager.broadcast(message)
