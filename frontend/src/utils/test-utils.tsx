import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import { configureStore } from '@reduxjs/toolkit';
import authReducer from '../store/slices/authSlice';
import themeReducer from '../store/slices/themeSlice';
import meetingReducer from '../store/slices/meetingSlice';
import { createAppTheme } from '../theme';

// Default store configuration for tests
export const createTestStore = (preloadedState?: any) => {
  return configureStore({
    reducer: {
      auth: authReducer,
      meeting: meetingReducer,
      theme: themeReducer,
    },
    preloadedState,
  });
};

// Test wrapper component that provides all necessary providers
interface AllTheProvidersProps {
  children: React.ReactNode;
  initialState?: any;
  theme?: 'light' | 'dark';
}

const AllTheProviders: React.FC<AllTheProvidersProps> = ({ 
  children, 
  initialState,
  theme = 'light'
}) => {
  const store = createTestStore(initialState);
  const muiTheme = createAppTheme(theme);

  return (
    <Provider store={store}>
      <BrowserRouter>
        <ThemeProvider theme={muiTheme}>
          <CssBaseline />
          {children}
        </ThemeProvider>
      </BrowserRouter>
    </Provider>
  );
};

// Custom render function
const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'> & {
    initialState?: any;
    theme?: 'light' | 'dark';
  }
) => {
  const { initialState, theme, ...renderOptions } = options || {};
  
  return render(ui, {
    wrapper: (props) => (
      <AllTheProviders 
        initialState={initialState} 
        theme={theme}
        {...props} 
      />
    ),
    ...renderOptions,
  });
};

// Re-export everything
export * from '@testing-library/react';
export { customRender as render };

// Common test data factories
export const createMockUser = (overrides = {}) => ({
  email: 'test@example.com',
  user_type: 'normal',
  exp: Math.floor(Date.now() / 1000) + 3600, // 1 hour from now
  ...overrides,
});

export const createMockAuthState = (overrides = {}) => ({
  token: 'mock-jwt-token',
  user: createMockUser(),
  isAuthenticated: true,
  loading: false,
  error: null,
  ...overrides,
});

export const createMockMeeting = (overrides = {}) => ({
  id: 1,
  title: 'Test Meeting',
  description: 'A test meeting',
  status: 'active',
  created_at: new Date().toISOString(),
  tags: [],
  owner_id: 1,
  ...overrides,
});

export const createMockTag = (overrides = {}) => ({
  id: 1,
  name: 'test-tag',
  color: '#ff0000',
  ...overrides,
});

// Mock implementations for common APIs
export const mockAxios = {
  get: jest.fn(() => Promise.resolve({ data: {} })),
  post: jest.fn(() => Promise.resolve({ data: {} })),
  put: jest.fn(() => Promise.resolve({ data: {} })),
  delete: jest.fn(() => Promise.resolve({ data: {} })),
  patch: jest.fn(() => Promise.resolve({ data: {} })),
};

// Helper function to mock localStorage with data
export const mockLocalStorage = (data: Record<string, string> = {}) => {
  const localStorageMock = {
    getItem: jest.fn((key: string) => data[key] || null),
    setItem: jest.fn((key: string, value: string) => {
      data[key] = value;
    }),
    removeItem: jest.fn((key: string) => {
      delete data[key];
    }),
    clear: jest.fn(() => {
      Object.keys(data).forEach(key => delete data[key]);
    }),
  };
  
  Object.defineProperty(window, 'localStorage', {
    value: localStorageMock,
  });
  
  return localStorageMock;
};

// Helper to wait for async operations
export const waitForAsync = () => new Promise(resolve => setTimeout(resolve, 0));

// Mock timers helper
export const mockTimers = () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });
};

// Mock fetch for API calls
export const mockFetch = (responseData: any, status = 200) => {
  global.fetch = jest.fn(() =>
    Promise.resolve({
      ok: status >= 200 && status < 300,
      status,
      json: () => Promise.resolve(responseData),
      text: () => Promise.resolve(JSON.stringify(responseData)),
    })
  ) as jest.Mock;
};

// Helper to simulate user interactions
export const createUserEvent = async () => {
  const userEvent = (await import('@testing-library/user-event')).default;
  return userEvent;
};

// Default test IDs
export const testIds = {
  // Navigation
  navbar: 'navbar',
  loginButton: 'login-button',
  logoutButton: 'logout-button',
  
  // Forms
  emailInput: 'email-input',
  passwordInput: 'password-input',
  submitButton: 'submit-button',
  
  // Meeting
  meetingTitle: 'meeting-title',
  audioRecorder: 'audio-recorder',
  recordButton: 'record-button',
  
  // Common
  loadingSpinner: 'loading-spinner',
  errorMessage: 'error-message',
  successMessage: 'success-message',
} as const; 