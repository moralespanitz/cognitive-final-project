'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { vehiclesApi, trackingApi } from '@/lib/api';
import { ArrowLeftIcon, MapPinIcon, ActivityIcon, ClockIcon } from 'lucide-react';

const VehicleMap = dynamic(() => import('@/components/map'), { ssr: false });

interface VehicleDetailProps {
  params: {
    id: string;
  };
}

export default function VehicleDetailPage({ params }: VehicleDetailProps) {
  const router = useRouter();
  const [vehicle, setVehicle] = useState<any>(null);
  const [location, setLocation] = useState<any>(null);
  const [locationHistory, setLocationHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadVehicleData();
  }, [params.id]);

  const loadVehicleData = async () => {
    try {
      const vehicleData = await vehiclesApi.getById(parseInt(params.id));
      setVehicle(vehicleData);

      try {
        const liveLocations = await trackingApi.getLiveLocations();
        const currentLocation = liveLocations.find(
          (loc: any) => loc.vehicle_id === parseInt(params.id)
        );
        if (currentLocation) {
          setLocation(currentLocation);
        }
      } catch (err) {
        console.log('No live location found');
      }

      try {
        const history = await trackingApi.getVehicleHistory(parseInt(params.id));
        setLocationHistory(history.slice(0, 10));
      } catch (err) {
        console.log('No location history found');
      }
    } catch (error) {
      console.error('Failed to load vehicle:', error);
      alert('Vehicle not found');
      router.push('/vehicles');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      ACTIVE: 'text-green-600 bg-green-50',
      MAINTENANCE: 'text-yellow-600 bg-yellow-50',
      OUT_OF_SERVICE: 'text-red-600 bg-red-50'
    };
    return colors[status] || 'text-gray-600 bg-gray-50';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <p className="text-gray-600">Loading vehicle details...</p>
      </div>
    );
  }

  if (!vehicle) {
    return (
      <div className="flex items-center justify-center h-96">
        <p className="text-gray-600">Vehicle not found</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" onClick={() => router.push('/vehicles')}>
          <ArrowLeftIcon className="h-4 w-4 mr-2" />
          Back
        </Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold text-gray-900">{vehicle.license_plate}</h1>
          <p className="text-gray-600">
            {vehicle.make} {vehicle.model} ({vehicle.year})
          </p>
        </div>
        <span className={`px-4 py-2 rounded-full text-sm font-medium ${getStatusColor(vehicle.status)}`}>
          {vehicle.status.replace('_', ' ')}
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {location && (
            <Card>
              <CardHeader>
                <CardTitle>Current Location</CardTitle>
                <CardDescription>Real-time position on map</CardDescription>
              </CardHeader>
              <CardContent>
                <VehicleMap
                  height="400px"
                  center={[location.longitude, location.latitude]}
                  zoom={14}
                  vehicles={[{
                    id: vehicle.id,
                    license_plate: vehicle.license_plate,
                    latitude: location.latitude,
                    longitude: location.longitude,
                    status: vehicle.status
                  }]}
                />
                <div className="mt-4 grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-600">Speed</p>
                    <p className="text-lg font-semibold">
                      {location.speed?.toFixed(1) || '0'} km/h
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Heading</p>
                    <p className="text-lg font-semibold">
                      {location.heading?.toFixed(0) || '0'}°
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Location History</CardTitle>
              <CardDescription>Recent GPS updates</CardDescription>
            </CardHeader>
            <CardContent>
              {locationHistory.length === 0 ? (
                <p className="text-center text-gray-500 py-8">No location history available</p>
              ) : (
                <div className="space-y-3">
                  {locationHistory.map((loc: any, index: number) => (
                    <div key={loc.id || index} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                      <MapPinIcon className="h-5 w-5 text-blue-600 mt-0.5" />
                      <div className="flex-1">
                        <p className="text-sm font-medium">
                          {loc.latitude.toFixed(6)}, {loc.longitude.toFixed(6)}
                        </p>
                        <p className="text-xs text-gray-500">
                          Speed: {loc.speed?.toFixed(1) || '0'} km/h •
                          Heading: {loc.heading?.toFixed(0) || '0'}°
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-gray-500">
                          {new Date(loc.timestamp).toLocaleTimeString()}
                        </p>
                        <p className="text-xs text-gray-400">
                          {new Date(loc.timestamp).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Vehicle Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm text-gray-600">Make & Model</p>
                <p className="font-medium">{vehicle.make} {vehicle.model}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Year</p>
                <p className="font-medium">{vehicle.year}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Color</p>
                <p className="font-medium">{vehicle.color}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">VIN</p>
                <p className="font-medium text-xs break-all">{vehicle.vin}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Capacity</p>
                <p className="font-medium">{vehicle.capacity} passengers</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">License Plate</p>
                <p className="font-medium">{vehicle.license_plate}</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Quick Stats</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-50 rounded-lg">
                  <ActivityIcon className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Trips Today</p>
                  <p className="font-semibold">0</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-50 rounded-lg">
                  <ClockIcon className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Hours Active</p>
                  <p className="font-semibold">0h</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-50 rounded-lg">
                  <MapPinIcon className="h-5 w-5 text-purple-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Distance Traveled</p>
                  <p className="font-semibold">0 km</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="space-y-2">
            <Button className="w-full" variant="outline">
              Edit Vehicle
            </Button>
            <Button className="w-full text-red-600" variant="outline">
              Delete Vehicle
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
