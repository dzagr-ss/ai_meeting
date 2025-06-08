import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface User {
  email: string;
  user_type?: string;
  exp?: number;
}

interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
}

// Utility function to decode user info from JWT token
const decodeUserFromToken = (token: string | null): User | null => {
  if (!token) return null;
  
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return {
      email: payload.sub,
      user_type: payload.user_type,
      exp: payload.exp
    };
  } catch (error) {
    console.error('Error decoding user from token:', error);
    return null;
  }
};

// Utility function to check if token is expired
const isTokenExpired = (token: string | null): boolean => {
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

// Check initial token validity
const storedToken = localStorage.getItem('token');
const isValidToken = !!(storedToken && !isTokenExpired(storedToken));
const storedUser = isValidToken ? decodeUserFromToken(storedToken) : null;

const initialState: AuthState = {
  token: isValidToken ? storedToken : null,
  user: storedUser,
  isAuthenticated: isValidToken,
  loading: false,
  error: null,
};

// Clear invalid token from localStorage if it exists
if (storedToken && !isValidToken) {
  localStorage.removeItem('token');
}

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    loginStart: (state) => {
      state.loading = true;
      state.error = null;
    },
    loginSuccess: (state, action: PayloadAction<string>) => {
      state.loading = false;
      state.isAuthenticated = true;
      state.token = action.payload;
      state.user = decodeUserFromToken(action.payload);
      localStorage.setItem('token', action.payload);
    },
    loginFailure: (state, action: PayloadAction<string>) => {
      state.loading = false;
      state.error = action.payload;
    },
    logout: (state) => {
      state.token = null;
      state.user = null;
      state.isAuthenticated = false;
      localStorage.removeItem('token');
    },
    validateToken: (state) => {
      if (state.token && isTokenExpired(state.token)) {
        state.token = null;
        state.user = null;
        state.isAuthenticated = false;
        localStorage.removeItem('token');
      }
    },
  },
});

export const { loginStart, loginSuccess, loginFailure, logout, validateToken } = authSlice.actions;
export default authSlice.reducer; 