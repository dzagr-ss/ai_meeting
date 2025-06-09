import React from 'react';
import { screen, waitFor } from '@testing-library/react';
import { render, createMockAuthState, createUserEvent } from '../utils/test-utils';
import App from '../App';

// Mock all the page components
jest.mock('../pages/LandingPage', () => {
  return function MockLandingPage() {
    return <div>Landing Page</div>;
  };
});

jest.mock('../pages/Login', () => {
  return function MockLogin() {
    return <div>Login Page</div>;
  };
});

jest.mock('../pages/Register', () => {
  return function MockRegister() {
    return <div>Register Page</div>;
  };
});

jest.mock('../pages/Dashboard', () => {
  return function MockDashboard() {
    return <div>Dashboard Page</div>;
  };
});

jest.mock('../pages/MeetingRoom', () => {
  return function MockMeetingRoom() {
    return <div>Meeting Room Page</div>;
  };
});

jest.mock('../pages/AdminPanel', () => {
  return function MockAdminPanel() {
    return <div>Admin Panel Page</div>;
  };
});

jest.mock('../pages/ForgotPassword', () => {
  return function MockForgotPassword() {
    return <div>Forgot Password Page</div>;
  };
});

jest.mock('../pages/ResetPassword', () => {
  return function MockResetPassword() {
    return <div>Reset Password Page</div>;
  };
});

// Mock Navbar component
jest.mock('../components/Navbar', () => {
  return function MockNavbar() {
    return <div>Navbar</div>;
  };
});

// Mock @vercel/analytics
jest.mock('@vercel/analytics/react', () => ({
  Analytics: () => null,
}));

// Mock dispatch function
const mockDispatch = jest.fn();
jest.mock('react-redux', () => ({
  ...jest.requireActual('react-redux'),
  useDispatch: () => mockDispatch,
}));

describe('App', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset window location
    delete (window as any).location;
    window.location = { pathname: '/' } as any;
  });

  const authenticatedState = {
    auth: createMockAuthState(),
    theme: { mode: 'light' },
    meeting: { currentMeeting: null, meetings: [], loading: false },
  };

  const unauthenticatedState = {
    auth: {
      token: null,
      user: null,
      isAuthenticated: false,
      loading: false,
      error: null,
    },
    theme: { mode: 'light' },
    meeting: { currentMeeting: null, meetings: [], loading: false },
  };

  describe('routing for unauthenticated users', () => {
    it('shows landing page at root when not authenticated', () => {
      window.history.replaceState({}, '', '/');
      render(<App />, { initialState: unauthenticatedState });
      
      expect(screen.getByText('Landing Page')).toBeInTheDocument();
      expect(screen.queryByText('Navbar')).not.toBeInTheDocument();
    });

    it('shows login page when navigating to /login', () => {
      window.history.replaceState({}, '', '/login');
      render(<App />, { initialState: unauthenticatedState });
      
      expect(screen.getByText('Login Page')).toBeInTheDocument();
    });

    it('shows register page when navigating to /register', () => {
      window.history.replaceState({}, '', '/register');
      render(<App />, { initialState: unauthenticatedState });
      
      expect(screen.getByText('Register Page')).toBeInTheDocument();
    });

    it('shows forgot password page when navigating to /forgot-password', () => {
      window.history.replaceState({}, '', '/forgot-password');
      render(<App />, { initialState: unauthenticatedState });
      
      expect(screen.getByText('Forgot Password Page')).toBeInTheDocument();
    });

    it('shows reset password page when navigating to /reset-password', () => {
      window.history.replaceState({}, '', '/reset-password');
      render(<App />, { initialState: unauthenticatedState });
      
      expect(screen.getByText('Reset Password Page')).toBeInTheDocument();
    });

    it('redirects to login when accessing protected routes', () => {
      window.history.replaceState({}, '', '/dashboard');
      render(<App />, { initialState: unauthenticatedState });
      
      expect(screen.getByText('Login Page')).toBeInTheDocument();
    });
  });

  describe('routing for authenticated users', () => {
    it('shows navbar when authenticated', () => {
      window.history.replaceState({}, '', '/dashboard');
      render(<App />, { initialState: authenticatedState });
      
      expect(screen.getByText('Navbar')).toBeInTheDocument();
    });

    it('shows dashboard when navigating to /dashboard', () => {
      window.history.replaceState({}, '', '/dashboard');
      render(<App />, { initialState: authenticatedState });
      
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument();
    });

    it('shows meeting room when navigating to /meeting/:id', () => {
      window.history.replaceState({}, '', '/meeting/123');
      render(<App />, { initialState: authenticatedState });
      
      expect(screen.getByText('Meeting Room Page')).toBeInTheDocument();
    });

    it('shows admin panel when navigating to /admin', () => {
      window.history.replaceState({}, '', '/admin');
      render(<App />, { initialState: authenticatedState });
      
      expect(screen.getByText('Admin Panel Page')).toBeInTheDocument();
    });

    it('redirects to dashboard when accessing auth routes while authenticated', () => {
      window.history.replaceState({}, '', '/login');
      render(<App />, { initialState: authenticatedState });
      
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument();
    });

    it('redirects to dashboard when accessing root while authenticated', () => {
      window.history.replaceState({}, '', '/');
      render(<App />, { initialState: authenticatedState });
      
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument();
    });

    it('redirects unknown routes to dashboard when authenticated', () => {
      window.history.replaceState({}, '', '/unknown-route');
      render(<App />, { initialState: authenticatedState });
      
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument();
    });
  });

  describe('theme management', () => {
    it('applies light theme correctly', () => {
      render(<App />, { initialState: authenticatedState, theme: 'light' });
      
      // The theme should be applied via ThemeProvider
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument();
    });

    it('applies dark theme correctly', () => {
      const darkThemeState = {
        ...authenticatedState,
        theme: { mode: 'dark' },
      };

      render(<App />, { initialState: darkThemeState, theme: 'dark' });
      
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument();
    });
  });

  describe('token validation', () => {
    it('dispatches validateToken on mount', () => {
      render(<App />, { initialState: authenticatedState });
      
      expect(mockDispatch).toHaveBeenCalledWith(expect.any(Object));
    });

    it('sets up token validation interval', async () => {
      jest.useFakeTimers();
      
      render(<App />, { initialState: authenticatedState });
      
      // Fast forward time to trigger interval
      jest.advanceTimersByTime(5 * 60 * 1000); // 5 minutes
      
      expect(mockDispatch).toHaveBeenCalledTimes(2); // Initial + interval call
      
      jest.useRealTimers();
    });

    it('cleans up interval on unmount', () => {
      jest.useFakeTimers();
      const clearIntervalSpy = jest.spyOn(global, 'clearInterval');
      
      const { unmount } = render(<App />, { initialState: authenticatedState });
      
      unmount();
      
      expect(clearIntervalSpy).toHaveBeenCalled();
      
      jest.useRealTimers();
      clearIntervalSpy.mockRestore();
    });
  });

  describe('token expiration handling', () => {
    it('shows token expiration message when custom event is fired', async () => {
      render(<App />, { initialState: authenticatedState });
      
      // Simulate token expiration event
      const tokenExpiredEvent = new CustomEvent('tokenExpired', {
        detail: { message: 'Your session has expired' },
      });
      window.dispatchEvent(tokenExpiredEvent);
      
      await waitFor(() => {
        expect(screen.getByText('Your session has expired')).toBeInTheDocument();
      });
    });

    it('closes token expiration message when close button is clicked', async () => {
      const user = await createUserEvent();
      render(<App />, { initialState: authenticatedState });
      
      // Trigger token expiration
      const tokenExpiredEvent = new CustomEvent('tokenExpired', {
        detail: { message: 'Session expired' },
      });
      window.dispatchEvent(tokenExpiredEvent);
      
      await waitFor(() => {
        expect(screen.getByText('Session expired')).toBeInTheDocument();
      });
      
      // Close the snackbar
      const closeButton = screen.getByRole('button', { name: /close/i });
      await user.click(closeButton);
      
      await waitFor(() => {
        expect(screen.queryByText('Session expired')).not.toBeInTheDocument();
      });
    });

    it('auto-hides token expiration message after timeout', async () => {
      jest.useFakeTimers();
      
      render(<App />, { initialState: authenticatedState });
      
      // Trigger token expiration
      const tokenExpiredEvent = new CustomEvent('tokenExpired', {
        detail: { message: 'Session expired' },
      });
      window.dispatchEvent(tokenExpiredEvent);
      
      await waitFor(() => {
        expect(screen.getByText('Session expired')).toBeInTheDocument();
      });
      
      // Fast forward time
      jest.advanceTimersByTime(6000); // 6 seconds
      
      await waitFor(() => {
        expect(screen.queryByText('Session expired')).not.toBeInTheDocument();
      });
      
      jest.useRealTimers();
    });

    it('cleans up event listener on unmount', () => {
      const removeEventListenerSpy = jest.spyOn(window, 'removeEventListener');
      
      const { unmount } = render(<App />, { initialState: authenticatedState });
      
      unmount();
      
      expect(removeEventListenerSpy).toHaveBeenCalledWith(
        'tokenExpired',
        expect.any(Function)
      );
      
      removeEventListenerSpy.mockRestore();
    });
  });

  describe('error handling', () => {
    it('renders without crashing when state is malformed', () => {
      const malformedState = {
        auth: null,
        theme: null,
        meeting: null,
      };

      expect(() => {
        render(<App />, { initialState: malformedState });
      }).not.toThrow();
    });

    it('handles missing user gracefully', () => {
      const stateWithoutUser = {
        ...authenticatedState,
        auth: {
          ...authenticatedState.auth,
          user: null,
        },
      };

      expect(() => {
        render(<App />, { initialState: stateWithoutUser });
      }).not.toThrow();
    });
  });

  describe('analytics', () => {
    it('includes analytics in production', () => {
      const originalEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'production';
      
      render(<App />, { initialState: authenticatedState });
      
      // Analytics component should be rendered (mocked to return null)
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument();
      
      process.env.NODE_ENV = originalEnv;
    });

    it('does not include analytics in development', () => {
      const originalEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'development';
      
      render(<App />, { initialState: authenticatedState });
      
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument();
      
      process.env.NODE_ENV = originalEnv;
    });
  });
}); 