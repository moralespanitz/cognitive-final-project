"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { tripsApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  CheckCircleIcon,
  MapPinIcon,
  CarIcon,
} from "lucide-react";

type BookingStep = "location" | "confirm";

export default function BookTaxiPage() {
  const router = useRouter();
  const [step, setStep] = useState<BookingStep>("location");
  const [pickup, setPickup] = useState("");
  const [destination, setDestination] = useState("");
  const [loading, setLoading] = useState(false);
  const [estimatedFare, setEstimatedFare] = useState<number | null>(null);

  const handleLocationSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!pickup || !destination) return;

    // Calculate estimated fare
    const distance = 5 + Math.random() * 10; // Mock distance
    const fare = 2.0 + distance * 1.5;
    setEstimatedFare(fare);

    // Move directly to confirm step
    setStep("confirm");
  };

  const handleBookTaxi = async () => {
    setLoading(true);

    try {
      const pickupLoc = {
        lat: 40.7128 + Math.random() * 0.01,
        lng: -74.006 + Math.random() * 0.01,
        address: pickup,
      };

      const destLoc = {
        lat: 40.7589 + Math.random() * 0.01,
        lng: -73.9851 + Math.random() * 0.01,
        address: destination,
      };

      const trip = await tripsApi.request({
        pickup_location: pickupLoc,
        destination: destLoc,
      });

      router.push(`/trip/${trip.id}`);
    } catch (error: any) {
      console.error("Error requesting taxi:", error);
      const message = error.response?.data?.detail || "Failed to request taxi. Please try again.";
      alert(message);
    } finally {
      setLoading(false);
    }
  };

  const renderStepIndicator = () => (
    <div className="flex items-center justify-center mb-8">
      <div className="flex items-center gap-2">
        <div
          className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold ${
            step === "location"
              ? "bg-blue-600 text-white"
              : "bg-green-500 text-white"
          }`}
        >
          {step !== "location" ? <CheckCircleIcon className="w-5 h-5" /> : "1"}
        </div>
        <span className="text-sm font-medium">Location</span>

        <div className="w-12 h-0.5 bg-gray-300 mx-2" />

        <div
          className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold ${
            step === "confirm" ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-500"
          }`}
        >
          2
        </div>
        <span className="text-sm font-medium">Confirm</span>
      </div>
    </div>
  );

  const renderLocationStep = () => (
    <form onSubmit={handleLocationSubmit} className="space-y-6">
      <div>
        <label className="block text-sm font-medium mb-2 flex items-center gap-2">
          <MapPinIcon className="w-4 h-4 text-green-500" />
          Pickup Location
        </label>
        <input
          type="text"
          value={pickup}
          onChange={(e) => setPickup(e.target.value)}
          placeholder="Enter pickup address"
          required
          className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-2 flex items-center gap-2">
          <MapPinIcon className="w-4 h-4 text-red-500" />
          Destination
        </label>
        <input
          type="text"
          value={destination}
          onChange={(e) => setDestination(e.target.value)}
          placeholder="Enter destination"
          required
          className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <Button type="submit" className="w-full" size="lg">
        Continue to Confirm
      </Button>
    </form>
  );

  const renderConfirmStep = () => (
    <div className="space-y-6">
      {/* Trip Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CarIcon className="w-5 h-5" />
            Trip Summary
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-start gap-3">
            <MapPinIcon className="w-5 h-5 text-green-500 mt-0.5" />
            <div>
              <p className="text-sm text-muted-foreground">Pickup</p>
              <p className="font-medium">{pickup}</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <MapPinIcon className="w-5 h-5 text-red-500 mt-0.5" />
            <div>
              <p className="text-sm text-muted-foreground">Destination</p>
              <p className="font-medium">{destination}</p>
            </div>
          </div>
          {estimatedFare && (
            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">Estimated Fare</p>
              <p className="text-2xl font-bold text-blue-600">${estimatedFare.toFixed(2)}</p>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="flex gap-2">
        <Button variant="outline" onClick={() => setStep("location")} className="flex-1">
          Back
        </Button>
        <Button onClick={handleBookTaxi} disabled={loading} className="flex-1">
          {loading ? "Requesting..." : "Confirm Booking"}
        </Button>
      </div>
    </div>
  );

  return (
    <div className="container mx-auto p-6 max-w-2xl">
      <h1 className="text-3xl font-bold mb-6 text-center">Book a Taxi</h1>

      {renderStepIndicator()}

      <div className="bg-white p-8 rounded-lg shadow">
        {step === "location" && renderLocationStep()}
        {step === "confirm" && renderConfirmStep()}
      </div>

      {step === "location" && (
        <div className="mt-8 bg-gray-50 p-6 rounded-lg">
          <h2 className="font-semibold mb-4">How it works</h2>
          <ol className="space-y-2 text-sm text-gray-600">
            <li className="flex items-center gap-2">
              <span className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-semibold">
                1
              </span>
              Enter your pickup location and destination
            </li>
            <li className="flex items-center gap-2">
              <span className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-semibold">
                2
              </span>
              Confirm your booking and track your driver
            </li>
            <li className="flex items-center gap-2">
              <span className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-semibold">
                3
              </span>
              Enjoy a safe ride with real-time monitoring!
            </li>
          </ol>
        </div>
      )}
    </div>
  );
}
