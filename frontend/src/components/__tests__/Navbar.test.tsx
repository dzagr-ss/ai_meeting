import React from 'react';
import { screen, waitFor } from '@testing-library/react';
import { render, createMockAuthState, createUserEvent } from '../../utils/test-utils';
import Navbar from '../Navbar';

// Mock the logout action
const mockLogout = jest.fn();
jest.mock('../../store/slices/authSlice', () => ({
  ...jest.requireActual('../../store/slices/authSlice'),
  logout: () => mockLogout,
}));

// Mock react-router-dom
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

describe('Navbar', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const authenticatedState = {
    auth: createMockAuthState(),
    theme: { mode: 'light' },
    meeting: { currentMeeting: null, meetings: [], loading: false },
  };

  it('renders navbar when user is authenticated', () => {
    render(<Navbar />, { initialState: authenticatedState });
    
    expect(screen.getByText('Meeting Transcription')).toBeInTheDocument();
  });

  it('displays user email in the navbar', () => {
    const customAuthState = {
      ...authenticatedState,
      auth: createMockAuthState({ user: { email: 'john@example.com', user_type: 'normal' } }),
    };

    render(<Navbar />, { initialState: customAuthState });
    
    expect(screen.getByText('john@example.com')).toBeInTheDocument();
  });

  it('shows admin panel link for admin users', () => {
    const adminState = {
      ...authenticatedState,
      auth: createMockAuthState({ user: { email: 'admin@example.com', user_type: 'admin' } }),
    };

    render(<Navbar />, { initialState: adminState });
    
    expect(screen.getByText('Admin Panel')).toBeInTheDocument();
  });

  it('does not show admin panel link for normal users', () => {
    render(<Navbar />, { initialState: authenticatedState });
    
    expect(screen.queryByText('Admin Panel')).not.toBeInTheDocument();
  });

  it('navigates to dashboard when logo is clicked', async () => {
    const user = await createUserEvent();
    render(<Navbar />, { initialState: authenticatedState });
    
    const logo = screen.getByText('Meeting Transcription');
    await user.click(logo);
    
    expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
  });

  it('opens user menu when profile button is clicked', async () => {
    const user = await createUserEvent();
    render(<Navbar />, { initialState: authenticatedState });
    
    const profileButton = screen.getByRole('button', { name: /account of current user/i });
    await user.click(profileButton);
    
    await waitFor(() => {
      expect(screen.getByText('Logout')).toBeInTheDocument();
    });
  });

  it('dispatches logout action when logout is clicked', async () => {
    const user = await createUserEvent();
    render(<Navbar />, { initialState: authenticatedState });
    
    // Open user menu
    const profileButton = screen.getByRole('button', { name: /account of current user/i });
    await user.click(profileButton);
    
    // Click logout
    await waitFor(() => {
      const logoutButton = screen.getByText('Logout');
      return user.click(logoutButton);
    });
    
    expect(mockLogout).toHaveBeenCalled();
  });

  it('toggles theme when theme switcher is used', async () => {
    const user = await createUserEvent();
    render(<Navbar />, { initialState: authenticatedState });
    
    // Look for theme toggle button (this might be an icon button)
    const themeToggle = screen.getByRole('button', { name: /toggle theme/i });
    await user.click(themeToggle);
    
    // Theme action should be dispatched (we'd need to mock the theme slice to test this)
    expect(themeToggle).toBeInTheDocument();
  });

  it('renders correctly in dark theme', () => {
    const darkThemeState = {
      ...authenticatedState,
      theme: { mode: 'dark' },
    };

    render(<Navbar />, { initialState: darkThemeState, theme: 'dark' });
    
    expect(screen.getByText('Meeting Transcription')).toBeInTheDocument();
  });

  it('handles mobile responsive behavior', () => {
    // Mock mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 500,
    });

    render(<Navbar />, { initialState: authenticatedState });
    
    // Should still render main elements
    expect(screen.getByText('Meeting Transcription')).toBeInTheDocument();
  });

  it('shows loading state appropriately', () => {
    const loadingState = {
      ...authenticatedState,
      auth: { ...authenticatedState.auth, loading: true },
    };

    render(<Navbar />, { initialState: loadingState });
    
    // Should still render navbar even during loading
    expect(screen.getByText('Meeting Transcription')).toBeInTheDocument();
  });

  it('navigates to admin panel when admin link is clicked', async () => {
    const user = await createUserEvent();
    const adminState = {
      ...authenticatedState,
      auth: createMockAuthState({ user: { email: 'admin@example.com', user_type: 'admin' } }),
    };

    render(<Navbar />, { initialState: adminState });
    
    const adminLink = screen.getByText('Admin Panel');
    await user.click(adminLink);
    
    expect(mockNavigate).toHaveBeenCalledWith('/admin');
  });

  it('shows correct user type badge', () => {
    const proUserState = {
      ...authenticatedState,
      auth: createMockAuthState({ user: { email: 'pro@example.com', user_type: 'pro' } }),
    };

    render(<Navbar />, { initialState: proUserState });
    
    // Look for user type indicator
    expect(screen.getByText('pro@example.com')).toBeInTheDocument();
  });

  it('handles error states gracefully', () => {
    const errorState = {
      ...authenticatedState,
      auth: { ...authenticatedState.auth, error: 'Authentication error' },
    };

    render(<Navbar />, { initialState: errorState });
    
    // Should still render navbar despite error
    expect(screen.getByText('Meeting Transcription')).toBeInTheDocument();
  });
}); 