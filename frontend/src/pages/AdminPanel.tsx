import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Box,
  Alert,
  Chip,
  CircularProgress,
  Button,
} from '@mui/material';
import { AdminPanelSettings, Person, CheckCircle, Pending, Star } from '@mui/icons-material';
import api from '../utils/api';
import { useTheme } from '@mui/material/styles';

interface AdminUser {
  id: number;
  email: string;
  user_type: string;
  is_active: boolean;
  created_at: string;
}

const AdminPanel: React.FC = () => {
  const theme = useTheme();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [updating, setUpdating] = useState<number | null>(null);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await api.get('/admin/users');
      setUsers(response.data);
    } catch (err: any) {
      setError('Failed to fetch users');
      console.error('Error fetching users:', err);
    } finally {
      setLoading(false);
    }
  };

  const updateUserType = async (userId: number, newType: string) => {
    try {
      setUpdating(userId);
      setError(null);
      setSuccess(null);
      
      await api.put(`/admin/users/${userId}/type`, { user_type: newType });
      
      // Update the user in the local state
      setUsers(users.map(u => 
        u.id === userId ? { ...u, user_type: newType } : u
      ));
      
      setSuccess(`User type updated successfully`);
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update user type');
      setTimeout(() => setError(null), 5000);
    } finally {
      setUpdating(null);
    }
  };

  const getUserTypeIcon = (userType: string) => {
    switch (userType) {
      case 'admin':
        return <AdminPanelSettings color="error" />;
      case 'pending':
        return <Pending color="warning" />;
      case 'trial':
        return <Star color="info" />;
      case 'normal':
        return <CheckCircle color="success" />;
      case 'pro':
        return <Star color="primary" />;
      default:
        return <Person />;
    }
  };

  const getUserTypeColor = (userType: string) => {
    switch (userType) {
      case 'admin':
        return 'error';
      case 'pending':
        return 'warning';
      case 'trial':
        return 'info';
      case 'normal':
        return 'success';
      case 'pro':
        return 'primary';
      default:
        return 'default';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 4, display: 'flex', alignItems: 'center', gap: 2 }}>
        <AdminPanelSettings color="primary" sx={{ fontSize: 32 }} />
        <Typography variant="h4" component="h1">
          Admin Panel
        </Typography>
      </Box>

      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Manage user accounts and permissions. Only admins can access this page.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3 }}>
          {success}
        </Alert>
      )}

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <TableContainer component={Paper} elevation={2}>
          <Table>
            <TableHead>
              <TableRow sx={{ 
                backgroundColor: theme.palette.mode === 'dark' ? 'grey.800' : 'grey.50'
              }}>
                <TableCell><strong>User</strong></TableCell>
                <TableCell><strong>Email</strong></TableCell>
                <TableCell><strong>Current Type</strong></TableCell>
                <TableCell><strong>Status</strong></TableCell>
                <TableCell><strong>Created</strong></TableCell>
                <TableCell><strong>Actions</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {users.map((user) => (
                <TableRow key={user.id} hover>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {getUserTypeIcon(user.user_type)}
                      <Typography variant="body2">
                        ID: {user.id}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body1">
                      {user.email}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={user.user_type.toUpperCase()}
                      color={getUserTypeColor(user.user_type) as any}
                      size="small"
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={user.is_active ? 'Active' : 'Inactive'}
                      color={user.is_active ? 'success' : 'error'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {formatDate(user.created_at)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <FormControl size="small" sx={{ minWidth: 120 }}>
                      <InputLabel>Type</InputLabel>
                      <Select
                        value={user.user_type}
                        label="Type"
                        onChange={(e) => updateUserType(user.id, e.target.value)}
                        disabled={updating === user.id || user.email === 'zagravsky@gmail.com'}
                      >
                        <MenuItem value="admin">Admin</MenuItem>
                        <MenuItem value="pending">Pending</MenuItem>
                        <MenuItem value="trial">Trial</MenuItem>
                        <MenuItem value="normal">Normal</MenuItem>
                        <MenuItem value="pro">Pro</MenuItem>
                      </Select>
                    </FormControl>
                    {updating === user.id && (
                      <CircularProgress size={16} sx={{ ml: 1 }} />
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {users.length === 0 && !loading && (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="h6" color="text.secondary">
            No users found
          </Typography>
        </Box>
      )}

      <Box sx={{ mt: 3 }}>
        <Button variant="outlined" onClick={fetchUsers} disabled={loading}>
          Refresh Users
        </Button>
      </Box>
    </Container>
  );
};

export default AdminPanel; 