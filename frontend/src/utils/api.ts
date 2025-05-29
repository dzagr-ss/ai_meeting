import axios, { AxiosResponse, AxiosError } from 'axios';
import { store } from '../store';
import { logout } from '../store/slices/authSlice';

// Create axios instance
const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 30000, // 30 seconds timeout
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const state = store.getState();
    const token = state.auth.token;
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token expiration
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error: AxiosError) => {
    // Check if error is due to token expiration
    if (error.response?.status === 401) {
      const errorDetail = (error.response.data as any)?.detail;
      
      // Check for token expiration or authentication failure
      if (
        errorDetail === 'Could not validate credentials' ||
        errorDetail === 'Token has expired' ||
        errorDetail === 'Invalid token' ||
        error.response.statusText === 'Unauthorized'
      ) {
        console.log('Token expired or invalid, logging out user');
        
        // Dispatch logout action
        store.dispatch(logout());
        
        // Redirect to login page
        window.location.href = '/login';
        
        // Show user-friendly message
        const event = new CustomEvent('tokenExpired', {
          detail: { message: 'Your session has expired. Please log in again.' }
        });
        window.dispatchEvent(event);
      }
    }
    
    return Promise.reject(error);
  }
);

// Utility function to check if token is expired (client-side check)
export const isTokenExpired = (token: string | null): boolean => {
  if (!token) return true;
  
  try {
    // Decode JWT token (without verification, just to check expiration)
    const payload = JSON.parse(atob(token.split('.')[1]));
    const currentTime = Date.now() / 1000;
    
    return payload.exp < currentTime;
  } catch (error) {
    console.error('Error decoding token:', error);
    return true;
  }
};

// Utility function to handle token expiration manually (for fetch calls)
export const handleTokenExpiration = (response: Response) => {
  if (response.status === 401) {
    console.log('Token expired (fetch), logging out user');
    
    // Dispatch logout action
    store.dispatch(logout());
    
    // Redirect to login page
    window.location.href = '/login';
    
    // Show user-friendly message
    const event = new CustomEvent('tokenExpired', {
      detail: { message: 'Your session has expired. Please log in again.' }
    });
    window.dispatchEvent(event);
  }
};

// Enhanced fetch wrapper that handles token expiration
export const fetchWithAuth = async (url: string, options: RequestInit = {}): Promise<Response> => {
  const state = store.getState();
  const token = state.auth.token;
  
  // Check if token is expired before making request
  if (isTokenExpired(token)) {
    console.log('Token is expired, logging out user');
    store.dispatch(logout());
    window.location.href = '/login';
    throw new Error('Token expired');
  }
  
  // Add authorization header
  const headers = {
    ...options.headers,
    ...(token && { Authorization: `Bearer ${token}` }),
  };
  
  const response = await fetch(url, {
    ...options,
    headers,
  });
  
  // Handle token expiration
  handleTokenExpiration(response);
  
  return response;
};

export default api; 