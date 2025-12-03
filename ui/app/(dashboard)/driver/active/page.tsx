"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  MapPinIcon,
  CheckCircleIcon,
  CarIcon,
  ArrowRightIcon,
} from "lucide-react";

interface Trip {
  id: number;
  status: string;
  pickup_location: { lat: number; lng: number; address: string };
  destination: { lat: number; lng: number; address: string };
  estimated_fare: number;
  customer_id: number;
  identity_verified?: boolean;
  verification_score?: number;
}

export default function DriverActiveTripPage() {
  const router = useRouter();
  const [trip, setTrip] = useState<Trip | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    fetchTrip();
    const interval = setInterval(fetchTrip, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchTrip = async () => {
    try {
      const token = localStorage.getItem("access_token");
      const response = await fetch("http://localhost:8000/api/v1/trips", {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        const active = data.find(
          (t: Trip) =>
            t.status === "ACCEPTED" ||
            t.status === "IN_PROGRESS" ||
            t.status === "ARRIVED"
        );
        setTrip(active || null);
      }
    } catch (error) {
      console.error("Error:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleAction = async (action: string) => {
    if (!trip) return;
    setActionLoading(true);

    try {
      const token = localStorage.getItem("access_token");
      const response = await fetch(
        `http://localhost:8000/api/v1/trips/${trip.id}/${action}`,
        {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (response.ok) {
        if (action === "complete" || action === "cancel") {
          setTrip(null);
        } else {
          fetchTrip();
        }
      }
    } catch (error) {
      console.error("Error:", error);
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (!trip) {
    return (
      <div className="max-w-md mx-auto p-6 text-center">
        <CarIcon className="w-20 h-20 mx-auto text-gray-300 mb-4" />
        <h2 className="text-2xl font-bold text-gray-600 mb-2">No Active Trip</h2>
        <p className="text-gray-500 mb-6">Go to Driver Panel to accept a trip</p>
        <Button onClick={() => router.push("/driver")} size="lg">
          Go to Driver Panel
        </Button>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto p-4">
      {/* Trip Header */}
      <div className="text-center mb-6">
        <h1 className="text-2xl font-bold">Trip #{trip.id}</h1>
        {trip.identity_verified && (
          <span className="inline-flex items-center text-green-600 text-sm mt-1">
            <CheckCircleIcon className="w-4 h-4 mr-1" />
            Customer Verified
          </span>
        )}
      </div>

      {/* Route Card */}
      <div className="bg-white rounded-xl shadow-lg p-5 mb-6">
        {/* Pickup */}
        <div className="flex items-start gap-3 mb-4">
          <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center shrink-0">
            <MapPinIcon className="w-5 h-5 text-green-600" />
          </div>
          <div>
            <p className="text-xs text-gray-500 uppercase">Pickup</p>
            <p className="font-semibold">{trip.pickup_location.address}</p>
          </div>
        </div>

        {/* Arrow */}
        <div className="flex justify-center my-2">
          <ArrowRightIcon className="w-5 h-5 text-gray-400 rotate-90" />
        </div>

        {/* Destination */}
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center shrink-0">
            <MapPinIcon className="w-5 h-5 text-red-600" />
          </div>
          <div>
            <p className="text-xs text-gray-500 uppercase">Destination</p>
            <p className="font-semibold">{trip.destination.address}</p>
          </div>
        </div>

        {/* Fare */}
        <div className="mt-5 pt-4 border-t text-center">
          <p className="text-sm text-gray-500">Fare</p>
          <p className="text-3xl font-bold text-green-600">
            ${parseFloat(String(trip.estimated_fare || 0)).toFixed(2)}
          </p>
        </div>
      </div>

      {/* Action Buttons - Simple and Clear */}
      <div className="space-y-3">
        {trip.status === "ACCEPTED" && (
          <Button
            className="w-full h-16 text-xl bg-yellow-500 hover:bg-yellow-600"
            onClick={() => handleAction("arrive")}
            disabled={actionLoading}
          >
            {actionLoading ? "..." : "I Have Arrived"}
          </Button>
        )}

        {trip.status === "ARRIVED" && (
          <Button
            className="w-full h-16 text-xl bg-blue-600 hover:bg-blue-700"
            onClick={() => handleAction("start")}
            disabled={actionLoading}
          >
            {actionLoading ? "..." : "Start Trip"}
          </Button>
        )}

        {trip.status === "IN_PROGRESS" && (
          <Button
            className="w-full h-16 text-xl bg-green-600 hover:bg-green-700"
            onClick={() => handleAction("complete")}
            disabled={actionLoading}
          >
            {actionLoading ? "..." : "Complete Trip"}
          </Button>
        )}

        {trip.status !== "IN_PROGRESS" && (
          <Button
            variant="outline"
            className="w-full h-12 text-red-600 border-red-300 hover:bg-red-50"
            onClick={() => handleAction("cancel")}
            disabled={actionLoading}
          >
            Cancel Trip
          </Button>
        )}
      </div>

      {/* Status Indicator */}
      <div className="mt-6 text-center">
        <p className="text-sm text-gray-500">
          Status: <span className="font-semibold">{trip.status.replace("_", " ")}</span>
        </p>
      </div>
    </div>
  );
}
