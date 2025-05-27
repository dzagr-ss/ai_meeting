import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  Box,
  Grid,
  List,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
  Chip,
  Card,
  CardContent,
  Divider,
  LinearProgress,
  Alert,
} from '@mui/material';
import {
  Mic,
  Settings,
  Transcribe,
  Assignment,
  Person,
  AccessTime,
  TrendingUp,
  History,
} from '@mui/icons-material';
import AudioRecorder from '../components/AudioRecorder';
import { useAppSelector } from '../store/hooks';

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

const MeetingRoom: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const token = useAppSelector(state => state.auth.token);
  const [audioDevices, setAudioDevices] = useState<AudioDevice[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<string>('');
  const [transcriptions, setTranscriptions] = useState<TranscriptionData[]>([]);
  const [storedTranscriptions, setStoredTranscriptions] = useState<StoredTranscription[]>([]);
  const [loadingStoredTranscriptions, setLoadingStoredTranscriptions] = useState(false);
  const [lastProcessedCount, setLastProcessedCount] = useState<number | undefined>(undefined);
  const [totalProcessedCount, setTotalProcessedCount] = useState<number | undefined>(undefined);
  const [receivedChunkCount, setReceivedChunkCount] = useState<number | undefined>(undefined);
  const [speakerBufferDuration, setSpeakerBufferDuration] = useState<number | undefined>(undefined);
  const [chunkerProcessedCount, setChunkerProcessedCount] = useState<number | undefined>(undefined);

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
        const response = await fetch(`http://localhost:8000/meetings/${id}/transcriptions`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
        
        if (response.ok) {
          const data = await response.json();
          setStoredTranscriptions(data);
          console.log('Loaded stored transcriptions:', data);
        } else {
          console.error('Failed to load stored transcriptions:', response.status);
        }
      } catch (error) {
        console.error('Error loading stored transcriptions:', error);
      } finally {
        setLoadingStoredTranscriptions(false);
      }
    };

    getAudioDevices();
    loadStoredTranscriptions();
  }, [id, token]);

  const handleDeviceChange = (event: SelectChangeEvent) => {
    setSelectedDevice(event.target.value);
  };

  const handleTranscriptionUpdate = (transcription: TranscriptionData, processedCount?: number, totalProcessedCount?: number, receivedChunkCount?: number, queuedChunkCount?: number, chunkerProcessedCount?: number) => {
    console.log('handleTranscriptionUpdate called', { transcription, processedCount, totalProcessedCount, receivedChunkCount, queuedChunkCount, chunkerProcessedCount });
    setTranscriptions(prev => [...prev, transcription]);
    setLastProcessedCount(processedCount);
    setTotalProcessedCount(totalProcessedCount);
    setReceivedChunkCount(receivedChunkCount);
    setSpeakerBufferDuration(queuedChunkCount);
    setChunkerProcessedCount(chunkerProcessedCount);
    console.log('State updated:', { lastProcessedCount: processedCount, totalProcessedCount, receivedChunkCount, speakerBufferDuration: queuedChunkCount });
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
    speaker: stored.speaker,
    start_time: index * 10, // Approximate timing for stored transcriptions
    end_time: (index + 1) * 10,
    text: stored.text,
  }));
  
  // Combine all segments (stored first, then live)
  const allSegments = [...storedSegments, ...liveSegments];
  const speakerSet = new Set<string>();
  allSegments.forEach(s => speakerSet.add(s.speaker));
  const uniqueSpeakers = Array.from(speakerSet);

  return (
    <Box sx={{ minHeight: '100vh', backgroundColor: 'background.default', py: 4 }}>
      <Container maxWidth="xl">
        {/* Header */}
        <Box sx={{ mb: 4 }}>
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
            Meeting Room #{id}
          </Typography>
          <Typography variant="h6" color="text.secondary">
            AI-powered transcription and analysis
          </Typography>
        </Box>

        {/* Stats Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)', color: 'white' }}>
              <CardContent sx={{ p: 2.5 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Person sx={{ fontSize: 28 }} />
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
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)', color: 'white' }}>
              <CardContent sx={{ p: 2.5 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <TrendingUp sx={{ fontSize: 28 }} />
                  <Box>
                    <Typography variant="h5" fontWeight={700}>
                      {totalProcessedCount || 0}
                    </Typography>
                    <Typography variant="body2" sx={{ opacity: 0.9 }}>
                      Processed
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)', color: 'white' }}>
              <CardContent sx={{ p: 2.5 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <AccessTime sx={{ fontSize: 28 }} />
                  <Box>
                    <Typography variant="h5" fontWeight={700}>
                      {receivedChunkCount || 0}
                    </Typography>
                    <Typography variant="body2" sx={{ opacity: 0.9 }}>
                      Chunks
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Audio Settings */}
        <Paper sx={{ p: 3, mb: 4, borderRadius: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
            <Settings color="primary" />
            <Typography variant="h6" fontWeight={600}>
              Audio Settings
            </Typography>
          </Box>
          <FormControl fullWidth sx={{ maxWidth: 400 }}>
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
                    <Mic fontSize="small" />
                    {device.label}
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Paper>

        {/* Audio Recorder */}
        <Paper sx={{ p: 3, mb: 4, borderRadius: 3 }}>
          {id && (
            <AudioRecorder
              meetingId={parseInt(id)}
              onTranscriptionUpdate={handleTranscriptionUpdate}
            />
          )}
        </Paper>

        {/* Processing Stats */}
        {(lastProcessedCount !== undefined || totalProcessedCount !== undefined || receivedChunkCount !== undefined) && (
          <Paper sx={{ p: 3, mb: 4, borderRadius: 3 }}>
            <Typography variant="h6" fontWeight={600} gutterBottom>
              Processing Statistics
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={4}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Last Chunk Segments
                  </Typography>
                  <Typography variant="h6" fontWeight={600}>
                    {lastProcessedCount !== undefined ? lastProcessedCount : 'N/A'}
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Total Segments
                  </Typography>
                  <Typography variant="h6" fontWeight={600}>
                    {totalProcessedCount !== undefined ? totalProcessedCount : 'N/A'}
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Buffer Duration
                  </Typography>
                  <Typography variant="h6" fontWeight={600}>
                    {speakerBufferDuration !== undefined ? speakerBufferDuration.toFixed(2) + 's' : 'N/A'}
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </Paper>
        )}

        {/* Main Content */}
        <Grid container spacing={4}>
          <Grid item xs={12} lg={8}>
            <Paper sx={{ borderRadius: 3, overflow: 'hidden' }}>
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
              <Box sx={{ p: 3, height: '500px', overflowY: 'auto' }}>
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
                                color="primary"
                                variant="outlined"
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
                                color="primary"
                                variant="outlined"
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
            </Paper>
          </Grid>

          <Grid item xs={12} lg={4}>
            <Paper sx={{ borderRadius: 3, overflow: 'hidden' }}>
              <Box sx={{ p: 3, background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.05) 0%, rgba(5, 150, 105, 0.05) 100%)' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Assignment color="success" />
                  <Typography variant="h6" fontWeight={600}>
                    Action Items
                  </Typography>
                </Box>
              </Box>
              <Divider />
              <Box sx={{ p: 3, height: '500px', overflowY: 'auto' }}>
                <Box sx={{ textAlign: 'center', py: 8 }}>
                  <Assignment sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" color="text.secondary" gutterBottom>
                    No action items yet
                  </Typography>
                  <Typography variant="body1" color="text.secondary">
                    Action items will be automatically extracted from the conversation
                  </Typography>
                </Box>
              </Box>
            </Paper>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
};

export default MeetingRoom; 