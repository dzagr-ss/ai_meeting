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
  const { token } = useAppSelector((state) => state.auth);
  const [newMeetingTitle, setNewMeetingTitle] = useState('');
  const [availableTags, setAvailableTags] = useState<Tag[]>([]);
  const [tagManagerOpen, setTagManagerOpen] = useState(false);
  const [selectedMeetingForTags, setSelectedMeetingForTags] = useState<Meeting | null>(null);
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
    
    try {
      const response = await api.post('/meetings/', { title: newMeetingTitle });
      navigate(`/meeting/${response.data.id}`);
    } catch (err) {
      console.error('Failed to create meeting:', err);
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

  // Filter meetings based on selected tags
  const filteredMeetings = selectedTags.length > 0 
    ? meetings.filter(meeting => 
        meeting.tags.some(tag => selectedTags.includes(tag.name))
      )
    : meetings;

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
                placeholder="e.g., Weekly Team Standup"
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
                disabled={!newMeetingTitle.trim()}
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

        {/* Meetings Grid */}
        <Box>
          <Typography variant="h5" fontWeight={600} gutterBottom sx={{ mb: 3 }}>
            Your Meetings
          </Typography>
          
          {filteredMeetings.length === 0 ? (
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