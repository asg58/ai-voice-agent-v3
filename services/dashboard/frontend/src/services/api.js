import axios from 'axios';

// Create axios instance with default config
const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Add response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle 401 Unauthorized errors
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Dashboard API functions
export const getDashboardSummary = () => api.get('/dashboard/summary');
export const getServices = () => api.get('/dashboard/services');
export const getService = (id) => api.get(`/dashboard/services/${id}`);
export const getSystemMetrics = () => api.get('/dashboard/metrics/system');
export const getServiceMetrics = () => api.get('/dashboard/metrics/services');
export const getAlerts = () => api.get('/dashboard/alerts');
export const acknowledgeAlert = (id) => api.put(`/dashboard/alerts/${id}/acknowledge`);

// Auth API functions
export const login = (username, password) => 
  api.post('/auth/login', { username, password });
export const getCurrentUser = () => api.get('/auth/me');

export default api;