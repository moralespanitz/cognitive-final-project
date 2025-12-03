import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        });

        const { access_token, refresh_token } = response.data;
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);

        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  login: async (username: string, password: string) => {
    const response = await api.post('/auth/login', { username, password });
    return response.data;
  },

  register: async (data: {
    username: string;
    email: string;
    password: string;
    first_name: string;
    last_name: string;
    role: string;
  }) => {
    const response = await api.post('/auth/register', data);
    return response.data;
  },

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  },
};

// Vehicles API
export const vehiclesApi = {
  getAll: async () => {
    const response = await api.get('/vehicles');
    return response.data;
  },

  getById: async (id: number) => {
    const response = await api.get(`/vehicles/${id}`);
    return response.data;
  },

  create: async (data: any) => {
    const response = await api.post('/vehicles', data);
    return response.data;
  },

  update: async (id: number, data: any) => {
    const response = await api.patch(`/vehicles/${id}`, data);
    return response.data;
  },

  delete: async (id: number) => {
    const response = await api.delete(`/vehicles/${id}`);
    return response.data;
  },
};

// Tracking API
export const trackingApi = {
  getLiveLocations: async () => {
    const response = await api.get('/tracking/live');
    return response.data;
  },

  getVehicleHistory: async (vehicleId: number, hours: number = 24) => {
    const response = await api.get(`/tracking/vehicle/${vehicleId}/history`, {
      params: { hours },
    });
    return response.data;
  },
};

// Chat API
export const chatApi = {
  sendMessage: async (message: string) => {
    const response = await api.post('/chat', { message });
    return response.data;
  },
};

// Users API
export const usersApi = {
  getAll: async () => {
    const response = await api.get('/users');
    return response.data;
  },

  getById: async (id: number) => {
    const response = await api.get(`/users/${id}`);
    return response.data;
  },

  create: async (data: any) => {
    const response = await api.post('/users', data);
    return response.data;
  },

  update: async (id: number, data: any) => {
    const response = await api.patch(`/users/${id}`, data);
    return response.data;
  },

  delete: async (id: number) => {
    const response = await api.delete(`/users/${id}`);
    return response.data;
  },
};

// Devices API
export const devicesApi = {
  getAll: async (vehicleId?: number) => {
    const response = await api.get('/devices', {
      params: vehicleId ? { vehicle_id: vehicleId } : {},
    });
    return response.data;
  },

  getById: async (id: number) => {
    const response = await api.get(`/devices/${id}`);
    return response.data;
  },

  create: async (data: any) => {
    const response = await api.post('/devices', data);
    return response.data;
  },

  update: async (id: number, data: any) => {
    const response = await api.patch(`/devices/${id}`, data);
    return response.data;
  },

  delete: async (id: number) => {
    const response = await api.delete(`/devices/${id}`);
    return response.data;
  },

  ping: async (id: number) => {
    const response = await api.post(`/devices/${id}/ping`);
    return response.data;
  },
};

// FAQs API
export const faqsApi = {
  getAll: async (category?: string) => {
    const response = await api.get('/faqs', {
      params: category ? { category } : {},
    });
    return response.data;
  },

  getById: async (id: number) => {
    const response = await api.get(`/faqs/${id}`);
    return response.data;
  },

  create: async (data: any) => {
    const response = await api.post('/faqs', data);
    return response.data;
  },

  update: async (id: number, data: any) => {
    const response = await api.patch(`/faqs/${id}`, data);
    return response.data;
  },

  delete: async (id: number) => {
    const response = await api.delete(`/faqs/${id}`);
    return response.data;
  },
};

// Face Recognition API
export const facesApi = {
  register: async (faceImage: string) => {
    const response = await api.post('/faces/register', { face_image: faceImage });
    return response.data;
  },

  verify: async (userId: number, faceImage: string) => {
    const response = await api.post('/faces/verify', { user_id: userId, face_image: faceImage });
    return response.data;
  },

  verifySelf: async (faceImage: string) => {
    const response = await api.post('/faces/verify-self', { face_image: faceImage });
    return response.data;
  },

  getMyRegistration: async () => {
    const response = await api.get('/faces/me');
    return response.data;
  },

  getStatus: async () => {
    const response = await api.get('/faces/status');
    return response.data;
  },

  deleteMyFace: async () => {
    const response = await api.delete('/faces/me');
    return response.data;
  },

  // Admin endpoints
  getAllRegistrations: async () => {
    const response = await api.get('/faces/admin/all');
    return response.data;
  },

  getLogs: async (limit: number = 50) => {
    const response = await api.get('/faces/admin/logs', { params: { limit } });
    return response.data;
  },

  getSettings: async () => {
    const response = await api.get('/faces/admin/settings');
    return response.data;
  },

  updateSettings: async (similarityThreshold: number) => {
    const response = await api.put('/faces/admin/settings', { similarity_threshold: similarityThreshold });
    return response.data;
  },

  adminDeleteFace: async (userId: number) => {
    const response = await api.delete(`/faces/admin/${userId}`);
    return response.data;
  },
};

// Trip Images API
export const imagesApi = {
  getTripImages: async (tripId: number) => {
    const response = await api.get(`/images/trip/${tripId}`);
    return response.data;
  },

  getHistory: async (params?: { start_date?: string; end_date?: string; limit?: number; offset?: number }) => {
    const response = await api.get('/images/history', { params });
    return response.data;
  },

  getLatest: async (tripId: number) => {
    const response = await api.get(`/images/latest/${tripId}`);
    return response.data;
  },

  delete: async (imageId: number) => {
    const response = await api.delete(`/images/${imageId}`);
    return response.data;
  },
};

// Trips API
export const tripsApi = {
  request: async (data: { pickup_location: any; destination: any; verification_image?: string }) => {
    const response = await api.post('/trips/request', data);
    return response.data;
  },

  getById: async (id: number) => {
    const response = await api.get(`/trips/${id}`);
    return response.data;
  },

  getAll: async (params?: { status?: string; driver_id?: number; vehicle_id?: number }) => {
    const response = await api.get('/trips', { params });
    return response.data;
  },

  accept: async (id: number) => {
    const response = await api.post(`/trips/${id}/accept`);
    return response.data;
  },

  arrive: async (id: number) => {
    const response = await api.post(`/trips/${id}/arrive`);
    return response.data;
  },

  start: async (id: number) => {
    const response = await api.post(`/trips/${id}/start`);
    return response.data;
  },

  complete: async (id: number) => {
    const response = await api.post(`/trips/${id}/complete`);
    return response.data;
  },

  cancel: async (id: number) => {
    const response = await api.post(`/trips/${id}/cancel`);
    return response.data;
  },
};
