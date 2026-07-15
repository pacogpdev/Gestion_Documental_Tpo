import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  // No default Content-Type — Axios auto-detects:
  //   - objects/JSON → application/json
  //   - FormData → multipart/form-data (with boundary)
});

// Add a request interceptor to include the JWT token from localStorage
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export default apiClient;
