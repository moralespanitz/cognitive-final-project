"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { facesApi, tripsApi } from "@/lib/api";
import { CameraCapture } from "@/components/camera-capture";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  CheckCircleIcon,
  XCircleIcon,
  ShieldCheckIcon,
  UserIcon,
  MapPinIcon,
  CarIcon,
} from "lucide-react";

type BookingStep = "location" | "verification" | "confirm";

interface VerificationResult {
  is_match: boolean;
  similarity_score: number;
  message: string;
}

export default function BookTaxiPage() {
  const router = useRouter();
  const [step, setStep] = useState<BookingStep>("location");
  const [pickup, setPickup] = useState("");
  const [destination, setDestination] = useState("");
  const [loading, setLoading] = useState(false);
  const [estimatedFare, setEstimatedFare] = useState<number | null>(null);
  const [hasRegisteredFace, setHasRegisteredFace] = useState<boolean | null>(null);
  const [verificationResult, setVerificationResult] = useState<VerificationResult | null>(null);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [checkingFace, setCheckingFace] = useState(true);

  // Check if user has registered face on mount
  useEffect(() => {
    checkFaceRegistration();
  }, []);

  const checkFaceRegistration = async () => {
    try {
      const status = await facesApi.getStatus();
      setHasRegisteredFace(status.has_registered_face);
    } catch (error) {
      console.error("Error checking face status:", error);
      setHasRegisteredFace(false);
    } finally {
      setCheckingFace(false);
    }
  };

  const handleLocationSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!pickup || !destination) return;

    // Calculate estimated fare
    const distance = 5 + Math.random() * 10; // Mock distance
    const fare = 2.0 + distance * 1.5;
    setEstimatedFare(fare);

    // Move to verification step
    setStep("verification");
  };

  const handleCaptureImage = async (imageBase64: string) => {
    setCapturedImage(imageBase64);
    setLoading(true);

    try {
      if (hasRegisteredFace) {
        // Verify against registered face
        const result = await facesApi.verifySelf(imageBase64);
        setVerificationResult(result);
      } else {
        // Register face for first time
        await facesApi.register(imageBase64);
        setVerificationResult({
          is_match: true,
          similarity_score: 100,
          message: "Face registered successfully!",
        });
        setHasRegisteredFace(true);
      }
      setStep("confirm");
    } catch (error) {
      console.error("Verification error:", error);
      setVerificationResult({
        is_match: false,
        similarity_score: 0,
        message: "Verification failed. Please try again.",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSkipVerification = () => {
    setVerificationResult(null);
    setCapturedImage(null);
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
        verification_image: capturedImage || undefined,
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
            step === "verification"
              ? "bg-blue-600 text-white"
              : step === "confirm"
              ? "bg-green-500 text-white"
              : "bg-gray-200 text-gray-500"
          }`}
        >
          {step === "confirm" ? <CheckCircleIcon className="w-5 h-5" /> : "2"}
        </div>
        <span className="text-sm font-medium">Verify</span>

        <div className="w-12 h-0.5 bg-gray-300 mx-2" />

        <div
          className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold ${
            step === "confirm" ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-500"
          }`}
        >
          3
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
        Continue to Verification
      </Button>
    </form>
  );

  const renderVerificationStep = () => (
    <div className="space-y-6">
      <div className="text-center mb-4">
        <ShieldCheckIcon className="w-12 h-12 mx-auto text-blue-500 mb-2" />
        <h2 className="text-xl font-semibold">Identity Verification</h2>
        <p className="text-sm text-muted-foreground">
          {hasRegisteredFace
            ? "Please verify your identity to continue"
            : "Register your face for secure trips"}
        </p>
      </div>

      <CameraCapture
        onCapture={handleCaptureImage}
        title={hasRegisteredFace ? "Verify Identity" : "Register Face"}
        description={
          hasRegisteredFace
            ? "Look at the camera to verify your identity"
            : "Take a photo to register your face for future trips"
        }
        autoStart={true}
      />

      <div className="flex gap-2">
        <Button variant="outline" onClick={() => setStep("location")} className="flex-1">
          Back
        </Button>
        <Button variant="ghost" onClick={handleSkipVerification} className="flex-1">
          Skip Verification
        </Button>
      </div>
    </div>
  );

  const renderConfirmStep = () => (
    <div className="space-y-6">
      {/* Verification Result */}
      {verificationResult && (
        <Card className={verificationResult.is_match ? "border-green-200" : "border-yellow-200"}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              {verificationResult.is_match ? (
                <CheckCircleIcon className="w-10 h-10 text-green-500" />
              ) : (
                <XCircleIcon className="w-10 h-10 text-yellow-500" />
              )}
              <div>
                <p className="font-semibold">
                  {verificationResult.is_match ? "Identity Verified" : "Verification Incomplete"}
                </p>
                <p className="text-sm text-muted-foreground">{verificationResult.message}</p>
                {verificationResult.similarity_score > 0 && (
                  <Badge variant="outline" className="mt-1">
                    Confidence: {verificationResult.similarity_score}%
                  </Badge>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {!verificationResult && (
        <Card className="border-gray-200">
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <UserIcon className="w-10 h-10 text-gray-400" />
              <div>
                <p className="font-semibold">Verification Skipped</p>
                <p className="text-sm text-muted-foreground">
                  You can still book, but verification is recommended for safety.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

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
        <Button variant="outline" onClick={() => setStep("verification")} className="flex-1">
          Back
        </Button>
        <Button onClick={handleBookTaxi} disabled={loading} className="flex-1">
          {loading ? "Requesting..." : "Confirm Booking"}
        </Button>
      </div>
    </div>
  );

  if (checkingFace) {
    return (
      <div className="container mx-auto p-6 max-w-2xl">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4" />
            <p className="text-muted-foreground">Loading...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 max-w-2xl">
      <h1 className="text-3xl font-bold mb-6 text-center">Book a Taxi</h1>

      {renderStepIndicator()}

      <div className="bg-white p-8 rounded-lg shadow">
        {step === "location" && renderLocationStep()}
        {step === "verification" && renderVerificationStep()}
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
              Verify your identity with facial recognition
            </li>
            <li className="flex items-center gap-2">
              <span className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-semibold">
                3
              </span>
              Confirm your booking and track your driver
            </li>
            <li className="flex items-center gap-2">
              <span className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-semibold">
                4
              </span>
              Enjoy a safe ride with real-time monitoring!
            </li>
          </ol>
        </div>
      )}
    </div>
  );
}
