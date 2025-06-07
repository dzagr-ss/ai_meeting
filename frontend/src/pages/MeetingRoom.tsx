import React, { useEffect, useState, useRef, useCallback } from 'react';
import { API_URL } from '../utils/api';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Chip,
  Divider,
  Alert,
  Tabs,
  Tab,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Popover,
  Badge,
  Tooltip,
  Card,
  CardContent,
} from '@mui/material';
import { SelectChangeEvent } from '@mui/material/Select';
import {
  Transcribe,
  Assignment,
  Notes,
  ChecklistRtl,
  History,
  Settings,
  Close,
  Mic,
  People,
  KeyboardArrowDown,
  LocalOffer,
  Edit,
} from '@mui/icons-material';
import { useParams } from 'react-router-dom';
import AudioRecorder from '../components/AudioRecorder';
import { fetchWithAuth } from '../utils/api';
import { useAppSelector } from '../store/hooks';
import ReactMarkdown from 'react-markdown';
import { getSpeakerColor } from '../utils/speakerColors';
import TagChip from '../components/TagChip';
import TagManager from '../components/TagManager';

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

interface AudioDevice {
  deviceId: string;
  label: string;
}

interface TranscriptionSegment {
  speaker: string;
  start_time: number;
  end_time: number;
  text: string;
}

interface TranscriptionData {
  segments: TranscriptionSegment[];
  start_time: number;
  end_time: number;
}

interface StoredTranscription {
  id: number;
  meeting_id: number;
  speaker: string;
  text: string;
  timestamp: string;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`meeting-tabpanel-${index}`}
      aria-labelledby={`meeting-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `meeting-tab-${index}`,
    'aria-controls': `meeting-tabpanel-${index}`,
  };
}

// Utility function to decode HTML entities
const decodeHtmlEntities = (text: string): string => {
    if (!text.includes('&')) return text;
    
    let decoded = text;
    let previousDecoded = '';
    
    // Keep decoding until no more changes occur (handles double/triple encoding)
    while (decoded !== previousDecoded) {
        previousDecoded = decoded;
        decoded = decoded
            .replace(/&quot;/g, '"')
            .replace(/&amp;/g, '&')
            .replace(/&lt;/g, '<')
            .replace(/&gt;/g, '>')
            .replace(/&#x27;/g, "'")
            .replace(/&#x2F;/g, '/');
    }
    
    return decoded;
};

const MeetingRoom: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const token = useAppSelector(state => state.auth.token);
  const [meeting, setMeeting] = useState<Meeting | null>(null);
  const [loadingMeeting, setLoadingMeeting] = useState(false);
  const [tagManagerOpen, setTagManagerOpen] = useState(false);
  const [audioDevices, setAudioDevices] = useState<AudioDevice[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<string>('');
  const [transcriptions, setTranscriptions] = useState<TranscriptionData[]>([]);
  const [storedTranscriptions, setStoredTranscriptions] = useState<StoredTranscription[]>([]);
  const [loadingStoredTranscriptions, setLoadingStoredTranscriptions] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const [audioSettingsAnchor, setAudioSettingsAnchor] = useState<HTMLButtonElement | null>(null);
  const [summary, setSummary] = useState<string>('');
  const [loadingStoredSummaries, setLoadingStoredSummaries] = useState(false);
  const [meetingNotes, setMeetingNotes] = useState<string>('');
  const [actionItems, setActionItems] = useState<string>('');
  const [loadingMeetingNotes, setLoadingMeetingNotes] = useState(false);
  const [loadingActionItems, setLoadingActionItems] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  
  // Ref for the scrollable transcription container
  const transcriptionScrollRef = useRef<HTMLDivElement>(null);
  const [isUserScrolledUp, setIsUserScrolledUp] = useState(false);
  const [hasNewMessages, setHasNewMessages] = useState(false);
  const [newMessagesCount, setNewMessagesCount] = useState(0);
  const [lastSeenLiveSegmentsCount, setLastSeenLiveSegmentsCount] = useState(0);

  // Add polling state for live transcription updates
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);
  const [lastTranscriptionCount, setLastTranscriptionCount] = useState(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  // Load meeting data
  const loadMeetingData = async () => {
    if (!id || !token) return;
    
    setLoadingMeeting(true);
    try {
      const response = await fetchWithAuth(`${API_URL}/meetings/`);
      
      if (response.ok) {
        const meetings = await response.json();
        const currentMeeting = meetings.find((m: Meeting) => m.id === parseInt(id));
        if (currentMeeting) {
          setMeeting(currentMeeting);
        }
      } else {
        console.error('Failed to load meeting data:', response.status);
      }
    } catch (error) {
      console.error('Error loading meeting data:', error);
    } finally {
      setLoadingMeeting(false);
    }
  };

  const handleTagsUpdated = (updatedTags: Tag[]) => {
    if (meeting) {
      setMeeting({ ...meeting, tags: updatedTags });
    }
  };

  useEffect(() => {
    // Get available audio input devices
    const getAudioDevices = async () => {
      try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const audioInputs = devices
          .filter(device => device.kind === 'audioinput')
          .map(device => ({
            deviceId: device.deviceId,
            label: device.label || `Microphone ${device.deviceId.slice(0, 5)}`
          }));
        setAudioDevices(audioInputs);
        if (audioInputs.length > 0) {
          setSelectedDevice(audioInputs[0].deviceId);
        }
      } catch (err) {
        console.error('Error getting audio devices:', err);
      }
    };

    // Load existing transcriptions for this meeting
    const loadStoredTranscriptions = async () => {
      if (!id || !token) return;
      
      setLoadingStoredTranscriptions(true);
      try {
        const response = await fetchWithAuth(`${API_URL}/meetings/${id}/transcriptions`);
        
        if (response.ok) {
          const data = await response.json();
          setStoredTranscriptions(data);
          setLastTranscriptionCount(data.length); // Initialize count for polling
          console.log(`[LoadStoredTranscriptions] Loaded ${data.length} stored transcriptions`);
        } else {
          console.error('Failed to load transcriptions:', response.status);
        }
      } catch (error) {
        console.error('Error loading stored transcriptions:', error);
      } finally {
        setLoadingStoredTranscriptions(false);
      }
    };

    getAudioDevices();
    loadStoredTranscriptions();
    loadMeetingData();
  }, [id, token]);

  // Monitor storedTranscriptions changes
  useEffect(() => {
    console.log('storedTranscriptions state changed:', {
      count: storedTranscriptions.length,
      speakers: storedTranscriptions.map(t => t.speaker),
      refreshKey
    });
  }, [storedTranscriptions, refreshKey]);

  // Listen for custom transcriptions update events
  useEffect(() => {
    const handleTranscriptionsUpdated = (event: CustomEvent) => {
      console.log('[MeetingRoom] Received transcriptionsUpdated event:', event.detail);
      if (event.detail.meetingId === parseInt(id || '0')) {
        console.log('[MeetingRoom] Event is for current meeting, updating transcriptions');
        setStoredTranscriptions(event.detail.transcriptions);
        setRefreshKey(prev => prev + 1);
      }
    };

    window.addEventListener('transcriptionsUpdated', handleTranscriptionsUpdated as EventListener);
    
    return () => {
      window.removeEventListener('transcriptionsUpdated', handleTranscriptionsUpdated as EventListener);
    };
  }, [id]);

  const handleDeviceChange = (event: SelectChangeEvent) => {
    setSelectedDevice(event.target.value);
  };

  const handleAudioSettingsClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAudioSettingsAnchor(event.currentTarget);
  };

  const handleAudioSettingsClose = () => {
    setAudioSettingsAnchor(null);
  };

  const audioSettingsOpen = Boolean(audioSettingsAnchor);

  const handleTranscriptionUpdate = (transcription: TranscriptionData) => {
    console.log('handleTranscriptionUpdate called', { transcription });
    setTranscriptions(prev => [...prev, transcription]);
    console.log('State updated with new segments');
  };

  const handleTranscriptionsRefresh = async () => {
    if (!id || !token) {
      console.log('handleTranscriptionsRefresh called but missing id or token:', { id, token: !!token });
      return;
    }
    
    console.log('Refreshing stored transcriptions after speaker refinement...');
    setLoadingStoredTranscriptions(true);
    try {
      const refreshResponse = await fetchWithAuth(`${API_URL}/meetings/${id}/transcriptions`);
      
      if (refreshResponse.ok) {
        const data = await refreshResponse.json();
        console.log('Previous stored transcriptions count:', storedTranscriptions.length);
        console.log('New stored transcriptions data:', data);
        setStoredTranscriptions(data);
        setRefreshKey(prev => prev + 1); // Force re-render
        console.log('Refreshed stored transcriptions count:', data.length);
        console.log('Forced re-render with refreshKey:', refreshKey + 1);
      } else {
        console.error('Failed to refresh stored transcriptions:', refreshResponse.status);
      }
    } catch (error) {
      console.error('Error refreshing stored transcriptions:', error);
    } finally {
      setLoadingStoredTranscriptions(false);
    }
  };

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Combine stored transcriptions and live transcriptions
  const liveSegments = transcriptions.reduce((acc, t) => acc.concat(t.segments), [] as TranscriptionSegment[]);
  
  // Convert stored transcriptions to segment format
  const storedSegments: TranscriptionSegment[] = storedTranscriptions.map((stored, index) => ({
    speaker: decodeHtmlEntities(stored.speaker),
    start_time: index * 10, // Approximate timing for stored transcriptions
    end_time: (index + 1) * 10,
    text: decodeHtmlEntities(stored.text),
  }));
  
  // Combine all segments (stored first, then live)
  const allSegments = [...storedSegments, ...liveSegments];
  const speakerSet = new Set<string>();
  allSegments.forEach(s => speakerSet.add(s.speaker));
  const uniqueSpeakers = Array.from(speakerSet);

  // Auto-scroll to bottom when new live transcriptions are added
  useEffect(() => {
    if (liveSegments.length > 0 && transcriptionScrollRef.current) {
      // If user hasn't scrolled up, auto-scroll to bottom
      if (!isUserScrolledUp) {
        // Use setTimeout to ensure the new content is rendered before scrolling
        setTimeout(() => {
          if (transcriptionScrollRef.current) {
            transcriptionScrollRef.current.scrollTo({
              top: transcriptionScrollRef.current.scrollHeight,
              behavior: 'smooth'
            });
          }
        }, 100);
        setLastSeenLiveSegmentsCount(liveSegments.length);
      } else {
        // User has scrolled up, calculate new messages count
        const newCount = liveSegments.length - lastSeenLiveSegmentsCount;
        if (newCount > 0) {
          setHasNewMessages(true);
          setNewMessagesCount(newCount);
        }
      }
    }
  }, [liveSegments.length, isUserScrolledUp, lastSeenLiveSegmentsCount]); // Only trigger when the number of live segments changes

  // Handle scroll events to detect if user scrolled up
  const handleScroll = (event: React.UIEvent<HTMLDivElement>) => {
    const container = event.currentTarget;
    const isAtBottom = container.scrollHeight - container.scrollTop <= container.clientHeight + 50; // 50px threshold
    setIsUserScrolledUp(!isAtBottom);
    
    if (isAtBottom) {
      setHasNewMessages(false);
      setNewMessagesCount(0);
      setLastSeenLiveSegmentsCount(liveSegments.length);
    }
  };

  // Function to scroll to bottom manually
  const scrollToBottom = () => {
    if (transcriptionScrollRef.current) {
      transcriptionScrollRef.current.scrollTo({
        top: transcriptionScrollRef.current.scrollHeight,
        behavior: 'smooth'
      });
      setIsUserScrolledUp(false);
      setHasNewMessages(false);
      setNewMessagesCount(0);
      setLastSeenLiveSegmentsCount(liveSegments.length);
    }
  };

  // Polling function to check for new transcriptions during active meetings
  const pollForTranscriptionUpdates = useCallback(async () => {
    if (!id || !token || !meeting) return;
    
    // Only poll if meeting is active (not ended)
    if (meeting.status === 'ended' || meeting.end_time) return;
    
    try {
      const response = await fetchWithAuth(`${API_URL}/meetings/${id}/transcriptions`);
      
      if (response.ok) {
        const data = await response.json();
        
        // Check if there are new transcriptions
        if (data.length !== lastTranscriptionCount) {
          console.log(`[Polling] New transcriptions detected: ${data.length} (was ${lastTranscriptionCount})`);
          setStoredTranscriptions(data);
          setLastTranscriptionCount(data.length);
          setRefreshKey(prev => prev + 1);
        }
      }
    } catch (error) {
      console.error('Error polling for transcription updates:', error);
    }
  }, [id, token, meeting, lastTranscriptionCount]);

  // Set up polling when meeting is active
  useEffect(() => {
    if (meeting && meeting.status === 'active' && !meeting.end_time) {
      console.log('[Polling] Starting transcription polling for active meeting');
      const interval = setInterval(pollForTranscriptionUpdates, 5000); // Poll every 5 seconds
      setPollingInterval(interval);
      
      return () => {
        console.log('[Polling] Cleaning up transcription polling');
        clearInterval(interval);
        setPollingInterval(null);
      };
    } else {
      console.log('[Polling] Meeting not active, stopping polling');
      if (pollingInterval) {
        clearInterval(pollingInterval);
        setPollingInterval(null);
      }
    }
  }, [meeting, pollForTranscriptionUpdates]);

  return (
    <Box sx={{ minHeight: '100vh', backgroundColor: 'background.default', py: 4 }}>
      <Container maxWidth="xl">
        {/* Header */}
        <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box sx={{ flexGrow: 1, mr: 3 }}>
            <Typography 
              variant="h4" 
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
              {meeting?.title || `Meeting Room #${id}`}
            </Typography>
            <Typography variant="h6" color="text.secondary" sx={{ mb: 2 }}>
              AI-powered transcription and analysis
            </Typography>
            
            {/* Tags Section */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <LocalOffer sx={{ fontSize: 20, color: 'text.secondary' }} />
                <Typography variant="body2" color="text.secondary" fontWeight={600}>
                  Tags:
                </Typography>
              </Box>
              
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, alignItems: 'center' }}>
                {meeting?.tags && meeting.tags.length > 0 ? (
                  <>
                    {meeting.tags.slice(0, 8).map(tag => (
                      <TagChip key={tag.id} tag={tag} size="small" />
                    ))}
                    {meeting.tags.length > 8 && (
                      <Chip
                        label={`+${meeting.tags.length - 8} more`}
                        size="small"
                        variant="outlined"
                        sx={{ fontSize: '0.7rem' }}
                      />
                    )}
                  </>
                ) : (
                  <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                    No tags
                  </Typography>
                )}
                
                <IconButton
                  size="small"
                  onClick={() => setTagManagerOpen(true)}
                  sx={{ 
                    ml: 1,
                    color: 'primary.main',
                    '&:hover': {
                      backgroundColor: 'primary.main',
                      color: 'white',
                    },
                  }}
                  disabled={!meeting}
                >
                  <Edit sx={{ fontSize: 18 }} />
                </IconButton>
              </Box>
            </Box>
          </Box>
          
          {/* Audio Settings Button */}
          <Tooltip title="Audio Settings" placement="left">
            <IconButton
              onClick={handleAudioSettingsClick}
              sx={{
                backgroundColor: 'primary.main',
                color: 'white',
                '&:hover': {
                  backgroundColor: 'primary.dark',
                },
                boxShadow: 2,
              }}
            >
              <Settings />
            </IconButton>
          </Tooltip>
        </Box>

        {/* Stats Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)', color: 'white' }}>
              <CardContent sx={{ p: 2.5 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <People sx={{ fontSize: 28 }} />
                  <Box>
                    <Typography variant="h5" fontWeight={700}>
                      {uniqueSpeakers.length}
                    </Typography>
                    <Typography variant="body2" sx={{ opacity: 0.9 }}>
                      Speakers
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)', color: 'white' }}>
              <CardContent sx={{ p: 2.5 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Transcribe sx={{ fontSize: 28 }} />
                  <Box>
                    <Typography variant="h5" fontWeight={700}>
                      {allSegments.length}
                    </Typography>
                    <Typography variant="body2" sx={{ opacity: 0.9 }}>
                      Segments
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Audio Settings Popover */}
        <Popover
          open={audioSettingsOpen}
          anchorEl={audioSettingsAnchor}
          onClose={handleAudioSettingsClose}
          anchorOrigin={{
            vertical: 'bottom',
            horizontal: 'right',
          }}
          transformOrigin={{
            vertical: 'top',
            horizontal: 'right',
          }}
          PaperProps={{
            sx: {
              p: 3,
              minWidth: 350,
              borderRadius: 3,
              boxShadow: '0 10px 40px rgba(0,0,0,0.1)',
            }
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Settings color="primary" />
              <Typography variant="h6" fontWeight={600}>
                Audio Settings
              </Typography>
            </Box>
            <IconButton
              onClick={handleAudioSettingsClose}
              size="small"
              sx={{ color: 'text.secondary' }}
            >
              <Close fontSize="small" />
            </IconButton>
          </Box>
          
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Select your preferred microphone for recording
            </Typography>
            <Chip 
              label={`${audioDevices.length} device${audioDevices.length !== 1 ? 's' : ''} available`}
              size="small"
              color="primary"
              variant="outlined"
            />
          </Box>
          
          <FormControl fullWidth>
            <InputLabel id="audio-device-select-label">Audio Input Device</InputLabel>
            <Select
              labelId="audio-device-select-label"
              id="audio-device-select"
              value={selectedDevice}
              label="Audio Input Device"
              onChange={handleDeviceChange}
            >
              {audioDevices.map((device) => (
                <MenuItem key={device.deviceId} value={device.deviceId}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Mic fontSize="small" color={selectedDevice === device.deviceId ? 'primary' : 'inherit'} />
                    <Typography variant="body2" sx={{ flexGrow: 1 }}>
                      {device.label}
                    </Typography>
                    {selectedDevice === device.deviceId && (
                      <Chip label="Active" size="small" color="success" variant="filled" />
                    )}
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Popover>

        {/* Audio Recorder */}
        <Paper sx={{ p: 3, mb: 4, borderRadius: 3 }}>
          {id && (
            <AudioRecorder
              meetingId={parseInt(id)}
              onTranscriptionUpdate={handleTranscriptionUpdate}
              onTranscriptionsRefresh={handleTranscriptionsRefresh}
              onSummaryChange={(summary, storedSummaries, loading) => {
                setSummary(summary || '');
                setLoadingStoredSummaries(loading);
              }}
              onMeetingNotesChange={(meetingNotes, loading) => {
                setMeetingNotes(meetingNotes || '');
                setLoadingMeetingNotes(loading);
              }}
              onActionItemsChange={(actionItems, loading) => {
                setActionItems(actionItems || '');
                setLoadingActionItems(loading);
              }}
            />
          )}
        </Paper>

        {/* Main Content */}
        <Grid container spacing={4}>
          {/* Live Transcription Section */}
          <Grid item xs={12} lg={7}>
            <Paper sx={{ borderRadius: 3, overflow: 'hidden', position: 'relative' }}>
              <Box sx={{ p: 3, background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.05) 0%, rgba(139, 92, 246, 0.05) 100%)' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Transcribe color="primary" />
                  <Typography variant="h6" fontWeight={600}>
                    Live Transcription
                  </Typography>
                  {allSegments.length > 0 && (
                    <Chip 
                      label={`${allSegments.length} segments`} 
                      size="small" 
                      color="primary" 
                      variant="outlined" 
                    />
                  )}
                </Box>
              </Box>
              <Divider />
              <Box sx={{ p: 3, height: { xs: '400px', lg: '600px' }, overflowY: 'auto' }} key={`transcriptions-${refreshKey}`} ref={transcriptionScrollRef} onScroll={handleScroll}>
                {loadingStoredTranscriptions && (
                  <Alert severity="info" sx={{ mb: 2 }}>
                    Loading previous transcriptions...
                  </Alert>
                )}
                
                {allSegments.length > 0 ? (
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    {storedTranscriptions.length > 0 && (
                      <Box sx={{ mb: 2 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                          <History color="primary" fontSize="small" />
                          <Typography variant="subtitle2" color="primary" fontWeight={600}>
                            Previous Session ({storedTranscriptions.length} segments)
                          </Typography>
                        </Box>
                        {storedSegments.map((segment, index) => (
                          <Box 
                            key={`stored-${index}`} 
                            sx={{ 
                              p: 2, 
                              borderRadius: 2, 
                              backgroundColor: 'rgba(99, 102, 241, 0.05)',
                              border: '1px solid',
                              borderColor: 'rgba(99, 102, 241, 0.2)',
                              mb: 1,
                            }}
                          >
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                              <Chip
                                label={segment.speaker}
                                size="small"
                                variant="outlined"
                                sx={{
                                  color: getSpeakerColor(segment.speaker).color,
                                  backgroundColor: getSpeakerColor(segment.speaker).backgroundColor,
                                  borderColor: getSpeakerColor(segment.speaker).borderColor,
                                  fontWeight: 600,
                                  '&:hover': {
                                    backgroundColor: getSpeakerColor(segment.speaker).backgroundColor,
                                  }
                                }}
                              />
                              <Chip
                                label="Previous"
                                size="small"
                                color="secondary"
                                variant="filled"
                              />
                              <Typography variant="caption" color="text.secondary">
                                {new Date(storedTranscriptions[index].timestamp).toLocaleString()}
                              </Typography>
                            </Box>
                            <Typography variant="body1" sx={{ lineHeight: 1.6 }}>
                              {segment.text}
                            </Typography>
                          </Box>
                        ))}
                      </Box>
                    )}
                    
                    {liveSegments.length > 0 && (
                      <Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                          <Transcribe color="success" fontSize="small" />
                          <Typography variant="subtitle2" color="success.main" fontWeight={600}>
                            Live Session ({liveSegments.length} segments)
                          </Typography>
                        </Box>
                        {liveSegments.map((segment, index) => (
                          <Box 
                            key={`live-${index}`} 
                            sx={{ 
                              p: 2, 
                              borderRadius: 2, 
                              backgroundColor: index % 2 === 0 ? 'grey.50' : 'transparent',
                              border: '1px solid',
                              borderColor: 'grey.200',
                              mb: 1,
                            }}
                          >
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                              <Chip
                                label={segment.speaker}
                                size="small"
                                variant="outlined"
                                sx={{
                                  color: getSpeakerColor(segment.speaker).color,
                                  backgroundColor: getSpeakerColor(segment.speaker).backgroundColor,
                                  borderColor: getSpeakerColor(segment.speaker).borderColor,
                                  fontWeight: 600,
                                  '&:hover': {
                                    backgroundColor: getSpeakerColor(segment.speaker).backgroundColor,
                                  }
                                }}
                              />
                              <Chip
                                label="Live"
                                size="small"
                                color="success"
                                variant="filled"
                              />
                              <Typography variant="caption" color="text.secondary">
                                {formatTime(segment.start_time)} - {formatTime(segment.end_time)}
                              </Typography>
                            </Box>
                            <Typography variant="body1" sx={{ lineHeight: 1.6 }}>
                              {segment.text}
                            </Typography>
                          </Box>
                        ))}
                      </Box>
                    )}
                  </Box>
                ) : (
                  <Box sx={{ textAlign: 'center', py: 8 }}>
                    <Transcribe sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                    <Typography variant="h6" color="text.secondary" gutterBottom>
                      {loadingStoredTranscriptions ? 'Loading transcriptions...' : 'No transcription yet'}
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                      {loadingStoredTranscriptions 
                        ? 'Please wait while we load previous session data'
                        : 'Start recording to see live transcription'
                      }
                    </Typography>
                  </Box>
                )}
              </Box>
              
              {/* Scroll to bottom button */}
              {(isUserScrolledUp && hasNewMessages) && (
                <Box
                  sx={{
                    position: 'absolute',
                    bottom: 20,
                    right: 20,
                    zIndex: 1000,
                  }}
                >
                  <Badge 
                    badgeContent={newMessagesCount} 
                    color="error"
                    sx={{
                      '& .MuiBadge-badge': {
                        fontSize: '0.75rem',
                        minWidth: '20px',
                        height: '20px',
                      }
                    }}
                  >
                    <IconButton
                      onClick={scrollToBottom}
                      sx={{
                        backgroundColor: 'primary.main',
                        color: 'white',
                        boxShadow: 3,
                        '&:hover': {
                          backgroundColor: 'primary.dark',
                          boxShadow: 6,
                        },
                        animation: 'pulse 2s infinite',
                        '@keyframes pulse': {
                          '0%': {
                            boxShadow: '0 0 0 0 rgba(99, 102, 241, 0.7)',
                          },
                          '70%': {
                            boxShadow: '0 0 0 10px rgba(99, 102, 241, 0)',
                          },
                          '100%': {
                            boxShadow: '0 0 0 0 rgba(99, 102, 241, 0)',
                          },
                        },
                      }}
                    >
                      <KeyboardArrowDown />
                    </IconButton>
                  </Badge>
                </Box>
              )}
            </Paper>
          </Grid>

          {/* Meeting Analysis Section with Tabs */}
          <Grid item xs={12} lg={5}>
            <Paper sx={{ borderRadius: 3, overflow: 'hidden', height: { xs: '600px', lg: '700px' }, display: 'flex', flexDirection: 'column' }}>
              <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                <Tabs 
                  value={activeTab} 
                  onChange={handleTabChange} 
                  aria-label="meeting analysis tabs"
                  variant="fullWidth"
                  sx={{
                    '& .MuiTab-root': {
                      minHeight: { xs: 56, lg: 64 },
                      fontSize: { xs: '0.85rem', lg: '0.95rem' },
                      fontWeight: 600,
                    }
                  }}
                >
                  <Tab 
                    icon={<Assignment />} 
                    label="Summary" 
                    {...a11yProps(0)}
                    sx={{ 
                      '&.Mui-selected': { 
                        color: 'success.main',
                        '& .MuiSvgIcon-root': { color: 'success.main' }
                      }
                    }}
                  />
                  <Tab 
                    icon={<Notes />} 
                    label="Notes" 
                    {...a11yProps(1)}
                    sx={{ 
                      '&.Mui-selected': { 
                        color: 'primary.main',
                        '& .MuiSvgIcon-root': { color: 'primary.main' }
                      }
                    }}
                  />
                  <Tab 
                    icon={<ChecklistRtl />} 
                    label="Action Items" 
                    {...a11yProps(2)}
                    sx={{ 
                      '&.Mui-selected': { 
                        color: 'warning.main',
                        '& .MuiSvgIcon-root': { color: 'warning.main' }
                      }
                    }}
                  />
                </Tabs>
              </Box>

              {/* Summary Tab */}
              <TabPanel value={activeTab} index={0}>
                <Box sx={{ height: { xs: '480px', lg: '580px' }, overflowY: 'auto', pr: 1 }}>
                  {summary ? (
                    <Box sx={{
                      '& h1, & h2, & h3, & h4, & h5, & h6': {
                        fontFamily: 'inherit',
                        fontWeight: 600,
                        marginTop: 2,
                        marginBottom: 1,
                        color: 'text.primary'
                      },
                      '& h1': { fontSize: '1.75rem' },
                      '& h2': { fontSize: '1.5rem' },
                      '& h3': { fontSize: '1.25rem' },
                      '& p': {
                        marginTop: 1,
                        marginBottom: 1,
                        lineHeight: 1.8,
                        color: 'text.primary',
                        fontSize: '1rem'
                      },
                      '& ul, & ol': {
                        marginTop: 1,
                        marginBottom: 1,
                        paddingLeft: 3
                      },
                      '& li': {
                        marginBottom: 0.5,
                        lineHeight: 1.7,
                        color: 'text.primary',
                        fontSize: '1rem'
                      },
                      '& strong': {
                        fontWeight: 600,
                        color: 'text.primary'
                      },
                      '& em': {
                        fontStyle: 'italic'
                      },
                      '& code': {
                        backgroundColor: 'grey.100',
                        padding: '4px 8px',
                        borderRadius: 1,
                        fontSize: '0.9rem',
                        fontFamily: 'monospace'
                      },
                      '& blockquote': {
                        borderLeft: '4px solid',
                        borderColor: 'primary.main',
                        paddingLeft: 2,
                        marginLeft: 0,
                        marginTop: 2,
                        marginBottom: 2,
                        fontStyle: 'italic',
                        backgroundColor: 'grey.50',
                        padding: 2,
                        borderRadius: 1
                      }
                    }}>
                      <ReactMarkdown>{summary}</ReactMarkdown>
                    </Box>
                  ) : (
                    <Box sx={{ textAlign: 'center', py: 8 }}>
                      <Assignment sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                      <Typography variant="h6" color="text.secondary" gutterBottom>
                        {loadingStoredSummaries ? 'Generating summary...' : 'No summary yet'}
                      </Typography>
                      <Typography variant="body1" color="text.secondary">
                        {loadingStoredSummaries 
                          ? 'Please wait while we generate a summary of the meeting'
                          : 'A summary will be generated after the meeting ends'
                        }
                      </Typography>
                    </Box>
                  )}
                </Box>
              </TabPanel>

              {/* Meeting Notes Tab */}
              <TabPanel value={activeTab} index={1}>
                <Box sx={{ height: { xs: '480px', lg: '580px' }, overflowY: 'auto', pr: 1 }}>
                  {meetingNotes ? (
                    <Box sx={{
                      '& h1, & h2, & h3, & h4, & h5, & h6': {
                        fontFamily: 'inherit',
                        fontWeight: 600,
                        marginTop: 2,
                        marginBottom: 1,
                        color: 'text.primary'
                      },
                      '& h1': { fontSize: '1.75rem' },
                      '& h2': { fontSize: '1.5rem' },
                      '& h3': { fontSize: '1.25rem' },
                      '& p': {
                        marginTop: 1,
                        marginBottom: 1,
                        lineHeight: 1.8,
                        color: 'text.primary',
                        fontSize: '1rem'
                      },
                      '& ul, & ol': {
                        marginTop: 1,
                        marginBottom: 1,
                        paddingLeft: 3
                      },
                      '& li': {
                        marginBottom: 0.5,
                        lineHeight: 1.7,
                        color: 'text.primary',
                        fontSize: '1rem'
                      },
                      '& strong': {
                        fontWeight: 600,
                        color: 'text.primary'
                      },
                      '& em': {
                        fontStyle: 'italic'
                      },
                      '& code': {
                        backgroundColor: 'grey.100',
                        padding: '4px 8px',
                        borderRadius: 1,
                        fontSize: '0.9rem',
                        fontFamily: 'monospace'
                      },
                      '& blockquote': {
                        borderLeft: '4px solid',
                        borderColor: 'primary.main',
                        paddingLeft: 2,
                        marginLeft: 0,
                        marginTop: 2,
                        marginBottom: 2,
                        fontStyle: 'italic',
                        backgroundColor: 'grey.50',
                        padding: 2,
                        borderRadius: 1
                      }
                    }}>
                      <ReactMarkdown>{meetingNotes}</ReactMarkdown>
                    </Box>
                  ) : (
                    <Box sx={{ textAlign: 'center', py: 8 }}>
                      <Notes sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                      <Typography variant="h6" color="text.secondary" gutterBottom>
                        {loadingMeetingNotes ? 'Generating notes...' : 'No notes yet'}
                      </Typography>
                      <Typography variant="body1" color="text.secondary">
                        {loadingMeetingNotes 
                          ? 'Please wait while we generate detailed meeting notes'
                          : 'Detailed notes will be generated after the meeting ends'
                        }
                      </Typography>
                    </Box>
                  )}
                </Box>
              </TabPanel>

              {/* Action Items Tab */}
              <TabPanel value={activeTab} index={2}>
                <Box sx={{ height: { xs: '480px', lg: '580px' }, overflowY: 'auto', pr: 1 }}>
                  {actionItems ? (
                    <Box sx={{
                      '& h1, & h2, & h3, & h4, & h5, & h6': {
                        fontFamily: 'inherit',
                        fontWeight: 600,
                        marginTop: 2,
                        marginBottom: 1,
                        color: 'text.primary'
                      },
                      '& h1': { fontSize: '1.75rem' },
                      '& h2': { fontSize: '1.5rem' },
                      '& h3': { fontSize: '1.25rem' },
                      '& p': {
                        marginTop: 1,
                        marginBottom: 1,
                        lineHeight: 1.8,
                        color: 'text.primary',
                        fontSize: '1rem'
                      },
                      '& ul, & ol': {
                        marginTop: 1,
                        marginBottom: 1,
                        paddingLeft: 3
                      },
                      '& li': {
                        marginBottom: 0.5,
                        lineHeight: 1.7,
                        color: 'text.primary',
                        fontSize: '1rem'
                      },
                      '& strong': {
                        fontWeight: 600,
                        color: 'text.primary'
                      },
                      '& em': {
                        fontStyle: 'italic'
                      },
                      '& code': {
                        backgroundColor: 'grey.100',
                        padding: '4px 8px',
                        borderRadius: 1,
                        fontSize: '0.9rem',
                        fontFamily: 'monospace'
                      },
                      '& blockquote': {
                        borderLeft: '4px solid',
                        borderColor: 'warning.main',
                        paddingLeft: 2,
                        marginLeft: 0,
                        marginTop: 2,
                        marginBottom: 2,
                        fontStyle: 'italic',
                        backgroundColor: 'grey.50',
                        padding: 2,
                        borderRadius: 1
                      }
                    }}>
                      <ReactMarkdown>{actionItems}</ReactMarkdown>
                    </Box>
                  ) : (
                    <Box sx={{ textAlign: 'center', py: 8 }}>
                      <ChecklistRtl sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                      <Typography variant="h6" color="text.secondary" gutterBottom>
                        {loadingActionItems ? 'Identifying action items...' : 'No action items yet'}
                      </Typography>
                      <Typography variant="body1" color="text.secondary">
                        {loadingActionItems 
                          ? 'Please wait while we identify action items from the meeting'
                          : 'Action items will be identified after the meeting ends'
                        }
                      </Typography>
                    </Box>
                  )}
                </Box>
              </TabPanel>
            </Paper>
          </Grid>
        </Grid>
      </Container>

      {/* Tag Manager Dialog */}
      {meeting && (
        <TagManager
          open={tagManagerOpen}
          onClose={() => setTagManagerOpen(false)}
          meetingId={meeting.id}
          currentTags={meeting.tags}
          onTagsUpdated={handleTagsUpdated}
        />
      )}
    </Box>
  );
};

export default MeetingRoom; 
