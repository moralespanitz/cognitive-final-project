'use client';

import { useEffect, useState } from 'react';
import { devicesApi, vehiclesApi } from '@/lib/api';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';

interface Device {
  id: number;
  vehicle_id: number;
  device_type: string;
  serial_number: string;
  model: string;
  manufacturer: string;
  firmware_version: string;
  status: string;
  last_ping: string | null;
  config: any;
  created_at: string;
  updated_at: string;
}

interface Vehicle {
  id: number;
  license_plate: string;
  make: string;
  model: string;
}

export default function DevicesPage() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [loading, setLoading] = useState(true);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<string>('ALL');
  const [filterStatus, setFilterStatus] = useState<string>('ALL');

  const [formData, setFormData] = useState({
    vehicle_id: '',
    device_type: 'GPS',
    serial_number: '',
    model: '',
    manufacturer: '',
    firmware_version: '1.0.0',
    status: 'OFFLINE',
  });

  useEffect(() => {
    loadDevices();
    loadVehicles();
  }, []);

  const loadDevices = async () => {
    try {
      const data = await devicesApi.getAll();
      setDevices(data);
    } catch (error) {
      console.error('Failed to load devices:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadVehicles = async () => {
    try {
      const data = await vehiclesApi.getAll();
      setVehicles(data);
    } catch (error) {
      console.error('Failed to load vehicles:', error);
    }
  };

  const handleCreate = async () => {
    try {
      await devicesApi.create({
        ...formData,
        vehicle_id: parseInt(formData.vehicle_id),
      });
      setIsCreateOpen(false);
      resetForm();
      await loadDevices();
    } catch (error) {
      console.error('Failed to create device:', error);
      alert('Failed to create device');
    }
  };

  const handleUpdate = async () => {
    if (!selectedDevice) return;

    try {
      await devicesApi.update(selectedDevice.id, {
        ...formData,
        vehicle_id: parseInt(formData.vehicle_id),
      });
      setIsEditOpen(false);
      setSelectedDevice(null);
      resetForm();
      await loadDevices();
    } catch (error) {
      console.error('Failed to update device:', error);
      alert('Failed to update device');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this device?')) return;

    try {
      await devicesApi.delete(id);
      await loadDevices();
    } catch (error) {
      console.error('Failed to delete device:', error);
      alert('Failed to delete device');
    }
  };

  const handlePing = async (id: number) => {
    try {
      await devicesApi.ping(id);
      await loadDevices();
    } catch (error) {
      console.error('Failed to ping device:', error);
      alert('Failed to ping device');
    }
  };

  const openEditDialog = (device: Device) => {
    setSelectedDevice(device);
    setFormData({
      vehicle_id: device.vehicle_id.toString(),
      device_type: device.device_type,
      serial_number: device.serial_number,
      model: device.model,
      manufacturer: device.manufacturer,
      firmware_version: device.firmware_version,
      status: device.status,
    });
    setIsEditOpen(true);
  };

  const resetForm = () => {
    setFormData({
      vehicle_id: '',
      device_type: 'GPS',
      serial_number: '',
      model: '',
      manufacturer: '',
      firmware_version: '1.0.0',
      status: 'OFFLINE',
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ONLINE':
        return 'bg-green-500';
      case 'OFFLINE':
        return 'bg-gray-500';
      case 'ERROR':
        return 'bg-red-500';
      case 'MAINTENANCE':
        return 'bg-yellow-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'GPS':
        return '📍';
      case 'CAMERA':
        return '📹';
      case 'SENSOR':
        return '🔧';
      case 'OBD':
        return '🔌';
      default:
        return '📱';
    }
  };

  const filteredDevices = devices.filter((device) => {
    const matchesSearch =
      device.serial_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      device.manufacturer.toLowerCase().includes(searchTerm.toLowerCase()) ||
      device.model.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesType = filterType === 'ALL' || device.device_type === filterType;
    const matchesStatus = filterStatus === 'ALL' || device.status === filterStatus;

    return matchesSearch && matchesType && matchesStatus;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg">Loading devices...</div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Device Management</h1>
          <p className="text-muted-foreground">Manage hardware devices for vehicles</p>
        </div>
        <Button onClick={() => setIsCreateOpen(true)}>Add Device</Button>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <div className="flex-1">
          <Input
            placeholder="Search by serial, manufacturer, or model..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <Select value={filterType} onValueChange={setFilterType}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Device Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">All Types</SelectItem>
            <SelectItem value="GPS">GPS</SelectItem>
            <SelectItem value="CAMERA">Camera</SelectItem>
            <SelectItem value="SENSOR">Sensor</SelectItem>
            <SelectItem value="OBD">OBD</SelectItem>
            <SelectItem value="OTHER">Other</SelectItem>
          </SelectContent>
        </Select>
        <Select value={filterStatus} onValueChange={setFilterStatus}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">All Status</SelectItem>
            <SelectItem value="ONLINE">Online</SelectItem>
            <SelectItem value="OFFLINE">Offline</SelectItem>
            <SelectItem value="ERROR">Error</SelectItem>
            <SelectItem value="MAINTENANCE">Maintenance</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Devices Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {filteredDevices.map((device) => {
          const vehicle = vehicles.find((v) => v.id === device.vehicle_id);
          return (
            <div key={device.id} className="border rounded-lg p-4 space-y-3">
              <div className="flex justify-between items-start">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">{getTypeIcon(device.device_type)}</span>
                  <div>
                    <h3 className="font-semibold">{device.device_type}</h3>
                    <p className="text-sm text-muted-foreground">{device.serial_number}</p>
                  </div>
                </div>
                <Badge className={getStatusColor(device.status)}>
                  {device.status}
                </Badge>
              </div>

              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Vehicle:</span>
                  <span className="font-medium">
                    {vehicle ? `${vehicle.license_plate}` : 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Manufacturer:</span>
                  <span>{device.manufacturer}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Model:</span>
                  <span>{device.model}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Firmware:</span>
                  <span>{device.firmware_version}</span>
                </div>
                {device.last_ping && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Last Ping:</span>
                    <span>{new Date(device.last_ping).toLocaleString()}</span>
                  </div>
                )}
              </div>

              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="flex-1"
                  onClick={() => handlePing(device.id)}
                >
                  Ping
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="flex-1"
                  onClick={() => openEditDialog(device)}
                >
                  Edit
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => handleDelete(device.id)}
                >
                  Delete
                </Button>
              </div>
            </div>
          );
        })}
      </div>

      {filteredDevices.length === 0 && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">No devices found</p>
        </div>
      )}

      {/* Create Dialog */}
      <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add New Device</DialogTitle>
            <DialogDescription>Create a new device for a vehicle</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Vehicle</Label>
              <Select
                value={formData.vehicle_id}
                onValueChange={(value) =>
                  setFormData({ ...formData, vehicle_id: value })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select vehicle" />
                </SelectTrigger>
                <SelectContent>
                  {vehicles.map((vehicle) => (
                    <SelectItem key={vehicle.id} value={vehicle.id.toString()}>
                      {vehicle.license_plate} - {vehicle.make} {vehicle.model}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Device Type</Label>
              <Select
                value={formData.device_type}
                onValueChange={(value) =>
                  setFormData({ ...formData, device_type: value })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="GPS">GPS</SelectItem>
                  <SelectItem value="CAMERA">Camera</SelectItem>
                  <SelectItem value="SENSOR">Sensor</SelectItem>
                  <SelectItem value="OBD">OBD</SelectItem>
                  <SelectItem value="OTHER">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Serial Number</Label>
              <Input
                value={formData.serial_number}
                onChange={(e) =>
                  setFormData({ ...formData, serial_number: e.target.value })
                }
                placeholder="SN123456"
              />
            </div>
            <div>
              <Label>Manufacturer</Label>
              <Input
                value={formData.manufacturer}
                onChange={(e) =>
                  setFormData({ ...formData, manufacturer: e.target.value })
                }
                placeholder="U-blox, Espressif, etc."
              />
            </div>
            <div>
              <Label>Model</Label>
              <Input
                value={formData.model}
                onChange={(e) =>
                  setFormData({ ...formData, model: e.target.value })
                }
                placeholder="NEO-6M, ESP32-CAM, etc."
              />
            </div>
            <div>
              <Label>Firmware Version</Label>
              <Input
                value={formData.firmware_version}
                onChange={(e) =>
                  setFormData({ ...formData, firmware_version: e.target.value })
                }
                placeholder="1.0.0"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreate}>Create Device</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Device</DialogTitle>
            <DialogDescription>Update device information</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Vehicle</Label>
              <Select
                value={formData.vehicle_id}
                onValueChange={(value) =>
                  setFormData({ ...formData, vehicle_id: value })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select vehicle" />
                </SelectTrigger>
                <SelectContent>
                  {vehicles.map((vehicle) => (
                    <SelectItem key={vehicle.id} value={vehicle.id.toString()}>
                      {vehicle.license_plate} - {vehicle.make} {vehicle.model}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Device Type</Label>
              <Select
                value={formData.device_type}
                onValueChange={(value) =>
                  setFormData({ ...formData, device_type: value })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="GPS">GPS</SelectItem>
                  <SelectItem value="CAMERA">Camera</SelectItem>
                  <SelectItem value="SENSOR">Sensor</SelectItem>
                  <SelectItem value="OBD">OBD</SelectItem>
                  <SelectItem value="OTHER">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Serial Number</Label>
              <Input
                value={formData.serial_number}
                onChange={(e) =>
                  setFormData({ ...formData, serial_number: e.target.value })
                }
              />
            </div>
            <div>
              <Label>Manufacturer</Label>
              <Input
                value={formData.manufacturer}
                onChange={(e) =>
                  setFormData({ ...formData, manufacturer: e.target.value })
                }
              />
            </div>
            <div>
              <Label>Model</Label>
              <Input
                value={formData.model}
                onChange={(e) =>
                  setFormData({ ...formData, model: e.target.value })
                }
              />
            </div>
            <div>
              <Label>Firmware Version</Label>
              <Input
                value={formData.firmware_version}
                onChange={(e) =>
                  setFormData({ ...formData, firmware_version: e.target.value })
                }
              />
            </div>
            <div>
              <Label>Status</Label>
              <Select
                value={formData.status}
                onValueChange={(value) =>
                  setFormData({ ...formData, status: value })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ONLINE">Online</SelectItem>
                  <SelectItem value="OFFLINE">Offline</SelectItem>
                  <SelectItem value="ERROR">Error</SelectItem>
                  <SelectItem value="MAINTENANCE">Maintenance</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleUpdate}>Update Device</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
