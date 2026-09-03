import axios from 'axios';

export type TokenProvider = () => Promise<string | null>;
let tokenProvider: TokenProvider = async () => null;
let onUnauthorized = () => {};
let onAccessDenied = () => {};

export const setTokenProvider = (provider: TokenProvider) => { tokenProvider = provider; };
export const setUnauthorizedHandler = (handler: () => void) => { onUnauthorized = handler; };
export const setAccessDeniedHandler = (handler: () => void) => { onAccessDenied = handler; };

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  // No default Content-Type — Axios auto-detects:
  //   - objects/JSON → application/json
  //   - FormData → multipart/form-data (with boundary)
});

apiClient.interceptors.request.use(
  async (config) => {
    const token = await tokenProvider();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) onUnauthorized();
    if (error.response?.status === 403) onAccessDenied();
    return Promise.reject(error);
  },
);

export default apiClient;
