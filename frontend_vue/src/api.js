import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api', // FastAPI URL
  timeout: 30000,
});

export default api;
