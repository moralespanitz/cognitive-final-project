'use client';

import { useEffect, useState, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { tripsApi } from '@/lib/api';
import { useAuthStore } from '@/lib/store';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  MapPinIcon,
  CarIcon,
  CheckCircleIcon,
  XCircleIcon,
  PhoneIcon,
  UserIcon,
  ShieldCheckIcon,
  ArrowLeftIcon,
  RefreshCwIcon,
  VideoIcon,
  WifiIcon,
} from 'lucide-react';

interface Trip {
  id: number;
  customer_id: number;
  vehicle_id: number;
  driver_id: number;
  pickup_location: { lat: number; lng: number; address: string };
  destination: { lat: number; lng: number; address: string };
  status: string;
  estimated_fare: number;
  fare: number;
  distance: number;
  duration: number;
  identity_verified: boolean;
  verification_score: number | null;
  created_at: string;
  start_time: string | null;
  end_time: string | null;
}

const statusSteps = [
  { key: 'REQUESTED', label: 'Requested', description: 'Looking for a driver...' },
  { key: 'ACCEPTED', label: 'Driver Assigned', description: 'Driver is on the way' },
  { key: 'ARRIVED', label: 'Driver Arrived', description: 'Your driver has arrived' },
  { key: 'IN_PROGRESS', label: 'In Progress', description: 'On your way to destination' },
  { key: 'COMPLETED', label: 'Completed', description: 'Trip completed' },
];

export default function TripTrackingPage() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuthStore();
  const [trip, setTrip] = useState<Trip | null>(null);
  const [loading, setLoading] = useState(true);
  const [spinning, setSpinning] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');

  // Live camera state
  const [showCamera, setShowCamera] = useState(false);
  const [cameraFrame, setCameraFrame] = useState<string | null>(null);
  const [cameraConnected, setCameraConnected] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const cameraWsRef = useRef<WebSocket | null>(null);

  const tripId = Number(params.id);

  // Connect to customer WebSocket for real-time trip updates
  useEffect(() => {
    if (!user?.id) return;

    let ws: WebSocket | null = null;
    let reconnectTimeout: NodeJS.Timeout;

    const connect = () => {
      try {
        const wsHost = process.env.NEXT_PUBLIC_API_URL?.replace('http://', '').replace('/api/v1', '') || 'localhost:8000';
        ws = new WebSocket(`ws://${wsHost}/ws/trips/customer/${user.id}`);

        ws.onopen = () => {
          console.log("👤 Customer WebSocket connected");
          setWsConnected(true);
        };

        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          console.log("📥 Trip update:", data);

          // Only process updates for this trip
          if (data.trip?.id !== tripId) return;

          if (data.type === "trip_accepted") {
            setTrip(prev => prev ? { ...prev, ...data.trip, status: 'ACCEPTED' } : null);
            setStatusMessage("Driver accepted your trip!");
          } else if (data.type === "driver_arrived") {
            setTrip(prev => prev ? { ...prev, ...data.trip, status: 'ARRIVED' } : null);
            setStatusMessage("Your driver has arrived!");
          } else if (data.type === "trip_started") {
            setTrip(prev => prev ? { ...prev, ...data.trip, status: 'IN_PROGRESS' } : null);
            setStatusMessage("Trip started! Enjoy your ride.");
            // Automatically show camera when trip starts
            setShowCamera(true);
          } else if (data.type === "trip_completed") {
            setTrip(prev => prev ? { ...prev, ...data.trip, status: 'COMPLETED' } : null);
            setStatusMessage("Trip completed! Thank you for riding.");
            setShowCamera(false);
          }

          // Clear status message after 5 seconds
          setTimeout(() => setStatusMessage(''), 5000);
        };

        ws.onclose = () => {
          console.log("👤 Customer WebSocket disconnected");
          setWsConnected(false);
          // Reconnect after 3 seconds
          reconnectTimeout = setTimeout(connect, 3000);
        };

        ws.onerror = () => {
          // Silent error - onclose handles reconnection
          setWsConnected(false);
        };

        wsRef.current = ws;
      } catch (err) {
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
  }, [user?.id, tripId]);

  // Connect to video WebSocket when camera is shown
  useEffect(() => {
    if (!showCamera || !trip?.vehicle_id) return;

    // Connect to video stream for this vehicle
    const routeId = `taxi-${trip.vehicle_id.toString().padStart(2, '0')}`;
    const wsHost = process.env.NEXT_PUBLIC_API_URL?.replace('http://', '').replace('/api/v1', '') || 'localhost:8000';
    const ws = new WebSocket(`ws://${wsHost}/ws/video/${routeId}`);

    ws.onopen = () => {
      console.log("📹 Camera WebSocket connected for", routeId);
      setCameraConnected(true);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "frame" && data.image) {
        setCameraFrame(`data:image/jpeg;base64,${data.image}`);
      }
    };

    ws.onclose = () => {
      console.log("📹 Camera WebSocket disconnected");
      setCameraConnected(false);
    };

    cameraWsRef.current = ws;

    return () => {
      ws.close();
    };
  }, [showCamera, trip?.vehicle_id]);

  useEffect(() => {
    loadTrip();
  }, [tripId]);

  // Auto-refresh for active trips (fallback if WebSocket fails)
  useEffect(() => {
    const interval = setInterval(() => {
      if (trip && ['REQUESTED', 'ACCEPTED', 'ARRIVED', 'IN_PROGRESS'].includes(trip.status)) {
        loadTrip(true);
      }
    }, 10000); // Reduced frequency since we have WebSocket
    return () => clearInterval(interval);
  }, [trip?.status]);

  const loadTrip = async (silent = false) => {
    try {
      if (!silent) setLoading(true);
      setSpinning(true);
      const data = await tripsApi.getById(tripId);
      setTrip(data);

      // Auto-show camera if trip is in progress
      if (data.status === 'IN_PROGRESS') {
        setShowCamera(true);
      }
    } catch (error) {
      console.error('Error loading trip:', error);
    } finally {
      setLoading(false);
      setSpinning(false);
    }
  };

  const handleCancel = async () => {
    if (!confirm('Are you sure you want to cancel this trip?')) return;
    try {
      await tripsApi.cancel(tripId);
      loadTrip();
    } catch (error) {
      console.error('Error cancelling trip:', error);
      alert('Failed to cancel trip');
    }
  };

  const formatDate = (dateString: string) => new Date(dateString).toLocaleString();

  const getCurrentStepIndex = () => {
    if (!trip) return 0;
    if (trip.status === 'CANCELLED') return -1;
    return statusSteps.findIndex(s => s.key === trip.status);
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6 max-w-2xl">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      </div>
    );
  }

  if (!trip) {
    return (
      <div className="container mx-auto p-6 max-w-2xl">
        <Card>
          <CardContent className="py-16 text-center">
            <XCircleIcon className="w-16 h-16 mx-auto text-gray-300 mb-4" />
            <h3 className="text-lg font-semibold text-gray-600">Trip Not Found</h3>
            <Button onClick={() => router.push('/trips')} className="mt-4">View My Trips</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const currentStep = getCurrentStepIndex();
  const isActive = ['REQUESTED', 'ACCEPTED', 'ARRIVED', 'IN_PROGRESS'].includes(trip.status);
  const isCancelled = trip.status === 'CANCELLED';
  const canShowCamera = ['ACCEPTED', 'ARRIVED', 'IN_PROGRESS'].includes(trip.status);

  return (
    <div className="container mx-auto p-6 max-w-2xl">
      <div className="flex items-center justify-between mb-6">
        <Button variant="ghost" onClick={() => router.push('/trips')}>
          <ArrowLeftIcon className="w-4 h-4 mr-2" />
          Back to Trips
        </Button>
        <div className="flex items-center gap-2">
          {wsConnected && (
            <Badge variant="outline" className="text-green-600 border-green-300">
              <WifiIcon className="w-3 h-3 mr-1" />
              Live
            </Badge>
          )}
          <Button variant="outline" size="sm" onClick={() => loadTrip()} disabled={spinning}>
            <RefreshCwIcon className={'w-4 h-4 mr-2 ' + (spinning ? 'animate-spin' : '')} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Real-time status message */}
      {statusMessage && (
        <div className="bg-blue-500 text-white p-4 rounded-lg mb-6 animate-pulse">
          <p className="font-semibold text-center">{statusMessage}</p>
        </div>
      )}

      <Card className="mb-6">
        <CardHeader>
          <div className="flex justify-between items-start">
            <div>
              <CardTitle className="text-2xl">Trip #{trip.id}</CardTitle>
              <p className="text-sm text-muted-foreground mt-1">{formatDate(trip.created_at)}</p>
            </div>
            <div className="text-right">
              {trip.identity_verified && (
                <Badge variant="outline" className="text-green-600 border-green-300 mb-2">
                  <ShieldCheckIcon className="w-3 h-3 mr-1" />
                  Verified ({trip.verification_score}%)
                </Badge>
              )}
              <p className="text-2xl font-bold text-green-600">
                ${parseFloat(String(trip.fare || trip.estimated_fare || 0)).toFixed(2)}
              </p>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {!isCancelled && (
            <div className="mb-8">
              {statusSteps.map((step, index) => {
                const isCompleted = index < currentStep;
                const isCurrent = index === currentStep;
                return (
                  <div key={step.key} className="flex items-start mb-4 last:mb-0">
                    <div className="flex flex-col items-center mr-4">
                      <div className={'w-8 h-8 rounded-full flex items-center justify-center ' + (
                        isCompleted ? 'bg-green-500 text-white' : isCurrent ? 'bg-blue-500 text-white animate-pulse' : 'bg-gray-200'
                      )}>
                        {isCompleted ? <CheckCircleIcon className="w-5 h-5" /> : index + 1}
                      </div>
                      {index < statusSteps.length - 1 && (
                        <div className={'w-0.5 h-8 ' + (isCompleted ? 'bg-green-500' : 'bg-gray-200')} />
                      )}
                    </div>
                    <div className="flex-1 pt-1">
                      <p className={'font-semibold ' + (isCurrent ? 'text-blue-600' : isCompleted ? 'text-green-600' : 'text-gray-400')}>
                        {step.label}
                      </p>
                      {isCurrent && <p className="text-sm text-muted-foreground">{step.description}</p>}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {isCancelled && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <div className="flex items-center gap-3">
                <XCircleIcon className="w-6 h-6 text-red-500" />
                <p className="font-semibold text-red-700">Trip Cancelled</p>
              </div>
            </div>
          )}

          <div className="space-y-4">
            <div className="flex items-start gap-3 p-4 bg-gray-50 rounded-lg">
              <MapPinIcon className="w-5 h-5 text-green-500 mt-0.5" />
              <div>
                <p className="text-sm text-muted-foreground">Pickup</p>
                <p className="font-medium">{trip.pickup_location.address}</p>
              </div>
            </div>
            <div className="flex items-start gap-3 p-4 bg-gray-50 rounded-lg">
              <MapPinIcon className="w-5 h-5 text-red-500 mt-0.5" />
              <div>
                <p className="text-sm text-muted-foreground">Destination</p>
                <p className="font-medium">{trip.destination.address}</p>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4 pt-4 border-t">
              <div className="text-center">
                <p className="text-2xl font-bold">{parseFloat(String(trip.distance || 0)).toFixed(1)}</p>
                <p className="text-xs text-muted-foreground">km</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold">{trip.duration || '-'}</p>
                <p className="text-xs text-muted-foreground">min</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">${parseFloat(String(trip.fare || trip.estimated_fare || 0)).toFixed(2)}</p>
                <p className="text-xs text-muted-foreground">fare</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Live Camera Feed */}
      {canShowCamera && (
        <Card className="mb-6">
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle className="flex items-center gap-2">
                <VideoIcon className="w-5 h-5" />
                Live Camera Feed
              </CardTitle>
              <div className="flex items-center gap-2">
                {cameraConnected && (
                  <Badge variant="outline" className="text-green-600 border-green-300">
                    <div className="w-2 h-2 bg-green-500 rounded-full mr-1 animate-pulse" />
                    Live
                  </Badge>
                )}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowCamera(!showCamera)}
                >
                  {showCamera ? 'Hide' : 'Show'} Camera
                </Button>
              </div>
            </div>
          </CardHeader>
          {showCamera && (
            <CardContent>
              <div className="aspect-video bg-gray-900 rounded-lg overflow-hidden relative">
                {cameraFrame ? (
                  <img
                    src={cameraFrame}
                    alt="Live camera feed"
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-white">
                    <div className="text-center">
                      <VideoIcon className="w-12 h-12 mx-auto mb-2 opacity-50" />
                      <p className="text-sm opacity-75">
                        {cameraConnected ? 'Waiting for video feed...' : 'Connecting to camera...'}
                      </p>
                    </div>
                  </div>
                )}
                {/* Live indicator overlay */}
                {cameraConnected && cameraFrame && (
                  <div className="absolute top-3 left-3 bg-red-600 text-white px-2 py-1 rounded text-xs font-bold flex items-center gap-1">
                    <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
                    LIVE
                  </div>
                )}
              </div>
              <p className="text-xs text-muted-foreground mt-2 text-center">
                Real-time video from vehicle #{trip.vehicle_id}
              </p>
            </CardContent>
          )}
        </Card>
      )}

      {trip.driver_id && !isCancelled && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <UserIcon className="w-5 h-5" />
              Your Driver
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
                <UserIcon className="w-8 h-8 text-blue-600" />
              </div>
              <div className="flex-1">
                <p className="font-semibold">Driver #{trip.driver_id}</p>
                <p className="text-sm text-muted-foreground">Vehicle #{trip.vehicle_id}</p>
              </div>
              <Button variant="outline" size="sm" disabled>
                <PhoneIcon className="w-4 h-4 mr-2" />
                Call
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="flex gap-4">
        {isActive && ['REQUESTED', 'ACCEPTED'].includes(trip.status) && (
          <Button variant="destructive" className="flex-1" onClick={handleCancel}>
            <XCircleIcon className="w-4 h-4 mr-2" />
            Cancel Trip
          </Button>
        )}
        {trip.status === 'COMPLETED' && (
          <Button className="flex-1" onClick={() => router.push('/book')}>
            <CarIcon className="w-4 h-4 mr-2" />
            Book Another Ride
          </Button>
        )}
      </div>
    </div>
  );
}
