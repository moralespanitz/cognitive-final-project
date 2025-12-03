'use client';

import { useEffect, useState, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  VideoIcon,
  RefreshCwIcon,
  WifiIcon,
  WifiOffIcon,
  MonitorIcon,
} from 'lucide-react';

interface DeviceFrame {
  image: string;
  timestamp: string;
  size: number;
  trip_id?: string;
}

interface ActiveDevice {
  id: string;
  frame: DeviceFrame | null;
  connected: boolean;
  lastUpdate: Date | null;
}

export default function VideoMonitorPage() {
  const [devices, setDevices] = useState<string[]>([]);
  const [activeDevices, setActiveDevices] = useState<Map<string, ActiveDevice>>(new Map());
  const [loading, setLoading] = useState(true);
  const [selectedDevice, setSelectedDevice] = useState<string | null>(null);
  const wsRefs = useRef<Map<string, WebSocket>>(new Map());

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
  const wsHost = apiUrl.replace('http://', '').replace('/api/v1', '');

  // Fetch list of active devices
  const fetchDevices = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${apiUrl}/video/device/list`);
      const data = await response.json();
      setDevices(data.devices || []);

      // Also fetch latest frame for each device
      for (const deviceId of data.devices || []) {
        try {
          const frameResponse = await fetch(`${apiUrl}/video/device/latest/${deviceId}`);
          const frameData = await frameResponse.json();
          if (frameData.image) {
            setActiveDevices(prev => {
              const newMap = new Map(prev);
              newMap.set(deviceId, {
                id: deviceId,
                frame: frameData,
                connected: false,
                lastUpdate: new Date(),
              });
              return newMap;
            });
          }
        } catch (e) {
          console.error(`Error fetching frame for ${deviceId}:`, e);
        }
      }
    } catch (error) {
      console.error('Error fetching devices:', error);
    } finally {
      setLoading(false);
    }
  };

  // Connect to WebSocket for a specific device
  const connectToDevice = (deviceId: string) => {
    if (wsRefs.current.has(deviceId)) {
      wsRefs.current.get(deviceId)?.close();
    }

    const ws = new WebSocket(`ws://${wsHost}/ws/video/${deviceId}`);

    ws.onopen = () => {
      console.log(`📹 Connected to ${deviceId}`);
      setActiveDevices(prev => {
        const newMap = new Map(prev);
        const device = newMap.get(deviceId) || { id: deviceId, frame: null, connected: false, lastUpdate: null };
        device.connected = true;
        newMap.set(deviceId, device);
        return newMap;
      });
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'frame' && data.image) {
        setActiveDevices(prev => {
          const newMap = new Map(prev);
          const device = newMap.get(deviceId) || { id: deviceId, frame: null, connected: true, lastUpdate: null };
          device.frame = {
            image: data.image,
            timestamp: data.timestamp,
            size: data.size,
            trip_id: data.trip_id,
          };
          device.lastUpdate = new Date();
          newMap.set(deviceId, device);
          return newMap;
        });
      }
    };

    ws.onclose = () => {
      console.log(`📹 Disconnected from ${deviceId}`);
      setActiveDevices(prev => {
        const newMap = new Map(prev);
        const device = newMap.get(deviceId);
        if (device) {
          device.connected = false;
          newMap.set(deviceId, device);
        }
        return newMap;
      });
    };

    wsRefs.current.set(deviceId, ws);
  };

  // Disconnect from a device
  const disconnectFromDevice = (deviceId: string) => {
    wsRefs.current.get(deviceId)?.close();
    wsRefs.current.delete(deviceId);
  };

  useEffect(() => {
    fetchDevices();

    // Auto-refresh device list every 10 seconds
    const interval = setInterval(fetchDevices, 10000);

    return () => {
      clearInterval(interval);
      // Close all WebSocket connections
      wsRefs.current.forEach(ws => ws.close());
    };
  }, []);

  // Auto-connect to selected device
  useEffect(() => {
    if (selectedDevice) {
      connectToDevice(selectedDevice);
    }
    return () => {
      if (selectedDevice) {
        disconnectFromDevice(selectedDevice);
      }
    };
  }, [selectedDevice]);

  const formatTimestamp = (ts: string) => {
    try {
      return new Date(ts).toLocaleTimeString();
    } catch {
      return ts;
    }
  };

  return (
    <div className="container mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <MonitorIcon className="w-6 h-6" />
            Video Stream Monitor
          </h1>
          <p className="text-muted-foreground">
            Monitor ESP32-CAM video streams in real-time
          </p>
        </div>
        <Button onClick={fetchDevices} disabled={loading}>
          <RefreshCwIcon className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh Devices
        </Button>
      </div>

      {/* Connection Info */}
      <Card className="mb-6">
        <CardContent className="py-4">
          <div className="flex flex-wrap gap-4 items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">API Endpoint</p>
              <code className="text-xs bg-gray-100 px-2 py-1 rounded">{apiUrl}</code>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">WebSocket Host</p>
              <code className="text-xs bg-gray-100 px-2 py-1 rounded">ws://{wsHost}</code>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Active Devices</p>
              <Badge variant={devices.length > 0 ? "default" : "secondary"}>
                {devices.length} device{devices.length !== 1 ? 's' : ''}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Device List */}
      {devices.length === 0 ? (
        <Card>
          <CardContent className="py-16 text-center">
            <VideoIcon className="w-16 h-16 mx-auto text-gray-300 mb-4" />
            <h3 className="text-lg font-semibold text-gray-600 mb-2">No Active Devices</h3>
            <p className="text-muted-foreground mb-4">
              Run the ESP32 mock simulator to start sending frames:
            </p>
            <div className="bg-gray-100 rounded-lg p-4 text-left max-w-xl mx-auto">
              <code className="text-sm text-gray-800 whitespace-pre-wrap">
{`cd backend/app/scripts
python esp32_mock.py --route taxi-01`}
              </code>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {devices.map(deviceId => {
            const device = activeDevices.get(deviceId);
            const isSelected = selectedDevice === deviceId;

            return (
              <Card
                key={deviceId}
                className={`cursor-pointer transition-all ${isSelected ? 'ring-2 ring-blue-500' : 'hover:shadow-lg'}`}
                onClick={() => setSelectedDevice(isSelected ? null : deviceId)}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <VideoIcon className="w-5 h-5" />
                      {deviceId}
                    </CardTitle>
                    <Badge variant={device?.connected ? "default" : "secondary"}>
                      {device?.connected ? (
                        <><WifiIcon className="w-3 h-3 mr-1" /> Live</>
                      ) : (
                        <><WifiOffIcon className="w-3 h-3 mr-1" /> Offline</>
                      )}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="aspect-video bg-gray-900 rounded-lg overflow-hidden relative">
                    {device?.frame?.image ? (
                      <>
                        <img
                          src={`data:image/jpeg;base64,${device.frame.image}`}
                          alt={`Feed from ${deviceId}`}
                          className="w-full h-full object-cover"
                        />
                        {device.connected && (
                          <div className="absolute top-2 left-2 bg-red-600 text-white px-2 py-0.5 rounded text-xs font-bold flex items-center gap-1">
                            <div className="w-1.5 h-1.5 bg-white rounded-full animate-pulse" />
                            LIVE
                          </div>
                        )}
                      </>
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-white text-sm">
                        {isSelected ? 'Connecting...' : 'Click to connect'}
                      </div>
                    )}
                  </div>
                  <div className="mt-2 text-xs text-muted-foreground space-y-1">
                    {device?.frame && (
                      <>
                        <p>Size: {device.frame.size} bytes</p>
                        <p>Last update: {device.lastUpdate ? device.lastUpdate.toLocaleTimeString() : 'N/A'}</p>
                        {device.frame.trip_id && (
                          <p>Trip: #{device.frame.trip_id}</p>
                        )}
                      </>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Instructions */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-lg">Testing Video Streaming</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h4 className="font-semibold mb-2">1. Run the ESP32 Mock Simulator</h4>
            <div className="bg-gray-100 rounded-lg p-4">
              <code className="text-sm text-gray-800 whitespace-pre-wrap">
{`# Install dependencies
pip install pillow requests

# Run the simulator (sends frames to production server)
cd backend/app/scripts
python esp32_mock.py --route taxi-01

# With custom options
python esp32_mock.py --route taxi-02 --interval 2 --trip 5`}
              </code>
            </div>
          </div>
          <div>
            <h4 className="font-semibold mb-2">2. Verify on this page</h4>
            <p className="text-muted-foreground">
              Once the simulator is running, click "Refresh Devices" to see the active device.
              Click on a device card to connect to its live WebSocket feed.
            </p>
          </div>
          <div>
            <h4 className="font-semibold mb-2">3. Test endpoints directly</h4>
            <div className="bg-gray-100 rounded-lg p-4 space-y-2">
              <p className="text-sm">
                <strong>List devices:</strong>{' '}
                <a href={`${apiUrl}/video/device/list`} target="_blank" className="text-blue-600 hover:underline">
                  {apiUrl}/video/device/list
                </a>
              </p>
              <p className="text-sm">
                <strong>Latest frame:</strong>{' '}
                <code className="bg-gray-200 px-1 rounded">{apiUrl}/video/device/latest/taxi-01</code>
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
