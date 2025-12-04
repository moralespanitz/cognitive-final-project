'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { tripsApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  MapPinIcon,
  ClockIcon,
  CarIcon,
  CheckCircleIcon,
  XCircleIcon,
  NavigationIcon,
  DollarSignIcon,
  ShieldCheckIcon,
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

const statusConfig: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
  REQUESTED: { label: 'Requested', color: 'bg-yellow-100 text-yellow-800', icon: <ClockIcon className="w-4 h-4" /> },
  ACCEPTED: { label: 'Driver Assigned', color: 'bg-blue-100 text-blue-800', icon: <CarIcon className="w-4 h-4" /> },
  ARRIVED: { label: 'Driver Arrived', color: 'bg-purple-100 text-purple-800', icon: <NavigationIcon className="w-4 h-4" /> },
  IN_PROGRESS: { label: 'In Progress', color: 'bg-green-100 text-green-800', icon: <NavigationIcon className="w-4 h-4" /> },
  COMPLETED: { label: 'Completed', color: 'bg-gray-100 text-gray-800', icon: <CheckCircleIcon className="w-4 h-4" /> },
  CANCELLED: { label: 'Cancelled', color: 'bg-red-100 text-red-800', icon: <XCircleIcon className="w-4 h-4" /> },
};

export default function MyTripsPage() {
  const router = useRouter();
  const [trips, setTrips] = useState<Trip[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    loadTrips();
  }, []);

  const loadTrips = async () => {
    try {
      setLoading(true);
      const data = await tripsApi.getAll({});
      setTrips(data);
    } catch (error) {
      console.error('Error loading trips:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelTrip = async (tripId: number) => {
    if (!confirm('Are you sure you want to cancel this trip?')) return;

    try {
      await tripsApi.cancel(tripId);
      loadTrips();
    } catch (error) {
      console.error('Error cancelling trip:', error);
      alert('Failed to cancel trip');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const filteredTrips = filter === 'all'
    ? trips
    : trips.filter(t => t.status === filter);

  const activeTrips = trips.filter(t =>
    ['REQUESTED', 'ACCEPTED', 'ARRIVED', 'IN_PROGRESS'].includes(t.status)
  );

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">My Trips</h1>
          <p className="text-muted-foreground">View and manage your taxi rides</p>
        </div>
        <Button onClick={() => router.push('/book')}>
          <CarIcon className="w-4 h-4 mr-2" />
          Book New Taxi
        </Button>
      </div>

      {/* Active Trip Alert */}
      {activeTrips.length > 0 && (
        <Card className="mb-6 border-blue-200 bg-blue-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-100 rounded-full">
                <CarIcon className="w-6 h-6 text-blue-600" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold">You have an active trip</h3>
                <p className="text-sm text-muted-foreground">
                  Trip #{activeTrips[0].id} - {statusConfig[activeTrips[0].status]?.label}
                </p>
              </div>
              <Button onClick={() => router.push(`/trip/${activeTrips[0].id}`)}>
                Track Trip
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filter Tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        {['all', 'REQUESTED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED'].map((status) => (
          <Button
            key={status}
            variant={filter === status ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilter(status)}
          >
            {status === 'all' ? 'All Trips' : statusConfig[status]?.label || status}
          </Button>
        ))}
      </div>

      {/* Trip List */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      ) : filteredTrips.length === 0 ? (
        <Card>
          <CardContent className="py-16 text-center">
            <CarIcon className="w-16 h-16 mx-auto text-gray-300 mb-4" />
            <h3 className="text-lg font-semibold text-gray-600">No Trips Found</h3>
            <p className="text-muted-foreground mb-4">
              {filter === 'all'
                ? "You haven't taken any trips yet."
                : `No ${statusConfig[filter]?.label.toLowerCase()} trips.`}
            </p>
            <Button onClick={() => router.push('/book')}>Book Your First Ride</Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredTrips.map((trip) => {
            const status = statusConfig[trip.status] || statusConfig.REQUESTED;
            return (
              <Card key={trip.id} className="hover:shadow-md transition-shadow">
                <CardContent className="pt-6">
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex items-center gap-3">
                      <div className="text-lg font-semibold">Trip #{trip.id}</div>
                      <Badge className={status.color}>
                        {status.icon}
                        <span className="ml-1">{status.label}</span>
                      </Badge>
                      {trip.identity_verified && (
                        <Badge variant="outline" className="text-green-600 border-green-300">
                          <ShieldCheckIcon className="w-3 h-3 mr-1" />
                          Verified
                        </Badge>
                      )}
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-green-600">
                        ${parseFloat(String(trip.fare || trip.estimated_fare || '0')).toFixed(2)}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {trip.fare && parseFloat(String(trip.fare)) > 0 ? 'Final fare' : 'Estimated'}
                      </p>
                    </div>                  </div>

                  <div className="grid md:grid-cols-2 gap-4 mb-4">
                    <div className="flex items-start gap-2">
                      <MapPinIcon className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-xs text-muted-foreground">Pickup</p>
                        <p className="font-medium">{trip.pickup_location.address}</p>
                      </div>
                    </div>
                    <div className="flex items-start gap-2">
                      <MapPinIcon className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-xs text-muted-foreground">Destination</p>
                        <p className="font-medium">{trip.destination.address}</p>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-4 border-t">
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <ClockIcon className="w-4 h-4" />
                        {formatDate(trip.created_at)}
                      </span>
                      {parseFloat(String(trip.distance || '0')) > 0 && (
                        <span>{parseFloat(String(trip.distance || '0')).toFixed(1)} km</span>
                      )}
                      {trip.duration > 0 && (
                        <span>{trip.duration} min</span>
                      )}
                    </div>
                    <div className="flex gap-2">
                      {['REQUESTED', 'ACCEPTED', 'ARRIVED', 'IN_PROGRESS'].includes(trip.status) && (
                        <>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => router.push(`/trip/${trip.id}`)}
                          >
                            Track
                          </Button>
                          {['REQUESTED', 'ACCEPTED'].includes(trip.status) && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-red-600 hover:text-red-700"
                              onClick={() => handleCancelTrip(trip.id)}
                            >
                              Cancel
                            </Button>
                          )}
                        </>
                      )}
                      {trip.status === 'COMPLETED' && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => router.push(`/trip/${trip.id}`)}
                        >
                          View Details
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
