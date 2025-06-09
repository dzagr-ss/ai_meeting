import React from 'react';
import { screen, waitFor } from '@testing-library/react';
import { render, createUserEvent, mockFetch } from '../../utils/test-utils';
import Login from '../Login';

// Mock axios
jest.mock('axios', () => ({
  post: jest.fn(),
}));

const mockAxios = require('axios');

// Mock react-router-dom
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  Link: ({ children, to }: any) => <a href={to}>{children}</a>,
}));

describe('Login', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockAxios.post.mockReset();
  });

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

  it('renders login form correctly', () => {
    render(<Login />, { initialState: unauthenticatedState });
    
    expect(screen.getByText('Sign In')).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('shows validation errors for empty fields', async () => {
    const user = await createUserEvent();
    render(<Login />, { initialState: unauthenticatedState });
    
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(/email is required/i)).toBeInTheDocument();
      expect(screen.getByText(/password is required/i)).toBeInTheDocument();
    });
  });

  it('shows validation error for invalid email format', async () => {
    const user = await createUserEvent();
    render(<Login />, { initialState: unauthenticatedState });
    
    const emailInput = screen.getByLabelText(/email/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    
    await user.type(emailInput, 'invalid-email');
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(/please enter a valid email/i)).toBeInTheDocument();
    });
  });

  it('submits form with valid credentials', async () => {
    const user = await createUserEvent();
    const mockToken = 'mock-jwt-token';
    
    mockAxios.post.mockResolvedValueOnce({
      data: { access_token: mockToken },
    });

    render(<Login />, { initialState: unauthenticatedState });
    
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    
    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'password123');
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(mockAxios.post).toHaveBeenCalledWith(
        expect.stringContaining('/auth/login'),
        {
          email: 'test@example.com',
          password: 'password123',
        }
      );
    });
  });

  it('displays error message on login failure', async () => {
    const user = await createUserEvent();
    const errorMessage = 'Invalid credentials';
    
    mockAxios.post.mockRejectedValueOnce({
      response: {
        data: { detail: errorMessage },
      },
    });

    render(<Login />, { initialState: unauthenticatedState });
    
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    
    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'wrongpassword');
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });
  });

  it('shows loading state during submission', async () => {
    const user = await createUserEvent();
    
    // Create a promise that we can control
    let resolvePromise: (value: any) => void;
    const pendingPromise = new Promise((resolve) => {
      resolvePromise = resolve;
    });
    
    mockAxios.post.mockReturnValueOnce(pendingPromise);

    render(<Login />, { initialState: unauthenticatedState });
    
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    
    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'password123');
    await user.click(submitButton);
    
    // Check loading state
    expect(screen.getByRole('button', { name: /signing in/i })).toBeInTheDocument();
    expect(submitButton).toBeDisabled();
    
    // Resolve the promise to complete the test
    resolvePromise!({ data: { access_token: 'token' } });
  });

  it('navigates to register page when register link is clicked', () => {
    render(<Login />, { initialState: unauthenticatedState });
    
    const registerLink = screen.getByText(/sign up/i);
    expect(registerLink).toHaveAttribute('href', '/register');
  });

  it('navigates to forgot password page when forgot password link is clicked', () => {
    render(<Login />, { initialState: unauthenticatedState });
    
    const forgotPasswordLink = screen.getByText(/forgot password/i);
    expect(forgotPasswordLink).toHaveAttribute('href', '/forgot-password');
  });

  it('handles password visibility toggle', async () => {
    const user = await createUserEvent();
    render(<Login />, { initialState: unauthenticatedState });
    
    const passwordInput = screen.getByLabelText(/password/i);
    const visibilityToggle = screen.getByRole('button', { name: /toggle password visibility/i });
    
    // Initially password should be hidden
    expect(passwordInput).toHaveAttribute('type', 'password');
    
    // Click to show password
    await user.click(visibilityToggle);
    expect(passwordInput).toHaveAttribute('type', 'text');
    
    // Click to hide password again
    await user.click(visibilityToggle);
    expect(passwordInput).toHaveAttribute('type', 'password');
  });

  it('focuses on email input when page loads', () => {
    render(<Login />, { initialState: unauthenticatedState });
    
    const emailInput = screen.getByLabelText(/email/i);
    expect(emailInput).toHaveFocus();
  });

  it('submits form when Enter is pressed', async () => {
    const user = await createUserEvent();
    mockAxios.post.mockResolvedValueOnce({
      data: { access_token: 'mock-token' },
    });

    render(<Login />, { initialState: unauthenticatedState });
    
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    
    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'password123');
    await user.keyboard('{Enter}');
    
    await waitFor(() => {
      expect(mockAxios.post).toHaveBeenCalled();
    });
  });

  it('clears error message when user starts typing', async () => {
    const user = await createUserEvent();
    
    // First, trigger an error
    mockAxios.post.mockRejectedValueOnce({
      response: { data: { detail: 'Login failed' } },
    });

    render(<Login />, { initialState: unauthenticatedState });
    
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    
    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'wrongpassword');
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Login failed')).toBeInTheDocument();
    });
    
    // Start typing to clear error
    await user.type(passwordInput, 'a');
    
    await waitFor(() => {
      expect(screen.queryByText('Login failed')).not.toBeInTheDocument();
    });
  });

  it('renders correctly in dark theme', () => {
    const darkThemeState = {
      ...unauthenticatedState,
      theme: { mode: 'dark' },
    };

    render(<Login />, { initialState: darkThemeState, theme: 'dark' });
    
    expect(screen.getByText('Sign In')).toBeInTheDocument();
  });

  it('handles network errors gracefully', async () => {
    const user = await createUserEvent();
    
    mockAxios.post.mockRejectedValueOnce(new Error('Network Error'));

    render(<Login />, { initialState: unauthenticatedState });
    
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    
    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'password123');
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(/error occurred/i)).toBeInTheDocument();
    });
  });
}); 