import React, { useState, useEffect } from 'react';
import { API_URL } from '../utils/api';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { useAppDispatch } from '../store/hooks';
import { loginStart, loginSuccess, loginFailure } from '../store/slices/authSlice';
import {
  Container,
  TextField,
  Button,
  Typography,
  Box,
  Alert,
  CircularProgress,
  Divider,
  Card,
  CardContent,
} from '@mui/material';
import {
  Login as LoginIcon,
  Email,
  Lock,
  Visibility,
  VisibilityOff,
  PersonAdd,
} from '@mui/icons-material';
import { IconButton, InputAdornment } from '@mui/material';
import axios from 'axios';

const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useAppDispatch();

  useEffect(() => {
    // Check if there's a success message from registration
    if (location.state?.message) {
      setSuccessMessage(location.state.message);
      // Clear the state to prevent showing the message on refresh
      window.history.replaceState({}, document.title);
    }
  }, [location]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    dispatch(loginStart());

    try {
      const response = await axios.post(API_URL + '/token', {
        email: email,
        password,
      });

      const { access_token } = response.data;
      dispatch(loginSuccess(access_token));
      navigate('/dashboard');
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Login failed';
      setError(errorMessage);
      dispatch(loginFailure(errorMessage));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        py: 4,
      }}
    >
      <Container maxWidth="sm">
        <Card
          sx={{
            borderRadius: 4,
            boxShadow: '0 25px 50px -12px rgb(0 0 0 / 0.25)',
            overflow: 'hidden',
          }}
        >
          {/* Header */}
          <Box
            sx={{
              background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
              color: 'white',
              p: 4,
              textAlign: 'center',
            }}
          >
            <LoginIcon sx={{ fontSize: 48, mb: 2 }} />
            <Typography variant="h4" component="h1" fontWeight={700} gutterBottom>
              Welcome Back
            </Typography>
            <Typography variant="body1" sx={{ opacity: 0.9 }}>
              Sign in to your account to continue
            </Typography>
          </Box>

          <CardContent sx={{ p: 4 }}>
            {successMessage && (
              <Alert severity="success" sx={{ mb: 3, borderRadius: 2 }}>
                {successMessage}
              </Alert>
            )}
            {error && (
              <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>
                {error}
              </Alert>
            )}

            <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1 }}>
              <TextField
                margin="normal"
                required
                fullWidth
                id="email"
                label="Email Address"
                name="email"
                autoComplete="email"
                autoFocus
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={loading}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Email color="action" />
                    </InputAdornment>
                  ),
                }}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
                  },
                }}
              />
              <TextField
                margin="normal"
                required
                fullWidth
                name="password"
                label="Password"
                type={showPassword ? 'text' : 'password'}
                id="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Lock color="action" />
                    </InputAdornment>
                  ),
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        aria-label="toggle password visibility"
                        onClick={() => setShowPassword(!showPassword)}
                        edge="end"
                      >
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
                  },
                }}
              />

              <Button
                type="submit"
                fullWidth
                variant="contained"
                disabled={loading}
                sx={{
                  mt: 3,
                  mb: 2,
                  py: 1.5,
                  borderRadius: 2,
                  background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                  fontSize: '1.1rem',
                  fontWeight: 600,
                  '&:hover': {
                    background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
                  },
                  '&:disabled': {
                    background: 'linear-gradient(135deg, #94a3b8 0%, #64748b 100%)',
                  },
                }}
                startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <LoginIcon />}
              >
                {loading ? 'Signing In...' : 'Sign In'}
              </Button>

              <Box sx={{ textAlign: 'center', mb: 2 }}>
                <Link
                  to="/forgot-password"
                  style={{
                    color: '#6366f1',
                    textDecoration: 'none',
                    fontSize: '0.9rem',
                    fontWeight: 500,
                  }}
                >
                  Forgot your password?
                </Link>
              </Box>

              <Divider sx={{ my: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  OR
                </Typography>
              </Divider>

              <Button
                fullWidth
                variant="outlined"
                onClick={() => navigate('/register')}
                startIcon={<PersonAdd />}
                sx={{
                  py: 1.5,
                  borderRadius: 2,
                  borderColor: '#6366f1',
                  color: '#6366f1',
                  fontSize: '1.1rem',
                  fontWeight: 600,
                  '&:hover': {
                    borderColor: '#4f46e5',
                    backgroundColor: 'rgba(99, 102, 241, 0.04)',
                  },
                }}
              >
                Create New Account
              </Button>
            </Box>
          </CardContent>
        </Card>

        {/* Footer */}
        <Box sx={{ textAlign: 'center', mt: 4 }}>
          <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.8)' }}>
            © 2025 Meeting Transcription App. All rights reserved.
          </Typography>
        </Box>
      </Container>
    </Box>
  );
};

export default Login; 
