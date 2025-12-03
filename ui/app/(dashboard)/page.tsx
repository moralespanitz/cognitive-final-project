'use client';

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { vehiclesApi, trackingApi } from '@/lib/api';
import { useVehicleStore, useTrackingStore } from '@/lib/store';
import { useTrackingWebSocket } from '@/lib/websocket';
import { CarIcon, ActivityIcon, AlertTriangleIcon, TrendingUpIcon } from 'lucide-react';

// Dynamic import to avoid SSR issues with Mapbox
const VehicleMap = dynamic(() => import('@/components/map'), { ssr: false });

export default function DashboardPage() {
  const { vehicles, setVehicles } = useVehicleStore();
  const { liveLocations, setLiveLocations } = useTrackingStore();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalVehicles: 0,
    activeVehicles: 0,
    totalTrips: 0,
    alerts: 0
  });

  // Connect to WebSocket for real-time updates
  useTrackingWebSocket();

  useEffect(() => {
    loadData();
    // Refresh data every 10 seconds
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      // Load vehicles
      const vehiclesData = await vehiclesApi.getAll();
      setVehicles(vehiclesData);

      // Load live locations
      const locationsData = await trackingApi.getLiveLocations();
      setLiveLocations(locationsData);

      // Calculate stats
      setStats({
        totalVehicles: vehiclesData.length,
        activeVehicles: vehiclesData.filter((v: any) => v.status === 'ACTIVE').length,
        totalTrips: 0, // TODO: Get from API
        alerts: 0 // TODO: Get from API
      });
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <p className="text-gray-600">Loading dashboard...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600">Monitor your fleet in real-time</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Vehicles</CardTitle>
            <CarIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalVehicles}</div>
            <p className="text-xs text-muted-foreground">
              {stats.activeVehicles} active
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Now</CardTitle>
            <ActivityIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{liveLocations.length}</div>
            <p className="text-xs text-muted-foreground">
              Vehicles broadcasting
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Trips Today</CardTitle>
            <TrendingUpIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalTrips}</div>
            <p className="text-xs text-muted-foreground">
              +12% from yesterday
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Alerts</CardTitle>
            <AlertTriangleIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.alerts}</div>
            <p className="text-xs text-muted-foreground">
              All systems normal
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Map */}
      <Card>
        <CardHeader>
          <CardTitle>Live Fleet Map</CardTitle>
          <CardDescription>
            Real-time location of all vehicles
          </CardDescription>
        </CardHeader>
        <CardContent>
          <VehicleMap height="500px" />
        </CardContent>
      </Card>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>Latest updates from your fleet</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {liveLocations.slice(0, 5).map((location) => {
                const vehicle = vehicles.find(v => v.id === location.vehicle_id);
                return (
                  <div key={location.id} className="flex items-center">
                    <div className="w-2 h-2 bg-green-500 rounded-full mr-3" />
                    <div className="flex-1">
                      <p className="text-sm font-medium">
                        {vehicle?.license_plate || `Vehicle #${location.vehicle_id}`}
                      </p>
                      <p className="text-xs text-gray-500">
                        {location.speed?.toFixed(1) || '0'} km/h • {new Date(location.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                );
              })}
              {liveLocations.length === 0 && (
                <p className="text-sm text-gray-500 text-center py-4">
                  No active vehicles broadcasting
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Fleet Status</CardTitle>
            <CardDescription>Overview of vehicle statuses</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-green-500 rounded-full mr-2" />
                  <span className="text-sm">Active</span>
                </div>
                <span className="text-sm font-medium">
                  {vehicles.filter(v => v.status === 'ACTIVE').length}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-yellow-500 rounded-full mr-2" />
                  <span className="text-sm">Maintenance</span>
                </div>
                <span className="text-sm font-medium">
                  {vehicles.filter(v => v.status === 'MAINTENANCE').length}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-red-500 rounded-full mr-2" />
                  <span className="text-sm">Out of Service</span>
                </div>
                <span className="text-sm font-medium">
                  {vehicles.filter(v => v.status === 'OUT_OF_SERVICE').length}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
