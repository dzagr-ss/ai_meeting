import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../store/hooks';
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Box,
  CircularProgress,
  TextField,
  Chip,
  Fade,
  Paper,
  Snackbar,
  Alert,
  Autocomplete,
  IconButton,
  ToggleButton,
  ToggleButtonGroup,
  Tabs,
  Tab,
} from '@mui/material';
import {
  Add,
  VideoCall,
  Schedule,
  PlayArrow,
  TrendingUp,
  Group,
  AccessTime,
  LocalOffer,
  Edit,
  FilterList,
  Clear,
  ViewModule,
  CalendarMonth,
  ChevronLeft,
  ChevronRight,
  Today,
} from '@mui/icons-material';
import {
  fetchMeetingsStart,
  fetchMeetingsSuccess,
  fetchMeetingsFailure,
  updateMeetingSuccess,
  deleteMeetingSuccess,
  setSelectedTags,
  clearSelectedTags,
} from '../store/slices/meetingSlice';
import MeetingDropdownMenu from '../components/MeetingDropdownMenu';
import TagChip from '../components/TagChip';
import TagManager from '../components/TagManager';
import api from '../utils/api';

interface Tag {
  id: number;
  name: string;
  color: string;
  created_at: string;
}

interface Meeting {
  id: number;
  title: string;
  description: string | null;
  start_time: string;
  end_time: string | null;
  status: string;
  tags: Tag[];
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { meetings, loading, selectedTags } = useAppSelector((state) => state.meeting);
  const { token, user } = useAppSelector((state) => state.auth);
  const [newMeetingTitle, setNewMeetingTitle] = useState('');
  const [availableTags, setAvailableTags] = useState<Tag[]>([]);
  const [tagManagerOpen, setTagManagerOpen] = useState(false);
  const [selectedMeetingForTags, setSelectedMeetingForTags] = useState<Meeting | null>(null);
  const [viewType, setViewType] = useState<'grid' | 'calendar'>('grid');
  const [calendarView, setCalendarView] = useState<'month' | 'week' | 'day'>('month');
  const [currentDate, setCurrentDate] = useState(new Date());
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error';
  }>({
    open: false,
    message: '',
    severity: 'success',
  });

  useEffect(() => {
    const fetchMeetings = async () => {
      dispatch(fetchMeetingsStart());
      try {
        const response = await api.get('/meetings/');
        dispatch(fetchMeetingsSuccess(response.data));
      } catch (err) {
        dispatch(fetchMeetingsFailure('Failed to fetch meetings'));
      }
    };

    const fetchTags = async () => {
      try {
        const response = await api.get('/tags/');
        setAvailableTags(response.data);
      } catch (err) {
        console.error('Failed to fetch tags:', err);
      }
    };

    fetchMeetings();
    fetchTags();
  }, [dispatch, token]);

  const handleCreateMeeting = async () => {
    if (!newMeetingTitle.trim()) return;
    
    if (user?.user_type === 'pending') {
      setSnackbar({
        open: true,
        message: 'Your account is pending approval. Please contact an administrator.',
        severity: 'error',
      });
      return;
    }
    
    try {
      const response = await api.post('/meetings/', { title: newMeetingTitle });
      navigate(`/meeting/${response.data.id}`);
    } catch (err: any) {
      console.error('Failed to create meeting:', err);
      setSnackbar({
        open: true,
        message: err.response?.data?.detail || 'Failed to create meeting',
        severity: 'error',
      });
    }
  };

  const handleRenameMeeting = async (meetingId: number, newTitle: string) => {
    try {
      const response = await api.put(`/meetings/${meetingId}`, { title: newTitle });
      dispatch(updateMeetingSuccess(response.data));
      setSnackbar({
        open: true,
        message: 'Meeting renamed successfully',
        severity: 'success',
      });
    } catch (err) {
      console.error('Failed to rename meeting:', err);
      setSnackbar({
        open: true,
        message: 'Failed to rename meeting',
        severity: 'error',
      });
    }
  };

  const handleDeleteMeeting = async (meetingId: number) => {
    try {
      await api.delete(`/meetings/${meetingId}`);
      dispatch(deleteMeetingSuccess(meetingId));
      setSnackbar({
        open: true,
        message: 'Meeting deleted successfully',
        severity: 'success',
      });
    } catch (err) {
      console.error('Failed to delete meeting:', err);
      setSnackbar({
        open: true,
        message: 'Failed to delete meeting',
        severity: 'error',
      });
    }
  };

  const handleManageTags = (meeting: Meeting) => {
    setSelectedMeetingForTags(meeting);
    setTagManagerOpen(true);
  };

  const handleTagsUpdated = (updatedTags: Tag[]) => {
    if (selectedMeetingForTags) {
      const updatedMeeting = { ...selectedMeetingForTags, tags: updatedTags };
      dispatch(updateMeetingSuccess(updatedMeeting));
      setSnackbar({
        open: true,
        message: 'Tags updated successfully',
        severity: 'success',
      });
    }
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  const handleTagFilterChange = (event: any, value: string[]) => {
    dispatch(setSelectedTags(value));
  };

  const clearTagFilter = () => {
    dispatch(clearSelectedTags());
  };

  // Calendar helper functions
  const getDaysInMonth = (date: Date) => {
    return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
  };

  const getFirstDayOfMonth = (date: Date) => {
    return new Date(date.getFullYear(), date.getMonth(), 1).getDay();
  };

  const isSameDay = (date1: Date, date2: Date) => {
    return (
      date1.getFullYear() === date2.getFullYear() &&
      date1.getMonth() === date2.getMonth() &&
      date1.getDate() === date2.getDate()
    );
  };

  const getMeetingsForDate = (date: Date) => {
    return filteredMeetings.filter(meeting => {
      const meetingDate = new Date(meeting.start_time);
      return isSameDay(meetingDate, date);
    });
  };

  const navigateCalendar = (direction: 'prev' | 'next') => {
    const newDate = new Date(currentDate);
    if (calendarView === 'month') {
      newDate.setMonth(newDate.getMonth() + (direction === 'next' ? 1 : -1));
    } else if (calendarView === 'week') {
      newDate.setDate(newDate.getDate() + (direction === 'next' ? 7 : -7));
    } else if (calendarView === 'day') {
      newDate.setDate(newDate.getDate() + (direction === 'next' ? 1 : -1));
    }
    setCurrentDate(newDate);
  };

  const goToToday = () => {
    setCurrentDate(new Date());
  };

  const renderCalendarMonth = () => {
    const daysInMonth = getDaysInMonth(currentDate);
    const firstDay = getFirstDayOfMonth(currentDate);
    const today = new Date();
    const daysOfWeek = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    
    // Convert Sunday (0) to be 6, and subtract 1 from others to make Monday = 0
    const adjustedFirstDay = firstDay === 0 ? 6 : firstDay - 1;
    
    const calendarDays = [];
    
    // Add empty cells for days before the first day of the month
    for (let i = 0; i < adjustedFirstDay; i++) {
      calendarDays.push(
        <Paper
          key={`empty-${i}`}
          sx={{
            minHeight: { xs: 80, sm: 120 },
            border: '1px solid',
            borderColor: 'divider',
            backgroundColor: 'action.disabled',
          }}
        />
      );
    }
    
    // Add cells for each day of the month
    for (let day = 1; day <= daysInMonth; day++) {
      const date = new Date(currentDate.getFullYear(), currentDate.getMonth(), day);
      const dayMeetings = getMeetingsForDate(date);
      const isToday = isSameDay(date, today);
      const dayOfWeek = date.getDay(); // 0 = Sunday, 6 = Saturday
      const isWeekend = dayOfWeek === 0 || dayOfWeek === 6; // Sunday or Saturday
      
      calendarDays.push(
        <Paper
          key={day}
          sx={{
            p: { xs: 0.5, sm: 1 },
            minHeight: { xs: 80, sm: 120 },
            border: isToday ? '2px solid' : '1px solid',
            borderColor: isToday ? 'primary.main' : 'divider',
            backgroundColor: (theme) => {
              if (isToday) {
                return theme.palette.primary.main + '0D'; // 5% opacity
              } else if (isWeekend) {
                return theme.palette.action.hover;
              }
              return theme.palette.background.paper;
            },
            cursor: 'pointer',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            '&:hover': {
              backgroundColor: (theme) => {
                if (isToday) {
                  return theme.palette.primary.main + '26'; // 15% opacity
                } else if (isWeekend) {
                  return theme.palette.primary.main + '14'; // 8% opacity
                } else {
                  return theme.palette.primary.main + '1A'; // 10% opacity
                }
              },
            },
          }}
        >
          <Typography
            variant="body2"
            fontWeight={isToday ? 700 : 400}
            color={isToday ? 'primary' : 'text.primary'}
            sx={{ 
              mb: { xs: 0.5, sm: 1 }, 
              textAlign: 'left',
              fontSize: { xs: '0.75rem', sm: '0.875rem' }
            }}
          >
            {day}
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: { xs: 0.25, sm: 0.5 }, flex: 1, overflow: 'hidden' }}>
            {dayMeetings.slice(0, 2).map(meeting => (
              <Chip
                key={meeting.id}
                label={meeting.title}
                size="small"
                sx={{
                  fontSize: { xs: '0.6rem', sm: '0.7rem' },
                  height: { xs: 16, sm: 18 },
                  cursor: 'pointer',
                  '& .MuiChip-label': {
                    px: { xs: 0.25, sm: 0.5 },
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  },
                }}
                onClick={(e) => {
                  e.stopPropagation();
                  navigate(`/meeting/${meeting.id}`);
                }}
              />
            ))}
            {dayMeetings.length > 2 && (
              <Typography 
                variant="caption" 
                color="text.secondary" 
                sx={{ fontSize: { xs: '0.55rem', sm: '0.65rem' } }}
              >
                +{dayMeetings.length - 2} more
              </Typography>
            )}
          </Box>
        </Paper>
      );
    }
    
    // Fill remaining cells to complete the grid (6 rows x 7 days = 42 cells)
    const totalCells = 42;
    const remainingCells = totalCells - calendarDays.length;
    for (let i = 0; i < remainingCells; i++) {
      calendarDays.push(
        <Paper
          key={`empty-end-${i}`}
          sx={{
            minHeight: { xs: 80, sm: 120 },
            border: '1px solid',
            borderColor: 'divider',
            backgroundColor: 'action.disabled',
          }}
        />
      );
    }
    
    return (
      <Box>
        {/* Days of week header */}
        <Paper sx={{ mb: 2, border: '1px solid', borderColor: 'divider', overflowX: 'auto' }}>
          <Box 
            sx={{ 
              display: 'grid',
              gridTemplateColumns: 'repeat(7, 1fr)',
              minWidth: { xs: '350px', sm: 'auto' }
            }}
          >
            {daysOfWeek.map(day => {
              const isWeekend = day === 'Sat' || day === 'Sun';
              return (
                <Box 
                  key={day}
                  sx={{ 
                    p: { xs: 1, sm: 2 }, 
                    textAlign: 'center',
                    borderRight: day !== 'Sun' ? '1px solid' : 'none',
                    borderColor: 'divider',
                    backgroundColor: isWeekend ? 'action.hover' : 'action.selected'
                  }}
                >
                  <Typography 
                    variant="subtitle2" 
                    fontWeight={600} 
                    color={isWeekend ? 'text.secondary' : 'text.primary'}
                    sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
                  >
                    {day}
                  </Typography>
                </Box>
              );
            })}
          </Box>
        </Paper>
        
        {/* Calendar grid - 6 rows x 7 columns */}
        <Paper sx={{ border: '1px solid', borderColor: 'divider', overflowX: 'auto' }}>
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: 'repeat(7, 1fr)',
              minWidth: { xs: '350px', sm: 'auto' }
            }}
          >
            {calendarDays.map((day, index) => (
              <Box
                key={index}
                sx={{
                  borderRight: (index + 1) % 7 !== 0 ? '1px solid' : 'none',
                  borderBottom: index < 35 ? '1px solid' : 'none',
                  borderColor: 'divider',
                }}
              >
                {day}
              </Box>
            ))}
          </Box>
        </Paper>
      </Box>
    );
  };

  const renderCalendarWeek = () => {
    const startOfWeek = new Date(currentDate);
    const day = startOfWeek.getDay();
    startOfWeek.setDate(startOfWeek.getDate() - day);
    
    const weekDays = [];
    for (let i = 0; i < 7; i++) {
      const date = new Date(startOfWeek);
      date.setDate(startOfWeek.getDate() + i);
      weekDays.push(date);
    }
    
    const today = new Date();
    
    return (
      <Grid container spacing={2}>
        {weekDays.map((date, index) => {
          const dayMeetings = getMeetingsForDate(date);
          const isToday = isSameDay(date, today);
          const dayOfWeek = date.getDay();
          const isWeekend = dayOfWeek === 0 || dayOfWeek === 6;
          
          return (
            <Grid item xs key={index}>
              <Paper
                sx={{
                  p: 2,
                  minHeight: 200,
                  border: isToday ? '2px solid' : '1px solid',
                  borderColor: isToday ? 'primary.main' : 'divider',
                  backgroundColor: (theme) => {
                    if (isToday) {
                      return theme.palette.primary.main + '0D'; // 5% opacity
                    } else if (isWeekend) {
                      return theme.palette.action.hover;
                    }
                    return theme.palette.background.paper;
                  },
                  transition: 'all 0.2s ease-in-out',
                  '&:hover': {
                    backgroundColor: (theme) => {
                      if (isToday) {
                        return theme.palette.primary.main + '1A'; // 10% opacity
                      } else {
                        return theme.palette.action.hover;
                      }
                    },
                    transform: 'translateY(-2px)',
                    boxShadow: (theme) => theme.shadows[4],
                  },
                }}
              >
                <Typography
                  variant="h6"
                  fontWeight={isToday ? 700 : 400}
                  color={isToday ? 'primary' : 'text.primary'}
                  sx={{ mb: 2 }}
                >
                  {date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  {dayMeetings.map(meeting => (
                    <Chip
                      key={meeting.id}
                      label={meeting.title}
                      size="small"
                      sx={{
                        cursor: 'pointer',
                        backgroundColor: 'primary.main',
                        color: 'primary.contrastText',
                        '& .MuiChip-label': {
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        },
                        '&:hover': {
                          backgroundColor: 'primary.dark',
                          transform: 'scale(1.02)',
                        },
                        transition: 'all 0.2s ease-in-out',
                      }}
                      onClick={() => navigate(`/meeting/${meeting.id}`)}
                    />
                  ))}
                  {dayMeetings.length === 0 && (
                    <Typography 
                      variant="body2" 
                      color="text.secondary" 
                      sx={{ 
                        textAlign: 'center', 
                        py: 2,
                        fontStyle: 'italic'
                      }}
                    >
                      No meetings
                    </Typography>
                  )}
                </Box>
              </Paper>
            </Grid>
          );
        })}
      </Grid>
    );
  };

  const renderCalendarDay = () => {
    const dayMeetings = getMeetingsForDate(currentDate);
    const isToday = isSameDay(currentDate, new Date());
    
    return (
      <Paper sx={{ p: 3 }}>
        <Typography
          variant="h4"
          fontWeight={isToday ? 700 : 400}
          color={isToday ? 'primary' : 'text.primary'}
          sx={{ mb: 3 }}
        >
          {currentDate.toLocaleDateString('en-US', { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
          })}
        </Typography>
        
        {dayMeetings.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="h6" color="text.secondary">
              No meetings scheduled for this day
            </Typography>
          </Box>
        ) : (
          <Grid container spacing={2}>
            {dayMeetings.map(meeting => (
              <Grid item xs={12} sm={6} md={4} key={meeting.id}>
                <Card
                  sx={{
                    cursor: 'pointer',
                    '&:hover': {
                      boxShadow: 3,
                    },
                  }}
                  onClick={() => navigate(`/meeting/${meeting.id}`)}
                >
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      {meeting.title}
                    </Typography>
                    <Chip
                      icon={getStatusIcon(meeting.status)}
                      label={meeting.status}
                      size="small"
                      color={getStatusColor(meeting.status) as any}
                    />
                    <Box sx={{ mt: 1 }}>
                      {meeting.tags.slice(0, 3).map(tag => (
                        <TagChip key={tag.id} tag={tag} size="small" />
                      ))}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </Paper>
    );
  };

  // Filter meetings based on selected tags and sort by most recent first
  const filteredMeetings = selectedTags.length > 0 
    ? meetings.filter(meeting => 
        meeting.tags.some(tag => selectedTags.includes(tag.name))
      ).sort((a, b) => new Date(b.start_time).getTime() - new Date(a.start_time).getTime())
    : [...meetings].sort((a, b) => new Date(b.start_time).getTime() - new Date(a.start_time).getTime());

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active':
        return 'success';
      case 'scheduled':
        return 'warning';
      case 'completed':
        return 'default';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active':
        return <PlayArrow fontSize="small" />;
      case 'scheduled':
        return <Schedule fontSize="small" />;
      case 'completed':
        return <AccessTime fontSize="small" />;
      default:
        return <Schedule fontSize="small" />;
    }
  };

  if (loading) {
    return (
      <Box 
        display="flex" 
        flexDirection="column"
        justifyContent="center" 
        alignItems="center" 
        minHeight="80vh"
        gap={2}
      >
        <CircularProgress size={48} thickness={4} />
        <Typography variant="body1" color="text.secondary">
          Loading your meetings...
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ minHeight: '100vh', backgroundColor: 'background.default', py: 4 }}>
      <Container maxWidth="lg">
        {/* Header Section */}
        <Box sx={{ mb: 6 }}>
          <Typography 
            variant="h3" 
            component="h1" 
            gutterBottom
            sx={{ 
              fontWeight: 700,
              background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            Welcome back! 👋
          </Typography>
          <Typography variant="h6" color="text.secondary" sx={{ mb: 4 }}>
            Manage your meetings and transcriptions
          </Typography>

          {/* User Status Alert for Pending Users */}
          {user?.user_type === 'pending' && (
            <Alert 
              severity="warning" 
              sx={{ 
                mb: 4,
                borderRadius: 2,
                '& .MuiAlert-message': {
                  width: '100%'
                }
              }}
            >
              <Box>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                  Account Pending Approval
                </Typography>
                <Typography variant="body2">
                  Your account is currently pending approval from an administrator. 
                  You won't be able to create meetings or start transcriptions until your account is approved.
                  Please contact an administrator for assistance.
                </Typography>
              </Box>
            </Alert>
          )}

          {/* Quick Stats */}
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} sm={4}>
              <Paper
                sx={{
                  p: 3,
                  background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                  color: 'white',
                  borderRadius: 3,
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <VideoCall sx={{ fontSize: 32 }} />
                  <Box>
                    <Typography variant="h4" fontWeight={700}>
                      {meetings.length}
                    </Typography>
                    <Typography variant="body2" sx={{ opacity: 0.9 }}>
                      Total Meetings
                    </Typography>
                  </Box>
                </Box>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Paper
                sx={{
                  p: 3,
                  background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                  color: 'white',
                  borderRadius: 3,
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <TrendingUp sx={{ fontSize: 32 }} />
                  <Box>
                    <Typography variant="h4" fontWeight={700}>
                      {meetings.filter(m => m.status === 'completed').length}
                    </Typography>
                    <Typography variant="body2" sx={{ opacity: 0.9 }}>
                      Completed
                    </Typography>
                  </Box>
                </Box>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Paper
                sx={{
                  p: 3,
                  background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
                  color: 'white',
                  borderRadius: 3,
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Group sx={{ fontSize: 32 }} />
                  <Box>
                    <Typography variant="h4" fontWeight={700}>
                      {meetings.filter(m => m.status === 'active').length}
                    </Typography>
                    <Typography variant="body2" sx={{ opacity: 0.9 }}>
                      Active Now
                    </Typography>
                  </Box>
                </Box>
              </Paper>
            </Grid>
          </Grid>

          {/* Create Meeting Section */}
          <Paper
            sx={{
              p: 4,
              borderRadius: 3,
              background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.05) 0%, rgba(139, 92, 246, 0.05) 100%)',
              border: '1px solid rgba(99, 102, 241, 0.1)',
            }}
          >
            <Typography variant="h5" fontWeight={600} gutterBottom>
              Start a New Meeting
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
              Create a new meeting room with AI-powered transcription
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <TextField
                label="Meeting Title"
                value={newMeetingTitle}
                onChange={(e) => setNewMeetingTitle(e.target.value)}
                placeholder={user?.user_type === 'pending' ? "Account pending approval" : "e.g., Weekly Team Standup"}
                disabled={user?.user_type === 'pending'}
                sx={{ flexGrow: 1, minWidth: 300 }}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleCreateMeeting();
                  }
                }}
              />
              <Button
                variant="contained"
                size="large"
                onClick={handleCreateMeeting}
                disabled={!newMeetingTitle.trim() || user?.user_type === 'pending'}
                startIcon={<Add />}
                sx={{
                  background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                  px: 4,
                  py: 1.5,
                  '&:hover': {
                    background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
                  },
                }}
              >
                Create Meeting
              </Button>
            </Box>
          </Paper>
        </Box>

        {/* Tag Filter Section */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <FilterList color="primary" />
            <Typography variant="h6" fontWeight={600}>
              Filter by Tags
            </Typography>
            {selectedTags.length > 0 && (
              <IconButton onClick={clearTagFilter} size="small">
                <Clear />
              </IconButton>
            )}
          </Box>
          <Autocomplete
            multiple
            options={availableTags.map(tag => tag.name)}
            value={selectedTags}
            onChange={handleTagFilterChange}
            renderInput={(params) => (
              <TextField
                {...params}
                placeholder="Select tags to filter meetings..."
                variant="outlined"
                size="small"
              />
            )}
            renderTags={(value, getTagProps) =>
              value.map((option, index) => {
                const tag = availableTags.find(t => t.name === option);
                return tag ? (
                  <TagChip
                    tag={tag}
                    {...getTagProps({ index })}
                  />
                ) : (
                  <Chip label={option} size="small" {...getTagProps({ index })} />
                );
              })
            }
            sx={{ maxWidth: 600 }}
          />
          {selectedTags.length > 0 && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Showing {filteredMeetings.length} of {meetings.length} meetings
            </Typography>
          )}
        </Box>

        {/* View Toggle Section */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: { xs: 'stretch', sm: 'center' }, 
            mb: 2,
            flexDirection: { xs: 'column', sm: 'row' },
            gap: { xs: 2, sm: 0 }
          }}>
            <ToggleButtonGroup
              value={viewType}
              exclusive
              onChange={(event, newView) => {
                if (newView !== null) {
                  setViewType(newView);
                }
              }}
              aria-label="view type"
              size={window.innerWidth < 600 ? 'small' : 'medium'}
              sx={{ alignSelf: { xs: 'center', sm: 'flex-start' } }}
            >
              <ToggleButton value="grid" aria-label="grid view">
                <ViewModule sx={{ mr: { xs: 0.5, sm: 1 } }} />
                <Box component="span" sx={{ display: { xs: 'none', sm: 'inline' } }}>Grid</Box>
              </ToggleButton>
              <ToggleButton value="calendar" aria-label="calendar view">
                <CalendarMonth sx={{ mr: { xs: 0.5, sm: 1 } }} />
                <Box component="span" sx={{ display: { xs: 'none', sm: 'inline' } }}>Calendar</Box>
              </ToggleButton>
            </ToggleButtonGroup>

            {viewType === 'calendar' && (
              <Box sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: { xs: 1, sm: 2 },
                flexWrap: { xs: 'wrap', sm: 'nowrap' },
                justifyContent: { xs: 'center', sm: 'flex-end' }
              }}>
                <IconButton onClick={() => navigateCalendar('prev')} size={window.innerWidth < 600 ? 'small' : 'medium'}>
                  <ChevronLeft />
                </IconButton>
                <Typography 
                  variant="h6" 
                  sx={{ 
                    minWidth: { xs: 'auto', sm: 200 }, 
                    textAlign: 'center',
                    fontSize: { xs: '1rem', sm: '1.25rem' },
                    flexShrink: 0
                  }}
                >
                  {calendarView === 'month' && 
                    currentDate.toLocaleDateString('en-US', { year: 'numeric', month: 'long' })
                  }
                  {calendarView === 'week' && 
                    `Week of ${currentDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`
                  }
                  {calendarView === 'day' && 
                    currentDate.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
                  }
                </Typography>
                <IconButton onClick={() => navigateCalendar('next')} size={window.innerWidth < 600 ? 'small' : 'medium'}>
                  <ChevronRight />
                </IconButton>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={goToToday}
                  startIcon={<Today />}
                  sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
                >
                  Today
                </Button>
              </Box>
            )}
          </Box>

          {viewType === 'calendar' && (
            <Tabs
              value={calendarView}
              onChange={(event, newValue) => setCalendarView(newValue)}
              aria-label="calendar view tabs"
            >
              <Tab label="Month" value="month" />
              <Tab label="Week" value="week" />
              <Tab label="Day" value="day" />
            </Tabs>
          )}
        </Box>

        {/* Meetings Section */}
        <Box>
          <Typography variant="h5" fontWeight={600} gutterBottom sx={{ mb: 3 }}>
            {viewType === 'grid' ? 'Your Meetings' : 'Calendar View'}
          </Typography>
          
          {viewType === 'grid' ? (
            // Grid View
            filteredMeetings.length === 0 ? (
              <Paper
                sx={{
                  p: 6,
                  textAlign: 'center',
                  borderRadius: 3,
                  border: '2px dashed #e2e8f0',
                  backgroundColor: 'transparent',
                }}
              >
                <VideoCall sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  {selectedTags.length > 0 ? 'No meetings match the selected tags' : 'No meetings yet'}
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  {selectedTags.length > 0 
                    ? 'Try adjusting your tag filters or create a new meeting'
                    : 'Create your first meeting to get started with AI transcription'
                  }
                </Typography>
              </Paper>
            ) : (
              <Grid container spacing={3}>
                {filteredMeetings.map((meeting, index) => (
                  <Grid item xs={12} sm={6} lg={4} key={meeting.id}>
                    <Fade in={true} timeout={300 + index * 100}>
                      <Card
                        sx={{
                          height: '100%',
                          display: 'flex',
                          flexDirection: 'column',
                          cursor: 'pointer',
                          transition: 'all 0.2s ease-in-out',
                          '&:hover': {
                            transform: 'translateY(-4px)',
                            boxShadow: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
                          },
                        }}
                        onClick={(e) => {
                          // Only navigate if the click didn't come from the dropdown menu or tag manager
                          if (!(e.target as HTMLElement).closest('[data-dropdown-menu]') && 
                              !(e.target as HTMLElement).closest('[data-tag-manager]')) {
                            navigate(`/meeting/${meeting.id}`);
                          }
                        }}
                      >
                        <CardContent sx={{ flexGrow: 1, p: 3 }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                            <Typography variant="h6" component="h2" fontWeight={600} sx={{ flexGrow: 1, pr: 1 }}>
                              {meeting.title}
                            </Typography>
                            <MeetingDropdownMenu
                              meetingId={meeting.id}
                              meetingTitle={meeting.title}
                              onRename={handleRenameMeeting}
                              onDelete={handleDeleteMeeting}
                            />
                          </Box>
                          
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                            <Chip
                              icon={getStatusIcon(meeting.status)}
                              label={meeting.status.charAt(0).toUpperCase() + meeting.status.slice(1)}
                              color={getStatusColor(meeting.status) as any}
                              size="small"
                              variant="outlined"
                            />
                          </Box>

                          {/* Tags Section */}
                          <Box sx={{ mb: 3 }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                              <LocalOffer sx={{ fontSize: 16, color: 'text.secondary' }} />
                              <Typography variant="caption" color="text.secondary">
                                Tags
                              </Typography>
                              <IconButton
                                size="small"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleManageTags(meeting);
                                }}
                                data-tag-manager
                                sx={{ ml: 'auto' }}
                              >
                                <Edit sx={{ fontSize: 16 }} />
                              </IconButton>
                            </Box>
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, minHeight: 24 }}>
                              {meeting.tags.length > 0 ? (
                                meeting.tags.slice(0, 5).map(tag => (
                                  <TagChip key={tag.id} tag={tag} size="small" />
                                ))
                              ) : (
                                <Typography variant="caption" color="text.secondary">
                                  No tags
                                </Typography>
                              )}
                              {meeting.tags.length > 5 && (
                                <Chip
                                  label={`+${meeting.tags.length - 5} more`}
                                  size="small"
                                  variant="outlined"
                                  sx={{ fontSize: '0.7rem' }}
                                />
                              )}
                            </Box>
                          </Box>

                          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                            Created on {new Date(meeting.start_time).toLocaleDateString()}
                          </Typography>

                          <Button
                            variant="contained"
                            fullWidth
                            startIcon={<VideoCall />}
                            sx={{
                              background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                              '&:hover': {
                                background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
                              },
                            }}
                          >
                            Join Meeting
                          </Button>
                        </CardContent>
                      </Card>
                    </Fade>
                  </Grid>
                ))}
              </Grid>
            )
          ) : (
            // Calendar View
            <Box>
              {calendarView === 'month' && renderCalendarMonth()}
              {calendarView === 'week' && renderCalendarWeek()}
              {calendarView === 'day' && renderCalendarDay()}
            </Box>
          )}
        </Box>
      </Container>

      {/* Tag Manager Dialog */}
      {selectedMeetingForTags && (
        <TagManager
          open={tagManagerOpen}
          onClose={() => {
            setTagManagerOpen(false);
            setSelectedMeetingForTags(null);
          }}
          meetingId={selectedMeetingForTags.id}
          currentTags={selectedMeetingForTags.tags}
          onTagsUpdated={handleTagsUpdated}
        />
      )}

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={handleCloseSnackbar}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Dashboard; 