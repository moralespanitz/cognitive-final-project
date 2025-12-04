"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Car,
  Users,
  TrendingUp,
  Activity,
  DollarSign,
  MapPin,
  RefreshCw,
  CheckCircle,
  XCircle,
  Clock,
  BarChart3,
  Wifi,
  WifiOff,
} from "lucide-react";

interface Stats {
  trips: {
    total_trips: number;
    completed_trips: number;
    cancelled_trips: number;
    in_progress_trips: number;
    total_revenue: number;
    total_distance: number;
    average_fare: number;
    average_distance: number;
    average_duration_minutes: number;
  };
  vehicles: {
    total_vehicles: number;
    active_vehicles: number;
    maintenance_vehicles: number;
    inactive_vehicles: number;
    utilization_rate: number;
  };
  drivers: {
    total_drivers: number;
    on_duty_drivers: number;
    off_duty_drivers: number;
    busy_drivers: number;
    average_rating: number;
    average_trips_per_driver: number;
  };
  users: {
    total_users: number;
    active_users: number;
    admin_users: number;
    customer_users: number;
    driver_users: number;
  };
  devices: {
    total_devices: number;
    online_devices: number;
    offline_devices: number;
    error_devices: number;
  };
  system_health: {
    database_connected: boolean;
    redis_connected: boolean;
    api_status: string;
    uptime_seconds: number;
    last_check: string;
  };
  generated_at: string;
}

interface AIMetrics {
  service: string;
  status: string;
  metrics: {
    accuracy: number;
    total_queries: number;
    successful_queries: number;
    uptime_hours: number;
    queries_per_hour: number;
    confidence_threshold: number;
    service_type: string;
    cost_savings: string;
  };
}

export default function AnalyticsPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [aiMetrics, setAIMetrics] = useState<AIMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("access_token");

      // Fetch dashboard stats
      const statsResponse = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/admin/stats`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (statsResponse.ok) {
        const data = await statsResponse.json();
        setStats(data);
      }

      // Fetch AI metrics
      const aiResponse = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/chat/metrics`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (aiResponse.ok) {
        const data = await aiResponse.json();
        setAIMetrics(data);
      }

      setLastUpdate(new Date());
    } catch (error) {
      console.error("Error fetching analytics:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(value);
  };

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  if (loading && !stats) {
    return (
      <div className="flex items-center justify-center h-[600px]">
        <RefreshCw className="h-12 w-12 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">System Analytics</h1>
          <p className="text-muted-foreground">
            Real-time performance metrics and statistics
          </p>
        </div>
        <Button onClick={fetchData} variant="outline" disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {/* Last Update */}
      <div className="text-sm text-muted-foreground">
        Last updated: {lastUpdate.toLocaleTimeString()}
      </div>

      {/* AI Performance */}
      {aiMetrics && (
        <Card className="border-green-200 bg-green-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              AI Service Performance
            </CardTitle>
            <CardDescription>
              Mock AI Service with pattern matching and FAQ database
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-4">
              <div>
                <div className="text-2xl font-bold text-green-600">
                  {(aiMetrics.metrics.accuracy * 100).toFixed(1)}%
                </div>
                <div className="text-xs text-muted-foreground">Accuracy</div>
              </div>
              <div>
                <div className="text-2xl font-bold">
                  {aiMetrics.metrics.total_queries}
                </div>
                <div className="text-xs text-muted-foreground">Total Queries</div>
              </div>
              <div>
                <div className="text-2xl font-bold">
                  {aiMetrics.metrics.queries_per_hour.toFixed(1)}
                </div>
                <div className="text-xs text-muted-foreground">Queries/Hour</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-green-600">
                  {aiMetrics.metrics.cost_savings}
                </div>
                <div className="text-xs text-muted-foreground">Cost Savings</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* System Health */}
      {stats && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              System Health
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="flex items-center gap-2">
                {stats.system_health.database_connected ? (
                  <CheckCircle className="h-5 w-5 text-green-500" />
                ) : (
                  <XCircle className="h-5 w-5 text-red-500" />
                )}
                <div>
                  <div className="font-medium">Database</div>
                  <div className="text-xs text-muted-foreground">
                    {stats.system_health.database_connected
                      ? "Connected"
                      : "Disconnected"}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {stats.system_health.redis_connected ? (
                  <CheckCircle className="h-5 w-5 text-green-500" />
                ) : (
                  <XCircle className="h-5 w-5 text-red-500" />
                )}
                <div>
                  <div className="font-medium">Redis Cache</div>
                  <div className="text-xs text-muted-foreground">
                    {stats.system_health.redis_connected
                      ? "Connected"
                      : "Disconnected"}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Clock className="h-5 w-5 text-blue-500" />
                <div>
                  <div className="font-medium">API Status</div>
                  <div className="text-xs text-muted-foreground">
                    {stats.system_health.api_status}
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Trip Statistics */}
      {stats && (
        <>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  Total Revenue
                </CardTitle>
                <DollarSign className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {formatCurrency(stats.trips.total_revenue)}
                </div>
                <p className="text-xs text-muted-foreground">
                  {stats.trips.completed_trips} completed trips
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Active Trips</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {stats.trips.in_progress_trips}
                </div>
                <p className="text-xs text-muted-foreground">
                  {stats.trips.total_trips} total trips
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  Average Fare
                </CardTitle>
                <DollarSign className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {formatCurrency(stats.trips.average_fare)}
                </div>
                <p className="text-xs text-muted-foreground">
                  {stats.trips.average_distance.toFixed(1)} km avg
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Distance</CardTitle>
                <MapPin className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {stats.trips.total_distance.toFixed(0)} km
                </div>
                <p className="text-xs text-muted-foreground">
                  {stats.trips.average_duration_minutes.toFixed(0)} min avg
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Vehicle & Driver Stats */}
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Car className="h-5 w-5" />
                  Vehicle Statistics
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Total Vehicles</span>
                    <Badge>{stats.vehicles.total_vehicles}</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Active</span>
                    <Badge variant="default">
                      {stats.vehicles.active_vehicles}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">In Maintenance</span>
                    <Badge variant="outline">
                      {stats.vehicles.maintenance_vehicles}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Utilization Rate</span>
                    <Badge variant="secondary">
                      {stats.vehicles.utilization_rate.toFixed(1)}%
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5" />
                  Driver Statistics
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Total Drivers</span>
                    <Badge>{stats.drivers.total_drivers}</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">On Duty</span>
                    <Badge variant="default">
                      {stats.drivers.on_duty_drivers}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Busy (in trip)</span>
                    <Badge variant="outline">{stats.drivers.busy_drivers}</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Average Rating</span>
                    <Badge variant="secondary">
                      {stats.drivers.average_rating.toFixed(2)} ⭐
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Devices & Users */}
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  IoT Devices
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Wifi className="h-4 w-4 text-green-500" />
                      <span className="text-sm">Online</span>
                    </div>
                    <Badge variant="default">{stats.devices.online_devices}</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <WifiOff className="h-4 w-4 text-gray-500" />
                      <span className="text-sm">Offline</span>
                    </div>
                    <Badge variant="secondary">
                      {stats.devices.offline_devices}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <XCircle className="h-4 w-4 text-red-500" />
                      <span className="text-sm">Error</span>
                    </div>
                    <Badge variant="destructive">
                      {stats.devices.error_devices}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5" />
                  User Statistics
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Total Users</span>
                    <Badge>{stats.users.total_users}</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Active</span>
                    <Badge variant="default">{stats.users.active_users}</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Customers</span>
                    <Badge variant="secondary">
                      {stats.users.customer_users}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Admins</span>
                    <Badge variant="outline">{stats.users.admin_users}</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
