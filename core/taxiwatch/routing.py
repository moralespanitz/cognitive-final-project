"""
WebSocket URL routing for TaxiWatch project.
"""

from django.urls import path

# WebSocket URL patterns
# Will be populated as we add consumers for tracking, alerts, and video
websocket_urlpatterns = [
    # path('ws/tracking/', TrackingConsumer.as_asgi()),
    # path('ws/alerts/', AlertsConsumer.as_asgi()),
    # path('ws/video/<int:vehicle_id>/', VideoConsumer.as_asgi()),
]
