import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'https://keday70-api-production.up.railway.app/api',
  timeout: 30000,
});

export default api;
