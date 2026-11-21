import axios from 'axios';

// Dedicated API Client for CYNERA SaaS Central Platform
const configuredUrl = import.meta.env.VITE_API_URL;
export const API_BASE_URL = configuredUrl || 'http://127.0.0.1:8000';

// In local development, use relative '/api' so Vite dev server proxy seamlessly handles requests without CORS
const isDev = import.meta.env.DEV;
const effectiveBaseURL = (isDev && (!configuredUrl || configuredUrl.includes('localhost') || configuredUrl.includes('127.0.0.1')))
  ? '/api'
  : (configuredUrl ? `${configuredUrl.replace(/\/$/, '')}/api` : '/api');

const api = axios.create({
  baseURL: effectiveBaseURL,
  timeout: 15000,
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
