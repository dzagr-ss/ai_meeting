import axios, { AxiosResponse, AxiosError } from 'axios';
import { store } from '../store';
import { logout } from '../store/slices/authSlice';

// Environment-aware API URL configuration
const getApiUrl = (): string => {
  // Production URL from environment variable
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  
  console.log('API URL:', getApiUrl());
  console.log('REACT_APP_API_URL env var:', process.env.REACT_APP_API_URL);
  console.log('NODE_ENV:', process.env.NODE_ENV);


  // Development fallback
  if (process.env.NODE_ENV === 'development') {
    return 'http://localhost:8000';
  }

  // Production fallback (REPLACE THIS WITH YOUR ACTUAL RAILWAY BACKEND URL)
  return 'https://aimeeting.up.railway.app';
};

// Input validation and sanitization utilities
export const sanitizeInput = (input: string): string => {
  if (!input) return '';
  
  // HTML escape
  return input
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;')
    .replace(/\//g, '&#x2F;');
};

export const validateEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email) && email.length <= 254;
};

export const validatePassword = (password: string): { isValid: boolean; errors: string[] } => {
  const errors: string[] = [];
  
  if (password.length < 8) {
    errors.push('Password must be at least 8 characters long');
  }
  if (password.length > 128) {
    errors.push('Password must be less than 128 characters');
  }
  if (!/[A-Z]/.test(password)) {
    errors.push('Password must contain at least one uppercase letter');
  }
  if (!/[a-z]/.test(password)) {
    errors.push('Password must contain at least one lowercase letter');
  }
  if (!/\d/.test(password)) {
    errors.push('Password must contain at least one number');
  }
  if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    errors.push('Password must contain at least one special character');
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
};

export const validateMeetingTitle = (title: string): { isValid: boolean; error?: string } => {
  if (!title || title.trim().length === 0) {
    return { isValid: false, error: 'Title cannot be empty' };
  }
  if (title.length > 200) {
    return { isValid: false, error: 'Title must be less than 200 characters' };
  }
  
  // Check for dangerous characters
  const dangerousChars = /<script|javascript:|data:|vbscript:|onload|onerror/i;
  if (dangerousChars.test(title)) {
    return { isValid: false, error: 'Title contains invalid characters' };
  }
  
  return { isValid: true };
};

export const validateFileUpload = (file: File): { isValid: boolean; error?: string } => {
  const allowedTypes = ['audio/wav', 'audio/mpeg', 'audio/mp3', 'audio/mp4', 'audio/m4a', 'audio/flac', 'audio/ogg', 'audio/aac', 'audio/webm'];
  const maxSize = 50 * 1024 * 1024; // 50MB
  
  if (!allowedTypes.includes(file.type)) {
    return { isValid: false, error: 'Invalid file type. Only audio files are allowed.' };
  }
  
  if (file.size > maxSize) {
    return { isValid: false, error: 'File size too large. Maximum size is 50MB.' };
  }
  
  if (file.name.length > 255) {
    return { isValid: false, error: 'Filename too long.' };
  }
  
  // Check for dangerous characters in filename
  const dangerousChars = /[<>:"/\\|?*]/;
  const hasControlChars = file.name.split('').some(char => {
    const code = char.charCodeAt(0);
    return code >= 0 && code <= 31; // Control characters (0x00-0x1F)
  });
  
  if (dangerousChars.test(file.name) || hasControlChars) {
    return { isValid: false, error: 'Filename contains invalid characters.' };
  }
  
  return { isValid: true };
};

export const sanitizeFormData = (data: Record<string, any>): Record<string, any> => {
  const sanitized: Record<string, any> = {};
  
  for (const [key, value] of Object.entries(data)) {
    if (typeof value === 'string') {
      sanitized[key] = sanitizeInput(value);
    } else {
      sanitized[key] = value;
    }
  }
  
  return sanitized;
};

// Rate limiting for client-side requests
class RateLimiter {
  private requests: Map<string, number[]> = new Map();
  
  isAllowed(key: string, maxRequests: number, windowMs: number): boolean {
    const now = Date.now();
    const windowStart = now - windowMs;
    
    if (!this.requests.has(key)) {
      this.requests.set(key, []);
    }
    
    const requests = this.requests.get(key)!;
    
    // Remove old requests outside the window
    const validRequests = requests.filter(time => time > windowStart);
    this.requests.set(key, validRequests);
    
    if (validRequests.length >= maxRequests) {
      return false;
    }
    
    validRequests.push(now);
    this.requests.set(key, validRequests);
    return true;
  }
}

const rateLimiter = new RateLimiter();

// Create axios instance with environment-aware configuration
const api = axios.create({
  baseURL: getApiUrl(),
  timeout: 30000, // 30 seconds timeout
  withCredentials: false, // Disable credentials for security
});

// Log the API URL for debugging (only in development)
if (process.env.NODE_ENV === 'development') {
  console.log('API URL:', getApiUrl());
}

// Request interceptor to add auth token and validate requests
api.interceptors.request.use(
  (config) => {
    const state = store.getState();
    const token = state.auth.token;
    
    // Rate limiting check
    const endpoint = `${config.method?.toUpperCase()}_${config.url}`;
    if (!rateLimiter.isAllowed(endpoint, 100, 60000)) { // 100 requests per minute
      throw new Error('Rate limit exceeded. Please slow down your requests.');
    }
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Add security headers
    config.headers['X-Requested-With'] = 'XMLHttpRequest';
    config.headers['Cache-Control'] = 'no-cache';
    
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
    'X-Requested-With': 'XMLHttpRequest',
    'Cache-Control': 'no-cache',
    ...options.headers,
    ...(token && { Authorization: `Bearer ${token}` }),
  };
  
  const response = await fetch(url, {
    ...options,
    headers,
    credentials: 'omit', // Don't send credentials for security
  });
  
  // Handle token expiration
  handleTokenExpiration(response);
  
  return response;
};

export default api; 