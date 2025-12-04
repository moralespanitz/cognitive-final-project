"use client";

import { useEffect, useState, useRef } from "react";
import { useAuthStore } from "@/lib/store";

interface Trip {
  id: number;
  status: string;
  pickup_location: { lat: number; lng: number; address: string };
  destination: { lat: number; lng: number; address: string };
  estimated_fare: number;
  customer_id: number;
  vehicle_id?: number;
  driver_id?: number;
  identity_verified?: boolean;
  verification_score?: number;
}

export default function DriverPanelPage() {
  const { user } = useAuthStore();
  const [trips, setTrips] = useState<Trip[]>([]);
  const [activeTrip, setActiveTrip] = useState<Trip | null>(null);
  const [loading, setLoading] = useState(true);
  const [wsConnected, setWsConnected] = useState(false);
  const [newTripAlert, setNewTripAlert] = useState<Trip | null>(null);
  const [driverId, setDriverId] = useState<number | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Fetch driver profile and set status to ON_DUTY
  useEffect(() => {
    const initializeDriver = async () => {
      if (!user) return;

      try {
        const token = localStorage.getItem("access_token");
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

        // Get driver profile
        const response = await fetch(`${apiUrl}/drivers/me`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (response.ok) {
          const driver = await response.json();
          setDriverId(driver.id);

          // Set status to ON_DUTY if not already
          if (driver.status !== "ON_DUTY") {
            await fetch(`${apiUrl}/drivers/${driver.id}/status?driver_status=ON_DUTY`, {
              method: "PATCH",
              headers: { Authorization: `Bearer ${token}` },
            });
            console.log("Driver status set to ON_DUTY");
          }
        }
      } catch (error) {
        console.error("Error initializing driver:", error);
      }
    };

    initializeDriver();
  }, [user]);

  // Connect to WebSocket for real-time trip notifications
  useEffect(() => {
    if (!user || !driverId) return;

    let ws: WebSocket | null = null;
    let reconnectTimeout: NodeJS.Timeout;

    const connect = () => {
      try {
        const wsUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";
        ws = new WebSocket(`${wsUrl}/ws/trips/driver/${driverId}`);

        ws.onopen = () => {
          console.log("🚗 Driver WebSocket connected");
          setWsConnected(true);
        };

        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          console.log("📥 WebSocket message:", data);

          if (data.type === "new_trip") {
            // New trip request received - show alert and add to list
            const newTrip = data.trip;
            setNewTripAlert(newTrip);
            setTrips(prev => {
              // Avoid duplicates
              if (prev.some(t => t.id === newTrip.id)) return prev;
              return [newTrip, ...prev];
            });

            // Play notification sound (optional)
            try {
              new Audio('/notification.mp3').play().catch(() => {});
            } catch {}

            // Clear alert after 5 seconds
            setTimeout(() => setNewTripAlert(null), 5000);
          } else if (data.type === "trip_taken") {
            // Another driver accepted this trip - remove from list
            setTrips(prev => prev.filter(t => t.id !== data.trip_id));
          } else if (data.type === "trip_update" || data.type === "trip_accepted") {
            // Update trip in list and active trip
            const updatedTrip = data.trip;
            setTrips(prev => prev.map(t =>
              t.id === updatedTrip.id ? { ...t, ...updatedTrip } : t
            ));
            // Update active trip if it's the same one
            setActiveTrip(prev => {
              if (prev && prev.id === updatedTrip.id) {
                return { ...prev, ...updatedTrip };
              }
              return prev;
            });
          }
        };

        ws.onclose = () => {
          console.log("🚗 Driver WebSocket disconnected");
          setWsConnected(false);
          // Try to reconnect after 3 seconds
          reconnectTimeout = setTimeout(connect, 3000);
        };

        ws.onerror = () => {
          // Silent error - will trigger onclose which handles reconnection
          setWsConnected(false);
        };

        wsRef.current = ws;
      } catch (err) {
        // Connection failed, retry after delay
        reconnectTimeout = setTimeout(connect, 3000);
      }
    };

    connect();

    return () => {
      clearTimeout(reconnectTimeout);
      if (ws) {
        ws.close();
      }
    };
  }, [user, driverId]);

  // Initial fetch of trips
  useEffect(() => {
    fetchTrips();
  }, []);

  const fetchTrips = async () => {
    try {
      const token = localStorage.getItem("access_token");
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
      const response = await fetch(`${apiUrl}/trips`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setTrips(data);

        // Find any active trip (ACCEPTED, ARRIVED, or IN_PROGRESS)
        // In a real app, we'd filter by driver_id from the backend
        const active = data.find(
          (t: Trip) =>
            t.status === "ACCEPTED" || t.status === "IN_PROGRESS" || t.status === "ARRIVED"
        );
        setActiveTrip(active || null);

        console.log("Trips loaded:", data.length, "Active trip:", active);
      }
    } catch (error) {
      console.error("Error fetching trips:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleAction = async (tripId: number, action: string) => {
    try {
      const token = localStorage.getItem("access_token");
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
      const response = await fetch(`${apiUrl}/trips/${tripId}/${action}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const updatedTrip = await response.json();

        // Update local state immediately
        if (action === "accept") {
          setActiveTrip(updatedTrip);
          setTrips(prev => prev.filter(t => t.id !== tripId));
        } else if (action === "complete" || action === "cancel") {
          setActiveTrip(null);
        } else {
          setActiveTrip(updatedTrip);
        }

        fetchTrips();
      }
    } catch (error) {
      console.error(`Error ${action} trip:`, error);
    }
  };

  const pendingTrips = trips.filter((t) => t.status === "REQUESTED");

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      {/* Connection Status */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">Driver Dashboard</h1>
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-sm text-gray-600">
            {wsConnected ? 'Live - Receiving Requests' : 'Disconnected'}
          </span>
        </div>
      </div>

      {/* New Trip Alert */}
      {newTripAlert && (
        <div className="bg-yellow-400 text-yellow-900 p-4 rounded-lg mb-6 animate-pulse">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-bold text-lg">New Trip Request!</p>
              <p>{newTripAlert.pickup_location.address}</p>
            </div>
            <span className="text-2xl font-bold">
              ${parseFloat(String(newTripAlert.estimated_fare || 0)).toFixed(2)}
            </span>
          </div>
        </div>
      )}

      {/* Active Trip */}
      {activeTrip && (
        <div className="bg-blue-600 text-white p-6 rounded-lg mb-6">
          <div className="flex justify-between items-start mb-4">
            <h2 className="text-xl font-bold">Active Trip #{activeTrip.id}</h2>
            <span className="bg-white text-blue-600 px-3 py-1 rounded-full text-sm font-semibold">
              {activeTrip.status}
            </span>
          </div>

          <div className="grid md:grid-cols-2 gap-4 mb-4">
            <div>
              <p className="text-sm opacity-90">Pickup</p>
              <p className="font-semibold">{activeTrip.pickup_location.address}</p>
            </div>
            <div>
              <p className="text-sm opacity-90">Destination</p>
              <p className="font-semibold">{activeTrip.destination.address}</p>
            </div>
          </div>

          {activeTrip.identity_verified && (
            <div className="bg-green-500 text-white px-3 py-1 rounded inline-block mb-4">
              Customer Verified ({activeTrip.verification_score}%)
            </div>
          )}

          <div className="flex gap-2 flex-wrap">
            {activeTrip.status === "ACCEPTED" && (
              <button
                onClick={() => handleAction(activeTrip.id, "arrive")}
                className="bg-white text-blue-600 px-6 py-2 rounded-lg font-semibold hover:bg-gray-100"
              >
                Arrived at Pickup
              </button>
            )}

            {activeTrip.status === "ARRIVED" && (
              <button
                onClick={() => handleAction(activeTrip.id, "start")}
                className="bg-green-500 text-white px-6 py-2 rounded-lg font-semibold hover:bg-green-600"
              >
                Start Trip
              </button>
            )}

            {activeTrip.status === "IN_PROGRESS" && (
              <button
                onClick={() => handleAction(activeTrip.id, "complete")}
                className="bg-green-500 text-white px-6 py-2 rounded-lg font-semibold hover:bg-green-600"
              >
                Complete Trip
              </button>
            )}

            {(activeTrip.status === "ACCEPTED" || activeTrip.status === "ARRIVED") && (
              <button
                onClick={() => handleAction(activeTrip.id, "cancel")}
                className="bg-red-500 text-white px-6 py-2 rounded-lg font-semibold hover:bg-red-600"
              >
                Cancel
              </button>
            )}
          </div>
        </div>
      )}

      {/* Pending Trip Requests */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b flex justify-between items-center">
          <h2 className="text-xl font-bold">
            Trip Requests ({pendingTrips.length})
          </h2>
          <button
            onClick={fetchTrips}
            className="text-blue-600 hover:text-blue-800 text-sm"
          >
            Refresh
          </button>
        </div>

        {loading ? (
          <div className="p-12 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p>Loading...</p>
          </div>
        ) : pendingTrips.length === 0 ? (
          <div className="p-12 text-center text-gray-500">
            <div className="text-6xl mb-4">🚕</div>
            <p className="text-lg">No pending trip requests</p>
            <p className="text-sm mt-2">
              {wsConnected
                ? "You'll see new requests here in real-time"
                : "Reconnecting to receive requests..."}
            </p>
          </div>
        ) : (
          <div className="divide-y">
            {pendingTrips.map((trip) => (
              <div key={trip.id} className="p-6 hover:bg-gray-50 transition-colors">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="font-semibold text-lg">Trip #{trip.id}</h3>
                    <p className="text-sm text-gray-500">
                      Fare: ${parseFloat(String(trip.estimated_fare || 0)).toFixed(2)}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {trip.identity_verified && (
                      <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs">
                        Verified
                      </span>
                    )}
                    <span className="bg-yellow-100 text-yellow-800 px-3 py-1 rounded-full text-sm">
                      New Request
                    </span>
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-4 mb-4">
                  <div>
                    <p className="text-sm text-gray-600">Pickup</p>
                    <p className="font-medium">{trip.pickup_location.address}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Destination</p>
                    <p className="font-medium">{trip.destination.address}</p>
                  </div>
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => handleAction(trip.id, "accept")}
                    className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 font-semibold"
                  >
                    Accept Trip
                  </button>
                  <button
                    onClick={() => handleAction(trip.id, "cancel")}
                    className="bg-gray-200 text-gray-700 px-6 py-2 rounded-lg hover:bg-gray-300"
                  >
                    Decline
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Trip History */}
      <div className="mt-6 bg-white rounded-lg shadow">
        <div className="p-6 border-b">
          <h2 className="text-xl font-bold">Recent Completed Trips</h2>
        </div>
        <div className="p-6">
          <div className="space-y-3">
            {trips
              .filter((t) => t.status === "COMPLETED")
              .slice(0, 5)
              .map((trip) => (
                <div key={trip.id} className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium">Trip #{trip.id}</p>
                    <p className="text-sm text-gray-500">
                      {trip.pickup_location.address} → {trip.destination.address}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-green-600">
                      ${parseFloat(String(trip.estimated_fare || 0)).toFixed(2)}
                    </p>
                    <p className="text-sm text-gray-500">Completed</p>
                  </div>
                </div>
              ))}
            {trips.filter((t) => t.status === "COMPLETED").length === 0 && (
              <p className="text-center text-gray-500 py-8">No completed trips yet</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
