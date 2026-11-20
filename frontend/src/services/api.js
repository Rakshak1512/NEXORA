import axios from 'axios';

// Centralized API Base URL strictly derived from VITE_API_URL
const rawBase = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
const cleanBase = rawBase.replace(/\/+$/, '');
export const API_BASE_URL = cleanBase;
export const API_ENDPOINT = cleanBase.endsWith('/api') ? cleanBase : `${cleanBase}/api`;

const api = axios.create({
  baseURL: API_ENDPOINT,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('cicada_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('cicada_token');
      localStorage.removeItem('cicada_user');
    }
    return Promise.reject(error);
  }
);

export default api;
