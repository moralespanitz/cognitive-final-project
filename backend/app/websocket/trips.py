"""
WebSocket manager for real-time trip notifications.
Broadcasts trip updates to drivers and customers.
"""

from fastapi import WebSocket
from typing import Dict, Set
import json
import logging

logger = logging.getLogger(__name__)


class TripConnectionManager:
    """
    Manages WebSocket connections for real-time trip updates.
    - Drivers connect to receive new trip requests
    - Customers connect to receive updates on their trips
    """

    def __init__(self):
        # All connected drivers (available to receive new trips)
        self.driver_connections: Dict[int, WebSocket] = {}  # driver_id -> websocket

        # Customers tracking specific trips
        self.customer_connections: Dict[int, WebSocket] = {}  # customer_id -> websocket

        # Trip subscriptions (who is watching which trip)
        self.trip_watchers: Dict[int, Set[WebSocket]] = {}  # trip_id -> set of websockets

    async def connect_driver(self, websocket: WebSocket, driver_id: int):
        """Connect a driver to receive trip requests."""
        await websocket.accept()
        self.driver_connections[driver_id] = websocket
        logger.info(f"🚗 Driver {driver_id} connected. Total drivers: {len(self.driver_connections)}")

    async def connect_customer(self, websocket: WebSocket, customer_id: int):
        """Connect a customer to receive trip updates."""
        await websocket.accept()
        self.customer_connections[customer_id] = websocket
        logger.info(f"👤 Customer {customer_id} connected. Total customers: {len(self.customer_connections)}")

    def disconnect_driver(self, driver_id: int):
        """Disconnect a driver."""
        if driver_id in self.driver_connections:
            del self.driver_connections[driver_id]
            logger.info(f"🚗 Driver {driver_id} disconnected. Total drivers: {len(self.driver_connections)}")

    def disconnect_customer(self, customer_id: int):
        """Disconnect a customer."""
        if customer_id in self.customer_connections:
            del self.customer_connections[customer_id]
            logger.info(f"👤 Customer {customer_id} disconnected. Total customers: {len(self.customer_connections)}")

    def subscribe_to_trip(self, trip_id: int, websocket: WebSocket):
        """Subscribe to updates for a specific trip."""
        if trip_id not in self.trip_watchers:
            self.trip_watchers[trip_id] = set()
        self.trip_watchers[trip_id].add(websocket)
        logger.info(f"👁️ Subscribed to trip {trip_id}. Watchers: {len(self.trip_watchers[trip_id])}")

    def unsubscribe_from_trip(self, trip_id: int, websocket: WebSocket):
        """Unsubscribe from a trip's updates."""
        if trip_id in self.trip_watchers:
            self.trip_watchers[trip_id].discard(websocket)
            if not self.trip_watchers[trip_id]:
                del self.trip_watchers[trip_id]

    async def broadcast_new_trip(self, trip_data: dict):
        """
        Broadcast a new trip request to ALL connected drivers.
        This is the key feature - all drivers see new requests in real-time.
        """
        message = {
            "type": "new_trip",
            "trip": trip_data
        }

        disconnected = []
        for driver_id, websocket in self.driver_connections.items():
            try:
                await websocket.send_json(message)
                logger.info(f"📤 Sent new trip {trip_data.get('id')} to driver {driver_id}")
            except Exception as e:
                logger.error(f"Error sending to driver {driver_id}: {e}")
                disconnected.append(driver_id)

        # Clean up disconnected drivers
        for driver_id in disconnected:
            self.disconnect_driver(driver_id)

        logger.info(f"📢 Broadcasted trip to {len(self.driver_connections)} drivers")

    async def notify_trip_update(self, trip_id: int, trip_data: dict, event_type: str = "trip_update"):
        """
        Notify all watchers of a trip about an update.
        Used when trip status changes (accepted, arrived, started, completed).
        """
        message = {
            "type": event_type,
            "trip": trip_data
        }

        # Notify trip watchers
        if trip_id in self.trip_watchers:
            disconnected = []
            for websocket in self.trip_watchers[trip_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error notifying trip watcher: {e}")
                    disconnected.append(websocket)

            for ws in disconnected:
                self.trip_watchers[trip_id].discard(ws)

        # Also notify the customer directly if connected
        customer_id = trip_data.get("customer_id")
        if customer_id and customer_id in self.customer_connections:
            try:
                await self.customer_connections[customer_id].send_json(message)
                logger.info(f"📤 Sent {event_type} to customer {customer_id}")
            except Exception as e:
                logger.error(f"Error sending to customer {customer_id}: {e}")
                self.disconnect_customer(customer_id)

        # Notify the assigned driver
        driver_id = trip_data.get("driver_id")
        if driver_id and driver_id in self.driver_connections:
            try:
                await self.driver_connections[driver_id].send_json(message)
                logger.info(f"📤 Sent {event_type} to driver {driver_id}")
            except Exception as e:
                logger.error(f"Error sending to driver {driver_id}: {e}")
                self.disconnect_driver(driver_id)

    async def notify_trip_accepted(self, trip_data: dict):
        """Notify when a trip is accepted by a driver."""
        await self.notify_trip_update(
            trip_data["id"],
            trip_data,
            event_type="trip_accepted"
        )

        # Also broadcast to all drivers that this trip is no longer available
        remove_message = {
            "type": "trip_taken",
            "trip_id": trip_data["id"],
            "driver_id": trip_data.get("driver_id")
        }

        for driver_id, websocket in self.driver_connections.items():
            if driver_id != trip_data.get("driver_id"):
                try:
                    await websocket.send_json(remove_message)
                except:
                    pass

    def get_stats(self):
        """Get connection statistics."""
        return {
            "connected_drivers": len(self.driver_connections),
            "connected_customers": len(self.customer_connections),
            "active_trip_watchers": len(self.trip_watchers),
            "driver_ids": list(self.driver_connections.keys()),
            "customer_ids": list(self.customer_connections.keys())
        }


# Global instance
trip_manager = TripConnectionManager()
