import React, { useEffect, useRef, useState, useCallback } from 'react';
import { 
  Box, 
  Button, 
  Typography, 
  CircularProgress, 
  Paper,
  Card,
  CardContent,
  Chip,
  LinearProgress,
  Fade,
  Alert,
} from '@mui/material';
import { styled } from '@mui/material/styles';
import { 
  Mic, 
  MicOff, 
  Stop, 
  PlayArrow,
  Download,
  Summarize,
  Error as ErrorIcon,
  CheckCircle,
  History,
} from '@mui/icons-material';
import { useAppSelector } from '../store/hooks';
import { GoogleGenAI } from '@google/genai';

// Define a constant for the desired audio sample rate
const TARGET_SAMPLE_RATE = 16000;

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

// Define a type for the incoming WebSocket message payload
interface WebSocketMessage {
    type: string;
    data: any; // Use a more specific type if the data structure varies by type
    message?: string; // For error messages
}

const AudioRecorderContainer = styled(Box)(({ theme }) => ({
    display: 'flex',
    flexDirection: 'column',
    gap: theme.spacing(3),
}));

const RecordingButton = styled(Button, {
    shouldForwardProp: (prop) => prop !== 'isRecording',
})<{ isRecording?: boolean }>(({ theme, isRecording }) => ({
    width: 120,
    height: 120,
    borderRadius: '50%',
    fontSize: '2rem',
    fontWeight: 600,
    boxShadow: isRecording 
        ? '0 0 0 4px rgba(239, 68, 68, 0.2), 0 0 20px rgba(239, 68, 68, 0.3)'
        : '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
    background: isRecording 
        ? 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)'
        : 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
    transition: 'all 0.3s ease-in-out',
    '&:hover': {
        transform: 'scale(1.05)',
        boxShadow: isRecording 
            ? '0 0 0 6px rgba(239, 68, 68, 0.3), 0 0 30px rgba(239, 68, 68, 0.4)'
            : '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
    },
    '&:disabled': {
        background: 'linear-gradient(135deg, #94a3b8 0%, #64748b 100%)',
        transform: 'none',
        boxShadow: 'none',
    },
}));

const StatusCard = styled(Card)(({ theme }) => ({
    background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.05) 0%, rgba(139, 92, 246, 0.05) 100%)',
    border: '1px solid rgba(99, 102, 241, 0.1)',
    borderRadius: 16,
}));

interface StoredSummary {
    id: number;
    meeting_id: number;
    content: string;
    generated_at: string;
}

interface AudioRecorderProps {
    meetingId: number;
    onTranscriptionUpdate: (transcription: TranscriptionData, processedCount?: number, totalProcessedCount?: number, receivedChunkCount?: number, queuedChunkCount?: number) => void;
}

const AudioRecorder: React.FC<AudioRecorderProps> = ({ meetingId, onTranscriptionUpdate }) => {
    const [isRecording, setIsRecording] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [isConnecting, setIsConnecting] = useState(false);
    const [summary, setSummary] = useState<string | null>(null);
    const [storedSummaries, setStoredSummaries] = useState<StoredSummary[]>([]);
    const [loadingStoredSummaries, setLoadingStoredSummaries] = useState(false);
    const [transcript, setTranscript] = useState<string | null>(null);
    const audioContextRef = useRef<AudioContext | null>(null);
    const websocketRef = useRef<WebSocket | null>(null);
    const audioSourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
    const audioWorkletNodeRef = useRef<AudioWorkletNode | null>(null);
    const token = useAppSelector(state => state.auth.token);
    const [audioChunks, setAudioChunks] = useState<Blob[]>([]);
    const [audioUrl, setAudioUrl] = useState<string | null>(null);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);

    // Load existing summaries for this meeting
    const loadStoredSummaries = async () => {
        if (!meetingId || !token) return;
        
        setLoadingStoredSummaries(true);
        try {
            const response = await fetch(`http://localhost:8000/meetings/${meetingId}/summaries`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });
            
            if (response.ok) {
                const data = await response.json();
                setStoredSummaries(data);
                console.log('Loaded stored summaries:', data);
            } else {
                console.error('Failed to load stored summaries:', response.status);
            }
        } catch (error) {
            console.error('Error loading stored summaries:', error);
        } finally {
            setLoadingStoredSummaries(false);
        }
    };

    const connectWebSocket = async () => {
        if (!token) {
            setError('Authentication token not found');
            return false;
        }

        setIsConnecting(true);
        setError(null);

        try {
            console.log('Connecting to WebSocket...');
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//localhost:8000/ws/meetings/${meetingId}/stream`;
            console.log('WebSocket URL:', wsUrl);
            
            const ws = new WebSocket(wsUrl);
            websocketRef.current = ws;

            // Wait for WebSocket to open
            await new Promise<void>((resolve, reject) => {
                const timeoutId = setTimeout(() => {
                    reject(new Error('WebSocket connection timeout'));
                }, 5000); // 5 second timeout

                ws.onopen = () => {
                    console.log('WebSocket connected, sending auth...');
                    clearTimeout(timeoutId);
                    // Send authentication message with Bearer token
                    ws.send(JSON.stringify({
                        type: 'auth',
                        token: `Bearer ${token}`
                    }));
                    resolve();
                };
                ws.onerror = (event) => {
                    console.error('WebSocket connection error:', event);
                    clearTimeout(timeoutId);
                    // Check if the error event has a message or code
                    const errorMessage = (event as any).message || `WebSocket error code: ${(event as any).code}`; // Type assertion for error details
                    reject(new Error(`WebSocket connection failed: ${errorMessage}`));
                };
            });

            // Set up message handler after successful connection
            ws.onmessage = (event) => {
                try {
                    const message: WebSocketMessage = JSON.parse(event.data);
                    if (message.type === 'transcription') {
                        const transcriptionData: TranscriptionData = {
                            segments: message.data.segments,
                            start_time: message.data.start_time,
                            end_time: message.data.end_time,
                        };
                        // Pass transcription data and processed_count up to parent
                        onTranscriptionUpdate(transcriptionData, message.data.processed_count, message.data.total_processed_count, message.data.received_chunk_count, message.data.queued_chunk_count);
                    } else if (message.type === 'audio_chunk') {
                        // Assuming the backend sends audio chunk data
                        // const audioChunk = new Float32Array(message.data.audio_chunk); // Convert to Float32Array
                        // const chunkStartTime = message.data.start_time; // Get the start time for the chunk
                        // Call the process_audio_chunk method on the SpeakerIdentifier instance
                        // if (speakerIdentifier.current) {
                        //     const segments = speakerIdentifier.current.process_audio_chunk(audioChunk, chunkStartTime);
                        //     // Handle the segments as needed (e.g., update state or send to parent)
                        // }
                    } else if (message.type === 'error') {
                        console.error('Backend error:', message.message);
                        setError(message.message || 'An unknown backend error occurred.');
                    }
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };

            ws.onclose = (event) => {
                console.log('WebSocket closed:', event.code, event.reason);
                if (event.code === 1008) {
                    if (event.reason === 'Token has expired') {
                        setError('Session expired. Please log in again.');
                        // You might want to trigger a logout or token refresh here
                    } else {
                        setError(`Authentication failed: ${event.reason || 'Unknown reason'}`);
                    }
                } else if (event.code !== 1000) {
                    setError(`WebSocket closed unexpectedly: ${event.reason || `Code: ${event.code}`}`);
                }
                websocketRef.current = null;
                setIsRecording(false); // Stop recording state if websocket closes
            };

            console.log('WebSocket setup complete');
            return true;

        } catch (error) {
            console.error('Error connecting to WebSocket:', error);
            setError(error instanceof Error ? error.message : 'Failed to connect to WebSocket');
            websocketRef.current = null; // Ensure websocketRef is null on error
            return false;
        } finally {
            setIsConnecting(false);
        }
    };

    const startRecording = async () => {
        console.log('Start Recording button clicked and function called');
        if (isRecording) return; // Prevent multiple clicks

        try {
            setError(null); // Clear previous errors
            setIsConnecting(true);

            console.log('Attempting to get user media...');
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    // Use ideal constraints, but don't make them mandatory
                    echoCancellation: { ideal: true },
                    noiseSuppression: { ideal: true },
                    autoGainControl: { ideal: true },
                    channelCount: { ideal: 1 },
                    sampleRate: { ideal: TARGET_SAMPLE_RATE }
                }
            });
            console.log('Successfully got media stream');

            // Create AudioContext if it doesn't exist
            if (!audioContextRef.current) {
                const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)({
                    sampleRate: TARGET_SAMPLE_RATE,
                    latencyHint: 'interactive'
                });
                audioContextRef.current = audioContext;
                console.log('Created AudioContext');
            }

            const audioContext = audioContextRef.current;
            // Resume context if it's suspended (e.g., after user interaction)
            if (audioContext.state === 'suspended') {
                await audioContext.resume();
                console.log('AudioContext resumed');
            }

            // Create MediaStreamAudioSourceNode
            audioSourceRef.current = audioContext.createMediaStreamSource(stream);
            console.log('Created MediaStreamAudioSourceNode');

            // Add an AudioWorklet if possible for better performance and access to raw data
            // Fallback to ScriptProcessorNode if AudioWorklet is not supported or fails

            // Check for AudioWorklet support
            if (typeof AudioWorklet !== 'undefined') {
                try {
                    // Add and create the worklet node
                    // Assumes you have an audio-processor.js file for the worklet in the public directory
                    // It will be served at the root path
                    const workletUrl = '/audio-processor.js'; // Path relative to the server root
                    await audioContext.audioWorklet.addModule(workletUrl);
                    const audioWorkletNode = new AudioWorkletNode(audioContext, 'audio-processor');
                    audioWorkletNodeRef.current = audioWorkletNode;
                    console.log('Created AudioWorkletNode');

                    // Connect source to worklet and worklet to destination (optional, for hearing yourself)
                    audioSourceRef.current.connect(audioWorkletNode);
                    // audioWorkletNode.connect(audioContext.destination); // Uncomment to hear microphone

                    // Set up message port to receive data from the worklet
                    audioWorkletNode.port.onmessage = (event) => {
                        if (event.data.type === 'audio_data') {
                            // Raw Float32Array data received from the worklet
                            const audioData = event.data.audioData;
                            // Send the raw Float32Array data as a binary message
                            if (websocketRef.current?.readyState === WebSocket.OPEN) {
                                try {
                                    // Send the raw Float32Array data as ArrayBuffer
                                    websocketRef.current.send(audioData.buffer);
                                    // console.log('Sent audio data chunk', audioData.buffer.byteLength);
                                } catch (error) {
                                    console.error('Error sending audio data via WebSocket:', error);
                                    setError('Error sending audio data');
                                    stopRecording(); // Stop recording on send error
                                }
                            }
                        }
                    };

                } catch (error) {
                    console.warn('AudioWorklet creation failed, falling back to ScriptProcessorNode:', error);
                    // Fallback to ScriptProcessorNode
                    const bufferSize = 4096; // Adjust buffer size as needed
                    const scriptProcessorNode = audioContext.createScriptProcessor(bufferSize, 1, 1);

                    scriptProcessorNode.onaudioprocess = (event) => {
                        // Get the raw audio data (Float32Array)
                        const audioData = event.inputBuffer.getChannelData(0);

                        if (websocketRef.current?.readyState === WebSocket.OPEN) {
                            try {
                                // Send the raw Float32Array data as ArrayBuffer
                                websocketRef.current.send(audioData.buffer);
                                // console.log('Sent audio data chunk (ScriptProcessor)', audioData.buffer.byteLength);
                            } catch (error) {
                                console.error('Error sending audio data via WebSocket (ScriptProcessor):', error);
                                setError('Error sending audio data');
                                stopRecording(); // Stop recording on send error
                            }
                        }
                    };

                    // Connect source to script processor and script processor to destination (optional)
                    audioSourceRef.current.connect(scriptProcessorNode);
                    scriptProcessorNode.connect(audioContext.destination); // Required for onaudioprocess to fire in some browsers

                }
            } else {
                console.warn('AudioWorklet not supported, using ScriptProcessorNode.');
                // Fallback to ScriptProcessorNode
                const bufferSize = 4096; // Adjust buffer size as needed
                const scriptProcessorNode = audioContext.createScriptProcessor(bufferSize, 1, 1);

                scriptProcessorNode.onaudioprocess = (event) => {
                    // Get the raw audio data (Float32Array)
                    const audioData = event.inputBuffer.getChannelData(0);

                    if (websocketRef.current?.readyState === WebSocket.OPEN) {
                        try {
                            // Send the raw Float32Array data as ArrayBuffer
                            websocketRef.current.send(audioData.buffer);
                            // console.log('Sent audio data chunk (ScriptProcessor)', audioData.buffer.byteLength);
                        } catch (error) {
                            console.error('Error sending audio data via WebSocket (ScriptProcessor):', error);
                            setError('Error sending audio data');
                            stopRecording(); // Stop recording on send error
                        }
                    }
                };

                // Connect source to script processor and script processor to destination (optional)
                audioSourceRef.current.connect(scriptProcessorNode);
                scriptProcessorNode.connect(audioContext.destination); // Required for onaudioprocess to fire in some browsers

            }

            // Connect WebSocket
            const connected = await connectWebSocket();
            if (!connected) {
                // connectWebSocket already sets an error
                stopRecording(); // Clean up media stream and context
                return; // Stop the process if WebSocket connection failed
            }

            // Start sending audio data via the onaudioprocess or AudioWorkletNode message handler
            console.log('Audio processing setup complete, sending raw audio data...');
            setIsRecording(true);
            setIsConnecting(false); // Connection is done now
            setAudioChunks([]);

            mediaRecorderRef.current = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' });
            mediaRecorderRef.current.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    console.log('[AudioRecorder] MediaRecorder data available, size:', event.data.size);
                    setAudioChunks((prev) => [...prev, event.data]);
                }
            };
            mediaRecorderRef.current.onstart = () => {
                console.log('[AudioRecorder] MediaRecorder started successfully');
            };
            mediaRecorderRef.current.onstop = () => {
                console.log('[AudioRecorder] MediaRecorder stopped');
            };
            mediaRecorderRef.current.start(1000); // Collect data every 1 second
            console.log('[AudioRecorder] MediaRecorder start() called');

        } catch (error) {
            console.error('Error starting recording:', error);
            setError(error instanceof Error ? error.message : 'Failed to start recording');
            setIsConnecting(false);
            stopRecording(); // Clean up if anything failed during setup
        }
    };

    const stopRecording = useCallback(async () => {
        console.log('stopRecording function called - starting process...');
        
        try {
            console.log('Setting isRecording to false...');
            setIsRecording(false);

        // Stop MediaRecorder first and wait for all data to be collected
        console.log('Checking MediaRecorder state...');
        console.log('mediaRecorderRef.current:', mediaRecorderRef.current);
        console.log('mediaRecorderRef.current?.state:', mediaRecorderRef.current?.state);
        
        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
            console.log('[AudioRecorder] MediaRecorder state before stop:', mediaRecorderRef.current.state);
            // Set up a promise to wait for the MediaRecorder to finish
            const mediaRecorderStopped = new Promise<void>((resolve) => {
                if (mediaRecorderRef.current) {
                    mediaRecorderRef.current.onstop = () => {
                        console.log('[AudioRecorder] MediaRecorder stopped and all data collected');
                        resolve();
                    };
                    mediaRecorderRef.current.stop();
                    console.log('[AudioRecorder] MediaRecorder stop() called');
                } else {
                    resolve();
                }
            });
            
            // Wait for MediaRecorder to finish collecting data
            await mediaRecorderStopped;
        } else {
            console.log('[AudioRecorder] MediaRecorder is already inactive or null');
        }

        // Stop the media stream tracks
        if (audioSourceRef.current && audioSourceRef.current.mediaStream) {
            audioSourceRef.current.mediaStream.getTracks().forEach(track => track.stop());
            console.log('Media stream tracks stopped');
        }

        // Disconnect nodes and close AudioContext
        if (audioSourceRef.current) {
            audioSourceRef.current.disconnect();
            audioSourceRef.current = null;
        }
        if (audioWorkletNodeRef.current) {
            audioWorkletNodeRef.current.port.onmessage = null; // Remove message handler
            audioWorkletNodeRef.current.disconnect();
            audioWorkletNodeRef.current = null;
        }

        if (websocketRef.current) {
            websocketRef.current.close(1000, 'Recording stopped');
            websocketRef.current = null;
            console.log('WebSocket closed');
        }

        // Get the current audio chunks (use a timeout to ensure all data is collected)
        setTimeout(async () => {
            // Get current audioChunks state
            setAudioChunks(currentChunks => {
                console.log('[AudioRecorder] Current audio chunks length:', currentChunks.length);
                
                // Now upload audio to backend if available (after MediaRecorder has finished)
                if (currentChunks.length > 0 && meetingId && typeof meetingId === 'number' && !isNaN(meetingId)) {
                    const audioBlob = new Blob(currentChunks, { type: 'audio/webm' });
                    const formData = new FormData();
                    formData.append('audio', audioBlob, 'recording.webm');
                    console.log('[AudioRecorder] Uploading audio to backend for meeting', meetingId, 'Blob size:', audioBlob.size);
                    
                    fetch(`http://localhost:8000/meetings/${meetingId}/transcribe`, {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${token}`,
                        },
                        body: formData,
                    })
                    .then(async (uploadResponse) => {
                        console.log('[AudioRecorder] Audio upload response:', uploadResponse.status, uploadResponse.statusText);
                        if (!uploadResponse.ok) {
                            const errorText = await uploadResponse.text();
                            console.error('[AudioRecorder] Audio upload failed:', errorText);
                            setError('Failed to upload audio for transcription: ' + errorText);
                        } else {
                            console.log('[AudioRecorder] Audio upload successful');
                            // After successful upload, fetch the summary
                            if (meetingId && typeof meetingId === 'number' && !isNaN(meetingId)) {
                                console.log('[AudioRecorder] Fetching summary for meeting', meetingId);
                                setTimeout(() => {
                                    fetchSummary(meetingId);
                                }, 1000); // 1 second delay to ensure backend processing
                            }
                        }
                    })
                    .catch((err) => {
                        setError('Failed to upload audio for transcription');
                        console.error('[AudioRecorder] Audio upload error:', err);
                    });

                    // Create audio URL for download
                    const url = URL.createObjectURL(audioBlob);
                    setAudioUrl(url);
                } else {
                    console.log('[AudioRecorder] No audio chunks to upload or invalid meetingId. Chunks length:', currentChunks.length);
                }
                
                return currentChunks; // Return the same chunks (no state change)
            });
        }, 500); // Wait 500ms for all data to be collected
        
        } catch (error) {
            console.error('Error stopping recording:', error);
            setError(error instanceof Error ? error.message : 'Failed to stop recording');
            setIsRecording(false); // Ensure recording state is reset even on error
        }
    }, [meetingId, token]);

    const fetchSummary = async (meetingId: number) => {
        setSummary('Summarizing...');
        console.log('[AudioRecorder] Starting fetchSummary for meeting', meetingId);
        try {
            const response = await fetch(`http://localhost:8000/api/meeting/${meetingId}/summary`);
            console.log('[AudioRecorder] Summary fetch response:', response.status, response.statusText);
            const contentType = response.headers.get('content-type');
            if (!response.ok) {
                // Try to parse JSON error if possible
                let errorMsg = 'No summary available for this meeting.';
                if (contentType && contentType.includes('application/json')) {
                    try {
                        const data = await response.json();
                        if (data && data.error) errorMsg = data.error;
                        console.error('[AudioRecorder] Summary fetch error data:', data);
                    } catch (e) {
                        console.error('[AudioRecorder] Error parsing summary error JSON:', e);
                    }
                } else {
                    // Not JSON, probably HTML error page
                    errorMsg = 'Server error or endpoint not found.';
                    console.error('[AudioRecorder] Summary fetch error: not JSON');
                }
                setSummary(errorMsg);
                return;
            }
            if (contentType && contentType.includes('application/json')) {
                const data = await response.json();
                console.log('[AudioRecorder] Summary fetch data:', data);
                if (!data.summary) {
                    setSummary(data.error || 'No summary available for this meeting.');
                } else {
                    setSummary(data.summary);
                    console.log('[Summary] Received summary:', data.summary);
                    // Reload stored summaries to include the new one
                    loadStoredSummaries();
                }
            } else {
                setSummary('Server error: response is not JSON.');
                console.error('[AudioRecorder] Summary fetch: response is not JSON');
            }
        } catch (err) {
            setSummary('Error summarizing audio');
            console.error('[AudioRecorder] Summary fetch error:', err);
        }
    };

    const summarizeAudioWithGemini = async (audioBlob: Blob, apiKey: string): Promise<{ transcript: string, summary: string }> => {
        // Read file as base64
        const base64Audio = await new Promise<string>((resolve, reject) => {
            const reader = new FileReader();
            reader.onloadend = () => {
                try {
                    const base64data = reader.result as string;
                    const base64Audio = base64data.split(',')[1];
                    resolve(base64Audio);
                } catch (err) {
                    reject(err);
                }
            };
            reader.onerror = () => reject(reader.error);
            reader.readAsDataURL(audioBlob);
        });

        const genAI = new GoogleGenAI({ apiKey, apiVersion: 'v1alpha' });
        // 1. Transcribe
        const transcriptionPrompt = 'Generate a complete, detailed transcript of this audio.';
        const transcriptionContents = [
            { text: transcriptionPrompt },
            { inlineData: { mimeType: audioBlob.type || 'audio/webm', data: base64Audio } },
        ];
        const transcriptionResponse = await genAI.models.generateContent({
            model: 'gemini-2.5-flash-preview-04-17',
            contents: transcriptionContents,
        });
        const transcript = transcriptionResponse.text || '';

        // 2. Summarize
        const summaryPrompt = 'Summarize the main points and action items from this meeting transcript.';
        const summaryContents = [
            { text: summaryPrompt + '\n\n' + transcript },
        ];
        const summaryResponse = await genAI.models.generateContent({
            model: 'gemini-2.5-flash-preview-04-17',
            contents: summaryContents,
        });
        const summary = summaryResponse.text || '';

        return { transcript, summary };
    };

    useEffect(() => {
        // Load stored summaries on component mount
        loadStoredSummaries();
    }, [meetingId, token]);

    useEffect(() => {
        // Cleanup on component unmount only
        return () => {
            stopRecording();
        };
    }, [stopRecording]);

    return (
        <AudioRecorderContainer>
            {/* Error Alert */}
            {error && (
                <Fade in={true}>
                    <Alert 
                        severity="error" 
                        icon={<ErrorIcon />}
                        sx={{ borderRadius: 2 }}
                    >
                        {error}
                    </Alert>
                </Fade>
            )}

            {/* Main Recording Section */}
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Mic color="primary" sx={{ fontSize: 32 }} />
                    <Typography variant="h5" fontWeight={600}>
                        Audio Recording
                    </Typography>
                </Box>

                {/* Recording Button */}
                <Box sx={{ position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <RecordingButton
                        isRecording={isRecording}
                        onClick={isRecording ? stopRecording : startRecording}
                        disabled={isConnecting}
                        variant="contained"
                    >
                        {isConnecting ? (
                            <CircularProgress size={32} sx={{ color: 'white' }} />
                        ) : isRecording ? (
                            <Stop sx={{ fontSize: 32 }} />
                        ) : (
                            <PlayArrow sx={{ fontSize: 32 }} />
                        )}
                    </RecordingButton>
                    
                    {/* Recording pulse animation */}
                    {isRecording && (
                        <Box
                            sx={{
                                position: 'absolute',
                                width: 140,
                                height: 140,
                                borderRadius: '50%',
                                border: '2px solid rgba(239, 68, 68, 0.3)',
                                animation: 'pulse 2s infinite',
                                pointerEvents: 'none', // This prevents the animation from blocking clicks
                                '@keyframes pulse': {
                                    '0%': {
                                        transform: 'scale(1)',
                                        opacity: 1,
                                    },
                                    '100%': {
                                        transform: 'scale(1.2)',
                                        opacity: 0,
                                    },
                                },
                            }}
                        />
                    )}
                </Box>

                {/* Status Text */}
                <Typography 
                    variant="h6" 
                    color={isRecording ? 'error.main' : 'text.secondary'}
                    fontWeight={500}
                >
                    {isConnecting ? 'Connecting to server...' : 
                     isRecording ? 'Recording in progress' : 
                     'Ready to record'}
                </Typography>



                {/* Status Chips */}
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', justifyContent: 'center' }}>
                    <Chip
                        icon={isRecording ? <Mic /> : <MicOff />}
                        label={isRecording ? 'Live' : 'Stopped'}
                        color={isRecording ? 'error' : 'default'}
                        variant={isRecording ? 'filled' : 'outlined'}
                    />
                    {isConnecting && (
                        <Chip
                            icon={<CircularProgress size={16} />}
                            label="Connecting"
                            color="warning"
                            variant="outlined"
                        />
                    )}
                </Box>
            </Box>

            {/* Transcript Section */}
            {transcript && (
                <Fade in={true}>
                    <StatusCard>
                        <CardContent sx={{ p: 3 }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                                <CheckCircle color="success" />
                                <Typography variant="h6" fontWeight={600}>
                                    Transcript
                                </Typography>
                            </Box>
                            <Typography variant="body1" sx={{ lineHeight: 1.6 }}>
                                {transcript}
                            </Typography>
                        </CardContent>
                    </StatusCard>
                </Fade>
            )}

            {/* Summary Section */}
            {(storedSummaries.length > 0 || summary || loadingStoredSummaries) && (
                <Fade in={true}>
                    <StatusCard>
                        <CardContent sx={{ p: 3 }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                                <Summarize color="primary" />
                                <Typography variant="h6" fontWeight={600}>
                                    Meeting Summaries
                                </Typography>
                                {storedSummaries.length > 0 && (
                                    <Chip 
                                        label={`${storedSummaries.length} stored`} 
                                        size="small" 
                                        color="primary" 
                                        variant="outlined" 
                                    />
                                )}
                            </Box>
                            
                            {loadingStoredSummaries && (
                                <Alert severity="info" sx={{ mb: 2 }}>
                                    Loading previous summaries...
                                </Alert>
                            )}
                            
                            {/* Stored Summaries */}
                            {storedSummaries.length > 0 && (
                                <Box sx={{ mb: summary ? 3 : 0 }}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                                        <History color="primary" fontSize="small" />
                                        <Typography variant="subtitle2" color="primary" fontWeight={600}>
                                            Previous Summaries ({storedSummaries.length})
                                        </Typography>
                                    </Box>
                                    {storedSummaries.map((storedSummary, index) => (
                                        <Box 
                                            key={storedSummary.id}
                                            sx={{ 
                                                p: 2, 
                                                borderRadius: 2, 
                                                backgroundColor: 'rgba(99, 102, 241, 0.05)',
                                                border: '1px solid',
                                                borderColor: 'rgba(99, 102, 241, 0.2)',
                                                mb: index < storedSummaries.length - 1 ? 2 : 0,
                                            }}
                                        >
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                                                <Chip
                                                    label="Previous"
                                                    size="small"
                                                    color="secondary"
                                                    variant="filled"
                                                />
                                                <Typography variant="caption" color="text.secondary">
                                                    {new Date(storedSummary.generated_at).toLocaleString()}
                                                </Typography>
                                            </Box>
                                            <Typography variant="body1" sx={{ lineHeight: 1.6 }}>
                                                {storedSummary.content}
                                            </Typography>
                                        </Box>
                                    ))}
                                </Box>
                            )}
                            
                            {/* Current Summary */}
                            {summary && (
                                <Box>
                                    {storedSummaries.length > 0 && (
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                                            <Summarize color="success" fontSize="small" />
                                            <Typography variant="subtitle2" color="success.main" fontWeight={600}>
                                                Latest Summary
                                            </Typography>
                                        </Box>
                                    )}
                                    <Box 
                                        sx={{ 
                                            p: 2, 
                                            borderRadius: 2, 
                                            backgroundColor: storedSummaries.length > 0 ? 'rgba(76, 175, 80, 0.05)' : 'transparent',
                                            border: storedSummaries.length > 0 ? '1px solid' : 'none',
                                            borderColor: storedSummaries.length > 0 ? 'rgba(76, 175, 80, 0.2)' : 'transparent',
                                        }}
                                    >
                                        {storedSummaries.length > 0 && (
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                                                <Chip
                                                    label="Latest"
                                                    size="small"
                                                    color="success"
                                                    variant="filled"
                                                />
                                                <Typography variant="caption" color="text.secondary">
                                                    Just generated
                                                </Typography>
                                            </Box>
                                        )}
                                        <Typography variant="body1" sx={{ lineHeight: 1.6 }}>
                                            {summary}
                                        </Typography>
                                    </Box>
                                </Box>
                            )}
                            
                            {!loadingStoredSummaries && storedSummaries.length === 0 && !summary && (
                                <Box sx={{ textAlign: 'center', py: 4 }}>
                                    <Summarize sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
                                    <Typography variant="body1" color="text.secondary">
                                        No summaries available yet
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        Stop recording to generate a summary
                                    </Typography>
                                </Box>
                            )}
                        </CardContent>
                    </StatusCard>
                </Fade>
            )}

            {/* Download Section */}
            {audioUrl && (
                <Fade in={true}>
                    <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                        <Button
                            variant="outlined"
                            startIcon={<Download />}
                            href={audioUrl}
                            download="meeting_recording.webm"
                            sx={{
                                borderColor: 'primary.main',
                                color: 'primary.main',
                                '&:hover': {
                                    backgroundColor: 'primary.main',
                                    color: 'white',
                                },
                            }}
                        >
                            Download Recording
                        </Button>
                    </Box>
                </Fade>
            )}
        </AudioRecorderContainer>
    );
};

export default AudioRecorder; 