'use client';

import { useEffect, useRef, useState } from 'react';
import Map, { Marker, Popup, NavigationControl, GeolocateControl } from 'react-map-gl/mapbox';
import 'mapbox-gl/dist/mapbox-gl.css';
import { useTrackingStore, useVehicleStore } from '@/lib/store';
import { CarIcon } from 'lucide-react';

const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN || 'pk.eyJ1IjoidGF4aXdhdGNoIiwiYSI6ImNscHcyZXB5cTBxdHAybHFwN25hbmRuNTEifQ.example';

interface VehicleMapProps {
  height?: string;
  center?: [number, number]; // [longitude, latitude]
  zoom?: number;
  vehicles?: any[]; // Optional custom vehicle data
}

export default function VehicleMap({
  height = '600px',
  center,
  zoom: initialZoom,
  vehicles: customVehicles
}: VehicleMapProps) {
  const mapRef = useRef<any>(null);
  const liveLocations = useTrackingStore((state) => state.liveLocations);
  const storeVehicles = useVehicleStore((state) => state.vehicles);
  const [selectedVehicle, setSelectedVehicle] = useState<number | null>(null);

  // Use custom vehicles if provided, otherwise use store
  const vehicles = customVehicles || storeVehicles;

  const [viewState, setViewState] = useState({
    longitude: center ? center[0] : -74.006,
    latitude: center ? center[1] : 40.7128,
    zoom: initialZoom || 12
  });

  // Get vehicle info by ID
  const getVehicleInfo = (vehicleId: number) => {
    return vehicles.find(v => v.id === vehicleId);
  };

  // Get marker color based on vehicle status
  const getMarkerColor = (vehicleId: number) => {
    const vehicle = getVehicleInfo(vehicleId);
    if (!vehicle) return '#gray';
    
    switch (vehicle.status) {
      case 'ACTIVE':
        return '#10b981'; // green
      case 'MAINTENANCE':
        return '#f59e0b'; // yellow
      case 'OUT_OF_SERVICE':
        return '#ef4444'; // red
      default:
        return '#6b7280'; // gray
    }
  };

  return (
    <div className="rounded-lg overflow-hidden border border-gray-200 shadow-lg">
      <Map
        ref={mapRef}
        {...viewState}
        onMove={evt => setViewState(evt.viewState)}
        style={{ width: '100%', height }}
        mapStyle="mapbox://styles/mapbox/streets-v12"
        mapboxAccessToken={MAPBOX_TOKEN}
      >
        {/* Controls */}
        <NavigationControl position="top-right" />
        <GeolocateControl position="top-right" />

        {/* Vehicle Markers */}
        {customVehicles ? (
          // Render custom vehicles with inline location data
          customVehicles.map((vehicle) => (
            <Marker
              key={vehicle.id}
              longitude={vehicle.longitude}
              latitude={vehicle.latitude}
              anchor="center"
              onClick={(e) => {
                e.originalEvent.stopPropagation();
                setSelectedVehicle(vehicle.id);
              }}
            >
              <div
                className="cursor-pointer transition-transform hover:scale-110"
                style={{
                  backgroundColor: getMarkerColor(vehicle.id),
                  borderRadius: '50%',
                  width: '32px',
                  height: '32px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  border: '3px solid white',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.3)'
                }}
              >
                <CarIcon className="w-4 h-4 text-white" />
              </div>
            </Marker>
          ))
        ) : (
          // Render from live locations store
          liveLocations.map((location) => (
            <Marker
              key={location.vehicle_id}
              longitude={location.longitude}
              latitude={location.latitude}
              anchor="center"
              onClick={(e) => {
                e.originalEvent.stopPropagation();
                setSelectedVehicle(location.vehicle_id);
              }}
            >
              <div
                className="cursor-pointer transition-transform hover:scale-110"
                style={{
                  backgroundColor: getMarkerColor(location.vehicle_id),
                  borderRadius: '50%',
                  width: '32px',
                  height: '32px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  border: '3px solid white',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.3)'
                }}
              >
                <CarIcon className="w-4 h-4 text-white" />
              </div>
            </Marker>
          ))
        )}

        {/* Popup */}
        {selectedVehicle && liveLocations.find(l => l.vehicle_id === selectedVehicle) && (
          <Popup
            longitude={liveLocations.find(l => l.vehicle_id === selectedVehicle)!.longitude}
            latitude={liveLocations.find(l => l.vehicle_id === selectedVehicle)!.latitude}
            anchor="bottom"
            onClose={() => setSelectedVehicle(null)}
            closeButton={true}
          >
            <div className="p-2">
              {(() => {
                const vehicle = getVehicleInfo(selectedVehicle);
                const location = liveLocations.find(l => l.vehicle_id === selectedVehicle);
                return (
                  <div>
                    <h3 className="font-bold text-sm mb-1">
                      {vehicle?.license_plate || `Vehicle #${selectedVehicle}`}
                    </h3>
                    {vehicle && (
                      <p className="text-xs text-gray-600 mb-2">
                        {vehicle.make} {vehicle.model} ({vehicle.year})
                      </p>
                    )}
                    {location && (
                      <>
                        <p className="text-xs">
                          <span className="font-semibold">Speed:</span> {location.speed?.toFixed(1) || '0'} km/h
                        </p>
                        <p className="text-xs text-gray-500">
                          Last update: {new Date(location.timestamp).toLocaleTimeString()}
                        </p>
                      </>
                    )}
                  </div>
                );
              })()}
            </div>
          </Popup>
        )}
      </Map>
    </div>
  );
}
