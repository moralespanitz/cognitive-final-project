'use client';

import { useEffect, useState } from 'react';
import { imagesApi, tripsApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  ImageIcon,
  CalendarIcon,
  MapPinIcon,
  ClockIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  XIcon,
} from 'lucide-react';

interface TripImage {
  id: number;
  trip_id: number;
  device_id: string | null;
  image_data: string;
  captured_at: string;
}

interface Trip {
  id: number;
  pickup_location: { address: string };
  destination: { address: string };
  status: string;
  created_at: string;
  identity_verified: boolean;
}

export default function ImageHistoryPage() {
  const [images, setImages] = useState<TripImage[]>([]);
  const [trips, setTrips] = useState<Trip[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedImage, setSelectedImage] = useState<TripImage | null>(null);
  const [currentPage, setCurrentPage] = useState(0);
  const [totalImages, setTotalImages] = useState(0);
  const [dateFilter, setDateFilter] = useState<{ start?: string; end?: string }>({});
  const limit = 12;

  useEffect(() => {
    loadData();
  }, [currentPage, dateFilter]);

  const loadData = async () => {
    try {
      setLoading(true);

      // Load images
      const imageData = await imagesApi.getHistory({
        start_date: dateFilter.start,
        end_date: dateFilter.end,
        limit,
        offset: currentPage * limit,
      });
      setImages(imageData.images);
      setTotalImages(imageData.total);

      // Load trips
      const tripData = await tripsApi.getAll({});
      setTrips(tripData);
    } catch (error) {
      console.error('Error loading history:', error);
    } finally {
      setLoading(false);
    }
  };

  const getTripForImage = (tripId: number) => {
    return trips.find((t) => t.id === tripId);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const totalPages = Math.ceil(totalImages / limit);

  return (
    <div className="container mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">Image History</h1>
          <p className="text-muted-foreground">
            View images captured during your trips
          </p>
        </div>
        <div className="flex gap-4">
          <input
            type="date"
            value={dateFilter.start || ''}
            onChange={(e) => setDateFilter({ ...dateFilter, start: e.target.value })}
            className="px-3 py-2 border rounded-lg"
            placeholder="Start date"
          />
          <input
            type="date"
            value={dateFilter.end || ''}
            onChange={(e) => setDateFilter({ ...dateFilter, end: e.target.value })}
            className="px-3 py-2 border rounded-lg"
            placeholder="End date"
          />
          {(dateFilter.start || dateFilter.end) && (
            <Button
              variant="ghost"
              onClick={() => setDateFilter({})}
              size="sm"
            >
              Clear Filters
            </Button>
          )}
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      ) : images.length === 0 ? (
        <Card>
          <CardContent className="py-16 text-center">
            <ImageIcon className="w-16 h-16 mx-auto text-gray-300 mb-4" />
            <h3 className="text-lg font-semibold text-gray-600">No Images Found</h3>
            <p className="text-muted-foreground">
              Images from your trips will appear here.
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Image Grid */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 mb-6">
            {images.map((image) => {
              const trip = getTripForImage(image.trip_id);
              return (
                <Card
                  key={image.id}
                  className="overflow-hidden cursor-pointer hover:shadow-lg transition-shadow"
                  onClick={() => setSelectedImage(image)}
                >
                  <div className="aspect-video bg-gray-100 relative">
                    <img
                      src={`data:image/jpeg;base64,${image.image_data}`}
                      alt={`Trip ${image.trip_id}`}
                      className="w-full h-full object-cover"
                    />
                    <Badge className="absolute top-2 right-2" variant="secondary">
                      Trip #{image.trip_id}
                    </Badge>
                  </div>
                  <CardContent className="p-3">
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                      <ClockIcon className="w-3 h-3" />
                      {formatDate(image.captured_at)}
                    </div>
                    {trip && (
                      <div className="flex items-center gap-1 text-xs text-muted-foreground mt-1 truncate">
                        <MapPinIcon className="w-3 h-3 flex-shrink-0" />
                        {trip.pickup_location.address}
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-4">
              <Button
                variant="outline"
                onClick={() => setCurrentPage((p) => Math.max(0, p - 1))}
                disabled={currentPage === 0}
              >
                <ChevronLeftIcon className="w-4 h-4" />
                Previous
              </Button>
              <span className="text-sm text-muted-foreground">
                Page {currentPage + 1} of {totalPages}
              </span>
              <Button
                variant="outline"
                onClick={() => setCurrentPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={currentPage >= totalPages - 1}
              >
                Next
                <ChevronRightIcon className="w-4 h-4" />
              </Button>
            </div>
          )}
        </>
      )}

      {/* Image Modal */}
      {selectedImage && (
        <div
          className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4"
          onClick={() => setSelectedImage(null)}
        >
          <div
            className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-center p-4 border-b">
              <div>
                <h3 className="font-semibold">Trip #{selectedImage.trip_id}</h3>
                <p className="text-sm text-muted-foreground">
                  {formatDate(selectedImage.captured_at)}
                </p>
              </div>
              <Button variant="ghost" size="icon" onClick={() => setSelectedImage(null)}>
                <XIcon className="w-5 h-5" />
              </Button>
            </div>
            <div className="p-4">
              <img
                src={`data:image/jpeg;base64,${selectedImage.image_data}`}
                alt={`Trip ${selectedImage.trip_id}`}
                className="w-full h-auto rounded-lg"
              />
            </div>
            {getTripForImage(selectedImage.trip_id) && (
              <div className="p-4 border-t bg-gray-50">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">Pickup</p>
                    <p className="font-medium">
                      {getTripForImage(selectedImage.trip_id)?.pickup_location.address}
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Destination</p>
                    <p className="font-medium">
                      {getTripForImage(selectedImage.trip_id)?.destination.address}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
