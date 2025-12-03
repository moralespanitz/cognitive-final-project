'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { vehiclesApi } from '@/lib/api';
import { useVehicleStore } from '@/lib/store';
import { CarIcon, SearchIcon, PlusIcon, EditIcon, TrashIcon } from 'lucide-react';

export default function VehiclesPage() {
  const router = useRouter();
  const { vehicles, setVehicles } = useVehicleStore();
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('ALL');
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [selectedVehicle, setSelectedVehicle] = useState<any>(null);
  const [formData, setFormData] = useState({
    license_plate: '',
    make: '',
    model: '',
    year: new Date().getFullYear(),
    vin: '',
    color: '',
    status: 'ACTIVE'
  });

  useEffect(() => {
    loadVehicles();
  }, []);

  const loadVehicles = async () => {
    try {
      const data = await vehiclesApi.getAll();
      setVehicles(data);
    } catch (error) {
      console.error('Failed to load vehicles:', error);
    } finally {
      setLoading(false);
    }
  };

  const resetFormData = () => {
    setFormData({
      license_plate: '',
      make: '',
      model: '',
      year: new Date().getFullYear(),
      vin: '',
      color: '',
      status: 'ACTIVE'
    });
  };

  const handleCreateClick = () => {
    resetFormData();
    setShowCreateDialog(true);
  };

  const handleEditClick = (vehicle: any, e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedVehicle(vehicle);
    setFormData({
      license_plate: vehicle.license_plate,
      make: vehicle.make,
      model: vehicle.model,
      year: vehicle.year,
      vin: vehicle.vin,
      color: vehicle.color || '',
      status: vehicle.status
    });
    setShowEditDialog(true);
  };

  const handleCreateVehicle = async () => {
    try {
      if (!formData.license_plate || !formData.make || !formData.model || !formData.vin) {
        alert('Please fill in all required fields');
        return;
      }
      await vehiclesApi.create(formData);
      setShowCreateDialog(false);
      resetFormData();
      await loadVehicles();
    } catch (error) {
      console.error('Failed to create vehicle:', error);
      alert('Failed to create vehicle');
    }
  };

  const handleUpdateVehicle = async () => {
    try {
      if (!selectedVehicle) return;
      if (!formData.license_plate || !formData.make || !formData.model || !formData.vin) {
        alert('Please fill in all required fields');
        return;
      }
      await vehiclesApi.update(selectedVehicle.id, formData);
      setShowEditDialog(false);
      resetFormData();
      setSelectedVehicle(null);
      await loadVehicles();
    } catch (error) {
      console.error('Failed to update vehicle:', error);
      alert('Failed to update vehicle');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this vehicle?')) return;

    try {
      await vehiclesApi.delete(id);
      await loadVehicles();
    } catch (error) {
      console.error('Failed to delete vehicle:', error);
      alert('Failed to delete vehicle');
    }
  };

  const filteredVehicles = vehicles.filter((vehicle: any) => {
    const matchesSearch =
      vehicle.license_plate?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      vehicle.make?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      vehicle.model?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus = filterStatus === 'ALL' || vehicle.status === filterStatus;

    return matchesSearch && matchesStatus;
  });

  const getStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      ACTIVE: 'bg-green-100 text-green-800',
      MAINTENANCE: 'bg-yellow-100 text-yellow-800',
      OUT_OF_SERVICE: 'bg-red-100 text-red-800'
    };

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[status] || 'bg-gray-100 text-gray-800'}`}>
        {status.replace('_', ' ')}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <p className="text-gray-600">Loading vehicles...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Vehicles</h1>
          <p className="text-gray-600">Manage your fleet vehicles</p>
        </div>
        <Button onClick={handleCreateClick} className="bg-blue-600 hover:bg-blue-700">
          <PlusIcon className="h-4 w-4 mr-2" />
          Add Vehicle
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Fleet Overview</CardTitle>
          <CardDescription>
            Total: {vehicles.length} vehicles
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 mb-6">
            <div className="flex-1">
              <div className="relative">
                <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search by license plate, make, or model..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-4 py-2 border rounded-lg bg-white"
            >
              <option value="ALL">All Status</option>
              <option value="ACTIVE">Active</option>
              <option value="MAINTENANCE">Maintenance</option>
              <option value="OUT_OF_SERVICE">Out of Service</option>
            </select>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4 font-medium text-gray-700">License Plate</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-700">Make & Model</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-700">Year</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-700">Status</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-700">VIN</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-700">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredVehicles.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-8 text-gray-500">
                      No vehicles found
                    </td>
                  </tr>
                ) : (
                  filteredVehicles.map((vehicle: any) => (
                    <tr
                      key={vehicle.id}
                      className="border-b hover:bg-gray-50 cursor-pointer"
                      onClick={() => router.push(`/vehicles/${vehicle.id}`)}
                    >
                      <td className="py-3 px-4 font-medium">{vehicle.license_plate}</td>
                      <td className="py-3 px-4">
                        {vehicle.make} {vehicle.model}
                      </td>
                      <td className="py-3 px-4">{vehicle.year}</td>
                      <td className="py-3 px-4">
                        {getStatusBadge(vehicle.status)}
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-600">{vehicle.vin}</td>
                      <td className="py-3 px-4">
                        <div className="flex gap-2 justify-end" onClick={(e) => e.stopPropagation()}>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={(e) => handleEditClick(vehicle, e)}
                          >
                            <EditIcon className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDelete(vehicle.id)}
                            className="text-red-600 hover:text-red-700"
                          >
                            <TrashIcon className="h-4 w-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600">
                {vehicles.filter((v: any) => v.status === 'ACTIVE').length}
              </div>
              <p className="text-sm text-gray-600 mt-1">Active Vehicles</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-yellow-600">
                {vehicles.filter((v: any) => v.status === 'MAINTENANCE').length}
              </div>
              <p className="text-sm text-gray-600 mt-1">In Maintenance</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-red-600">
                {vehicles.filter((v: any) => v.status === 'OUT_OF_SERVICE').length}
              </div>
              <p className="text-sm text-gray-600 mt-1">Out of Service</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Create Vehicle Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Add New Vehicle</DialogTitle>
            <DialogDescription>Register a new vehicle to the fleet</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="license_plate">License Plate *</Label>
                <Input
                  id="license_plate"
                  value={formData.license_plate}
                  onChange={(e) => setFormData({ ...formData, license_plate: e.target.value })}
                  placeholder="e.g., ABC-123"
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="color">Color</Label>
                <Input
                  id="color"
                  value={formData.color}
                  onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                  placeholder="e.g., White"
                />
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="make">Make *</Label>
                <Input
                  id="make"
                  value={formData.make}
                  onChange={(e) => setFormData({ ...formData, make: e.target.value })}
                  placeholder="e.g., Toyota"
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="model">Model *</Label>
                <Input
                  id="model"
                  value={formData.model}
                  onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                  placeholder="e.g., Prius"
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="year">Year *</Label>
                <Input
                  id="year"
                  type="number"
                  value={formData.year}
                  onChange={(e) => setFormData({ ...formData, year: parseInt(e.target.value) })}
                  placeholder="2024"
                />
              </div>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="vin">VIN *</Label>
              <Input
                id="vin"
                value={formData.vin}
                onChange={(e) => setFormData({ ...formData, vin: e.target.value })}
                placeholder="Vehicle Identification Number"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="status">Status *</Label>
              <select
                id="status"
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                className="px-3 py-2 border rounded-lg bg-white"
              >
                <option value="ACTIVE">Active</option>
                <option value="MAINTENANCE">Maintenance</option>
                <option value="OUT_OF_SERVICE">Out of Service</option>
              </select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateVehicle} className="bg-blue-600 hover:bg-blue-700">
              Add Vehicle
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Vehicle Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Edit Vehicle</DialogTitle>
            <DialogDescription>Update vehicle information</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="edit_license_plate">License Plate *</Label>
                <Input
                  id="edit_license_plate"
                  value={formData.license_plate}
                  onChange={(e) => setFormData({ ...formData, license_plate: e.target.value })}
                  placeholder="e.g., ABC-123"
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="edit_color">Color</Label>
                <Input
                  id="edit_color"
                  value={formData.color}
                  onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                  placeholder="e.g., White"
                />
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="edit_make">Make *</Label>
                <Input
                  id="edit_make"
                  value={formData.make}
                  onChange={(e) => setFormData({ ...formData, make: e.target.value })}
                  placeholder="e.g., Toyota"
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="edit_model">Model *</Label>
                <Input
                  id="edit_model"
                  value={formData.model}
                  onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                  placeholder="e.g., Prius"
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="edit_year">Year *</Label>
                <Input
                  id="edit_year"
                  type="number"
                  value={formData.year}
                  onChange={(e) => setFormData({ ...formData, year: parseInt(e.target.value) })}
                  placeholder="2024"
                />
              </div>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="edit_vin">VIN *</Label>
              <Input
                id="edit_vin"
                value={formData.vin}
                onChange={(e) => setFormData({ ...formData, vin: e.target.value })}
                placeholder="Vehicle Identification Number"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="edit_status">Status *</Label>
              <select
                id="edit_status"
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                className="px-3 py-2 border rounded-lg bg-white"
              >
                <option value="ACTIVE">Active</option>
                <option value="MAINTENANCE">Maintenance</option>
                <option value="OUT_OF_SERVICE">Out of Service</option>
              </select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleUpdateVehicle} className="bg-blue-600 hover:bg-blue-700">
              Update Vehicle
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
