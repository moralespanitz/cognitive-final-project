'use client';

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { vehiclesApi } from '@/lib/api';
import { useTrackingStore } from '@/lib/store';
import { useTrackingWebSocket } from '@/lib/websocket';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

// Dynamically import map to avoid SSR issues
const VehicleMap = dynamic(() => import('@/components/map'), {
  ssr: false,
  loading: () => <div className="h-full flex items-center justify-center">Loading map...</div>,
});

interface Vehicle {
  id: number;
  license_plate: string;
  make: string;
  model: string;
  status: string;
  color: string;
}

export default function MapPage() {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [selectedVehicleId, setSelectedVehicleId] = useState<number | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const { liveLocations } = useTrackingStore();

  // Connect to WebSocket for real-time updates
  useTrackingWebSocket();

  useEffect(() => {
    loadVehicles();
  }, []);

  const loadVehicles = async () => {
    try {
      const data = await vehiclesApi.getAll();
      setVehicles(data);
    } catch (error) {
      console.error('Failed to load vehicles:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ACTIVE':
        return 'bg-green-500';
      case 'MAINTENANCE':
        return 'bg-yellow-500';
      case 'OUT_OF_SERVICE':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  // Get vehicles with current locations
  const vehiclesWithLocations = vehicles
    .map((vehicle) => {
      const location = liveLocations.find((loc) => loc.vehicle_id === vehicle.id);
      return location
        ? {
            ...vehicle,
            latitude: location.latitude,
            longitude: location.longitude,
            speed: location.speed,
            heading: location.heading,
            timestamp: location.timestamp,
          }
        : null;
    })
    .filter((v) => v !== null);

  // Apply status filter
  const filteredVehicles =
    filterStatus === 'ALL'
      ? vehiclesWithLocations
      : vehiclesWithLocations.filter((v) => v!.status === filterStatus);

  // Get selected vehicle location for centering
  const selectedVehicle = selectedVehicleId
    ? filteredVehicles.find((v) => v!.id === selectedVehicleId)
    : null;

  const mapCenter = selectedVehicle
    ? [selectedVehicle.longitude, selectedVehicle.latitude]
    : undefined;

  const activeCount = vehiclesWithLocations.filter((v) => v!.status === 'ACTIVE').length;
  const maintenanceCount = vehiclesWithLocations.filter(
    (v) => v!.status === 'MAINTENANCE'
  ).length;
  const outOfServiceCount = vehiclesWithLocations.filter(
    (v) => v!.status === 'OUT_OF_SERVICE'
  ).length;

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col">
      {/* Header */}
      <div className="bg-background border-b p-4 space-y-4">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold">Live Fleet Map</h1>
            <p className="text-sm text-muted-foreground">
              Real-time GPS tracking of all vehicles
            </p>
          </div>
          <div className="flex gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-500">{activeCount}</div>
              <div className="text-xs text-muted-foreground">Active</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-500">{maintenanceCount}</div>
              <div className="text-xs text-muted-foreground">Maintenance</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-500">{outOfServiceCount}</div>
              <div className="text-xs text-muted-foreground">Out of Service</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold">{vehiclesWithLocations.length}</div>
              <div className="text-xs text-muted-foreground">Total</div>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="flex gap-4 items-center">
          <Select value={filterStatus} onValueChange={setFilterStatus}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Filter by status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All Vehicles</SelectItem>
              <SelectItem value="ACTIVE">Active Only</SelectItem>
              <SelectItem value="MAINTENANCE">Maintenance</SelectItem>
              <SelectItem value="OUT_OF_SERVICE">Out of Service</SelectItem>
            </SelectContent>
          </Select>

          <Select
            value={selectedVehicleId?.toString() || 'none'}
            onValueChange={(value) =>
              setSelectedVehicleId(value === 'none' ? null : parseInt(value))
            }
          >
            <SelectTrigger className="w-64">
              <SelectValue placeholder="Focus on vehicle" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">All Vehicles</SelectItem>
              {vehiclesWithLocations.map((vehicle) => (
                <SelectItem key={vehicle!.id} value={vehicle!.id.toString()}>
                  {vehicle!.license_plate} - {vehicle!.make} {vehicle!.model}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {selectedVehicleId && (
            <Button variant="outline" onClick={() => setSelectedVehicleId(null)}>
              Clear Selection
            </Button>
          )}

          <div className="flex-1" />

          <Button variant="outline" onClick={loadVehicles}>
            Refresh
          </Button>
        </div>
      </div>

      {/* Map Container */}
      <div className="flex-1 relative">
        <VehicleMap
          height="100%"
          center={mapCenter as [number, number] | undefined}
          zoom={selectedVehicleId ? 15 : 12}
          vehicles={filteredVehicles as any[]}
        />
      </div>

      {/* Vehicle Info Sidebar (when vehicle selected) */}
      {selectedVehicle && (
        <div className="absolute right-4 top-28 w-80 bg-background border rounded-lg shadow-lg p-4 space-y-4">
          <div className="flex justify-between items-start">
            <div>
              <h3 className="font-semibold text-lg">{selectedVehicle.license_plate}</h3>
              <p className="text-sm text-muted-foreground">
                {selectedVehicle.make} {selectedVehicle.model}
              </p>
            </div>
            <Badge className={getStatusColor(selectedVehicle.status)}>
              {selectedVehicle.status}
            </Badge>
          </div>

          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Speed:</span>
              <span className="font-medium">
                {selectedVehicle.speed?.toFixed(1) || 0} km/h
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Heading:</span>
              <span className="font-medium">
                {selectedVehicle.heading?.toFixed(0) || 0}°
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Location:</span>
              <span className="font-medium text-xs">
                {selectedVehicle.latitude?.toFixed(6)}, {selectedVehicle.longitude?.toFixed(6)}
              </span>
            </div>
            {selectedVehicle.timestamp && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Last Update:</span>
                <span className="font-medium text-xs">
                  {new Date(selectedVehicle.timestamp).toLocaleTimeString()}
                </span>
              </div>
            )}
          </div>

          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              className="flex-1"
              onClick={() => (window.location.href = `/vehicles/${selectedVehicle.id}`)}
            >
              View Details
            </Button>
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-background border rounded-lg shadow-lg p-4 space-y-2">
        <h4 className="font-semibold text-sm">Legend</h4>
        <div className="space-y-1 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500" />
            <span>Active Vehicle</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-yellow-500" />
            <span>Maintenance</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500" />
            <span>Out of Service</span>
          </div>
        </div>
      </div>

      {/* Connection Status */}
      <div className="absolute top-4 right-4 bg-background border rounded-lg shadow-lg px-3 py-2">
        <div className="flex items-center gap-2 text-xs">
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-muted-foreground">Live Updates Active</span>
        </div>
      </div>
    </div>
  );
}
