import React, { useEffect, useState, useMemo } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { Box, CssBaseline, Snackbar, Alert } from '@mui/material';
import { ThemeProvider } from '@mui/material/styles';
import { RootState } from './store';
import { validateToken } from './store/slices/authSlice';
import createAppTheme from './theme';

// Components
import Navbar from './components/Navbar';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import MeetingRoom from './pages/MeetingRoom';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';

const App: React.FC = () => {
  const { isAuthenticated } = useSelector((state: RootState) => state.auth);
  const { mode } = useSelector((state: RootState) => state.theme);
  const dispatch = useDispatch();
  const [tokenExpiredMessage, setTokenExpiredMessage] = useState<string | null>(null);

  // Create theme based on current mode
  const theme = useMemo(() => createAppTheme(mode), [mode]);

  useEffect(() => {
    // Listen for token expiration events
    const handleTokenExpired = (event: CustomEvent) => {
      setTokenExpiredMessage(event.detail.message);
    };

    window.addEventListener('tokenExpired', handleTokenExpired as EventListener);

    return () => {
      window.removeEventListener('tokenExpired', handleTokenExpired as EventListener);
    };
  }, []);

  useEffect(() => {
    // Validate token on app start and periodically
    dispatch(validateToken());

    // Check token validity every 5 minutes
    const tokenValidationInterval = setInterval(() => {
      dispatch(validateToken());
    }, 5 * 60 * 1000); // 5 minutes

    return () => {
      clearInterval(tokenValidationInterval);
    };
  }, [dispatch]);

  const handleCloseTokenExpiredMessage = () => {
    setTokenExpiredMessage(null);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
        {/* Only show navbar for authenticated users */}
        {isAuthenticated && <Navbar />}
        
        <Box 
          component="main" 
          sx={{ 
            flexGrow: 1,
            // Remove padding for login/register pages to allow full-screen design
            p: isAuthenticated ? 0 : 0,
          }}
        >
          <Routes>
            <Route
              path="/login"
              element={!isAuthenticated ? <Login /> : <Navigate to="/dashboard" />}
            />
            <Route
              path="/register"
              element={!isAuthenticated ? <Register /> : <Navigate to="/dashboard" />}
            />
            <Route
              path="/forgot-password"
              element={!isAuthenticated ? <ForgotPassword /> : <Navigate to="/dashboard" />}
            />
            <Route
              path="/reset-password"
              element={!isAuthenticated ? <ResetPassword /> : <Navigate to="/dashboard" />}
            />
            <Route
              path="/"
              element={isAuthenticated ? <Navigate to="/dashboard" /> : <Navigate to="/login" />}
            />
            <Route
              path="/dashboard"
              element={isAuthenticated ? <Dashboard /> : <Navigate to="/login" />}
            />
            <Route
              path="/meeting/:id"
              element={isAuthenticated ? <MeetingRoom /> : <Navigate to="/login" />}
            />
            {/* Catch all route */}
            <Route
              path="*"
              element={<Navigate to={isAuthenticated ? "/dashboard" : "/login"} />}
            />
          </Routes>
        </Box>

        {/* Token Expiration Snackbar */}
        <Snackbar
          open={!!tokenExpiredMessage}
          autoHideDuration={6000}
          onClose={handleCloseTokenExpiredMessage}
          anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        >
          <Alert 
            onClose={handleCloseTokenExpiredMessage} 
            severity="warning" 
            sx={{ width: '100%' }}
          >
            {tokenExpiredMessage}
          </Alert>
        </Snackbar>
      </Box>
    </ThemeProvider>
  );
};

export default App; 