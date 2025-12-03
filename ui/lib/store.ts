import { create } from 'zustand';

interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  is_superuser?: boolean;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  setUser: (user: User | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  setUser: (user) => set({ user, isAuthenticated: !!user }),
  logout: () => set({ user: null, isAuthenticated: false }),
}));

interface Vehicle {
  id: number;
  license_plate: string;
  make: string;
  model: string;
  year: number;
  status: string;
  current_driver?: any;
}

interface VehicleState {
  vehicles: Vehicle[];
  selectedVehicle: Vehicle | null;
  setVehicles: (vehicles: Vehicle[]) => void;
  setSelectedVehicle: (vehicle: Vehicle | null) => void;
}

export const useVehicleStore = create<VehicleState>((set) => ({
  vehicles: [],
  selectedVehicle: null,
  setVehicles: (vehicles) => set({ vehicles }),
  setSelectedVehicle: (vehicle) => set({ selectedVehicle: vehicle }),
}));

interface GPSLocation {
  id: number;
  vehicle_id: number;
  latitude: number;
  longitude: number;
  speed?: number;
  heading?: number;
  timestamp: string;
}

interface TrackingState {
  liveLocations: GPSLocation[];
  setLiveLocations: (locations: GPSLocation[]) => void;
  updateLocation: (location: GPSLocation) => void;
}

export const useTrackingStore = create<TrackingState>((set) => ({
  liveLocations: [],
  setLiveLocations: (locations) => set({ liveLocations: locations }),
  updateLocation: (location) =>
    set((state) => {
      const existing = state.liveLocations.findIndex(
        (l) => l.vehicle_id === location.vehicle_id
      );
      if (existing >= 0) {
        const updated = [...state.liveLocations];
        updated[existing] = location;
        return { liveLocations: updated };
      }
      return { liveLocations: [...state.liveLocations, location] };
    }),
}));
