import axios from 'axios';

// Dedicated API Client for CYNERA SaaS Central Platform
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL 
    ? `${import.meta.env.VITE_API_URL}/api`
    : '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Request interceptor: attach active JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('cynera_token') || localStorage.getItem('cicada_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: handle unauthorized errors gracefully
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('cynera_token');
      localStorage.removeItem('cynera_user');
      localStorage.removeItem('cicada_token');
      localStorage.removeItem('cicada_user');
    }
    return Promise.reject(error);
  }
);

export default api;
