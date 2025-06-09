import React, { useEffect, useRef, useState, useCallback } from 'react';
import { API_URL } from '../utils/api';
import { 
  Box, 
  Button, 
  Typography, 
  CircularProgress, 
  Card,
  CardContent,
  Chip,
  LinearProgress,
  Fade,
  Alert,
  Divider,
} from '@mui/material';
import { styled } from '@mui/material/styles';
import { 
  Mic, 
  MicOff, 
  Stop, 
  Download,
  Error as ErrorIcon,
  CheckCircle,
  Upload,
  AudioFile,
  EventAvailable,
} from '@mui/icons-material';
import { useAppSelector, useAppDispatch } from '../store/hooks';
import { validateToken } from '../store/slices/authSlice';
import { fetchWithAuth } from '../utils/api';
import AudioVisualizer from './AudioVisualizer';

// Define a constant for the desired audio sample rate
const TARGET_SAMPLE_RATE = 16000;

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

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const StatusCard = styled(Card)(({ theme }) => ({
    background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.05) 0%, rgba(139, 92, 246, 0.05) 100%)',
    border: '1px solid rgba(99, 102, 241, 0.1)',
    borderRadius: 16,
}));

export interface StoredSummary {
    id: number;
    meeting_id: number;
    content: string;
    generated_at: string;
}

interface AudioRecorderProps {
    meetingId: number;
    onTranscriptionUpdate: (transcription: TranscriptionData) => void;
    onTranscriptionsRefresh?: () => void;
    onTranscriptChange?: (transcript: string | null) => void;
    onSummaryChange?: (summary: string | null, storedSummaries: StoredSummary[], loading: boolean) => void;
    onMeetingNotesChange?: (meetingNotes: string | null, loading: boolean) => void;
    onActionItemsChange?: (actionItems: string | null, loading: boolean) => void;
}

const AudioRecorder: React.FC<AudioRecorderProps> = ({ meetingId, onTranscriptionUpdate, onTranscriptionsRefresh, onTranscriptChange, onSummaryChange, onMeetingNotesChange, onActionItemsChange }) => {
    const [isRecording, setIsRecording] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [isConnecting, setIsConnecting] = useState(false);
    const [summary, setSummary] = useState<string | null>(null);
    const [storedSummaries, setStoredSummaries] = useState<StoredSummary[]>([]);
    const [loadingStoredSummaries, setLoadingStoredSummaries] = useState(false);
    const [meetingNotes, setMeetingNotes] = useState<string | null>(null);
    const [actionItems, setActionItems] = useState<string | null>(null);
    const [isRefiningspeakers, setIsRefiningspeakers] = useState(false);
    const [speakerRefinementProgress, setSpeakerRefinementProgress] = useState<string>('');
    const [transcript] = useState<string | null>(null);
    const [isUploading, setIsUploading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [isSummarizing, setIsSummarizing] = useState(false);
    const [meetingEnded, setMeetingEnded] = useState(false);
    const [isMeetingEndedInDatabase, setIsMeetingEndedInDatabase] = useState(false);
    const [audioLevel, setAudioLevel] = useState(0); // Audio level for visualization (0-100)
    const audioContextRef = useRef<AudioContext | null>(null);
    const websocketRef = useRef<WebSocket | null>(null);
    const audioSourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
    const audioWorkletNodeRef = useRef<AudioWorkletNode | null>(null);
    const analyserRef = useRef<AnalyserNode | null>(null);
    const animationFrameRef = useRef<number>();
    const token = useAppSelector(state => state.auth.token);
    const dispatch = useAppDispatch();
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const [audioChunks, setAudioChunks] = useState<Blob[]>([]);
    const [audioUrl, setAudioUrl] = useState<string | null>(null);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);

    // Load existing summaries for this meeting
    const loadStoredSummaries = useCallback(async () => {
        if (!meetingId || !token) return;
        
        setLoadingStoredSummaries(true);
        try {
            const response = await fetchWithAuth(`${API_URL}/meetings/${meetingId}/summaries`);
            
            if (response.ok) {
                const data = await response.json();
                setStoredSummaries(data);
                
                // Also extract and set the summary content from the latest summary
                if (data && data.length > 0) {
                    const latestSummary = data[0];
                    console.log('[LoadStoredSummaries] Latest summary loaded');
                    
                    try {
                        // First, decode HTML entities if present
                        let decodedContent = decodeHtmlEntities(latestSummary.content);
                        if (latestSummary.content !== decodedContent) {
                            console.log('[LoadStoredSummaries] Detected and decoded HTML-encoded content');
                        }
                        
                        // Try to parse as JSON to extract summary content
                        const parsed = JSON.parse(decodedContent);
                        console.log('[LoadStoredSummaries] Parsed JSON');
                        
                        if (parsed.summary) {
                            console.log('[LoadStoredSummaries] Setting summary');
                            setSummary(parsed.summary);
                        } else {
                            console.log('[LoadStoredSummaries] No summary field found in parsed JSON');
                            setSummary('No summary content available in the stored data.');
                        }
                    } catch (parseError) {
                        console.error('[LoadStoredSummaries] JSON parse error:', parseError);
                        console.log('[LoadStoredSummaries] Raw content that failed to parse:', latestSummary.content);
                        
                        // If not JSON format, check if it looks like raw JSON string
                        if (latestSummary.content.startsWith('{"') && latestSummary.content.includes('"summary"')) {
                            console.log('[LoadStoredSummaries] Attempting manual extraction from malformed JSON');
                            // This looks like malformed JSON, try to extract summary manually
                            try {
                                const summaryMatch = latestSummary.content.match(/"summary":\s*"([^"]*?)"/);
                                if (summaryMatch) {
                                    console.log('[LoadStoredSummaries] Manual extraction successful');
                                    setSummary(summaryMatch[1]);
                                } else {
                                    console.log('[LoadStoredSummaries] Manual extraction failed - no match found');
                                    setSummary('Unable to parse summary from stored data.');
                                }
                            } catch (extractError) {
                                console.error('[LoadStoredSummaries] Manual extraction error:', extractError);
                                setSummary('Unable to parse summary from stored data.');
                            }
                        } else {
                            console.log('[LoadStoredSummaries] Using content as-is (not JSON-like)');
                            // Use the content as-is only if it doesn't look like raw JSON
                            setSummary(latestSummary.content);
                        }
                    }
                } else {
                    console.log('No stored summaries found');
                }
            } else {
                console.error('Failed to load stored summaries:', response.status);
            }
        } catch (error) {
            console.error('Error loading stored summaries:', error);
        } finally {
            setLoadingStoredSummaries(false);
        }
    }, [meetingId, token]);

    // Load existing meeting notes for this meeting
    const loadStoredMeetingNotes = useCallback(async () => {
        if (!meetingId || !token) return;
        
        try {
            const response = await fetchWithAuth(`${API_URL}/meetings/${meetingId}/notes`);
            
            if (response.ok) {
                const data = await response.json();
                if (data && data.length > 0) {
                    // Get the latest meeting notes (first item since backend returns them ordered by newest first)
                    const latestNotes = data[0];
                    // Decode HTML entities in the meeting notes content
                    const decodedContent = decodeHtmlEntities(latestNotes.content);
                    setMeetingNotes(decodedContent);
                } else {
                    console.log('No stored meeting notes found');
                }
            } else {
                console.error('Failed to load stored meeting notes:', response.status);
            }
        } catch (error) {
            console.error('Error loading stored meeting notes:', error);
        }
    }, [meetingId, token]);

    // Load existing action items from the latest summary for this meeting
    const loadStoredActionItems = useCallback(async () => {
        if (!meetingId || !token) return;
        
        try {
            const response = await fetchWithAuth(`${API_URL}/meetings/${meetingId}/summaries`);
            
            if (response.ok) {
                const data = await response.json();
                if (data && data.length > 0) {
                    // Get the latest summary (first item since backend returns them ordered by newest first)
                    const latestSummary = data[0];
                    try {
                        // First, decode HTML entities if present
                        let decodedContent = decodeHtmlEntities(latestSummary.content);
                        if (latestSummary.content !== decodedContent) {
                            console.log('[LoadStoredActionItems] Detected and decoded HTML-encoded content');
                        }
                        
                        // Try to parse as JSON to extract action items
                        const parsed = JSON.parse(decodedContent);
                        if (parsed.action_items) {
                            // Apply additional HTML decoding to the action items content
                            setActionItems(decodeHtmlEntities(parsed.action_items));
                        } else {
                            console.log('No action items found in stored summary');
                        }
                    } catch (parseError) {
                        console.log('Summary is not in JSON format, no action items available');
                    }
                } else {
                    console.log('No stored summaries found for action items');
                }
            } else {
                console.error('Failed to load stored summaries for action items:', response.status);
            }
        } catch (error) {
            console.error('Error loading stored action items:', error);
        }
    }, [meetingId, token]);

    // Load all stored data for this meeting
    const loadAllStoredData = useCallback(async () => {
        if (!meetingId || !token) return;
        
        // Load all data concurrently
        await Promise.all([
            loadStoredSummaries(),
            loadStoredMeetingNotes(),
            loadStoredActionItems()
        ]);
    }, [meetingId, token, loadStoredSummaries, loadStoredMeetingNotes, loadStoredActionItems]);

    // Check if the meeting is ended in the database
    const checkMeetingStatus = useCallback(async () => {
        if (!meetingId || !token) return;
        
        try {
            const response = await fetchWithAuth(`${API_URL}/meetings/${meetingId}/status`);
            
            if (response.ok) {
                const data = await response.json();
                const isEnded = data.is_ended || false;
                setIsMeetingEndedInDatabase(isEnded);
                console.log(`[AudioRecorder] Meeting ${meetingId} ended status:`, isEnded);
            } else {
                console.error('Failed to check meeting status:', response.status);
            }
        } catch (error) {
            console.error('Error checking meeting status:', error);
        }
    }, [meetingId, token]);

    // Audio level detection function
    const detectAudioLevel = useCallback(() => {
        if (!analyserRef.current || !isRecording) {
            console.log('[AudioLevel] Analyser not available or not recording');
            return;
        }

        const analyser = analyserRef.current;
        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);

        console.log('[AudioLevel] Starting audio level detection with buffer length:', bufferLength);

        const updateLevel = () => {
            if (!isRecording || !analyserRef.current) {
                console.log('[AudioLevel] Stopping audio level detection');
                setAudioLevel(0);
                return;
            }

            // Get frequency data
            analyser.getByteFrequencyData(dataArray);
            
            // Calculate average amplitude across all frequencies
            let sum = 0;
            for (let i = 0; i < bufferLength; i++) {
                sum += dataArray[i];
            }
            const average = sum / bufferLength;
            
            // Convert to percentage (0-100) with better sensitivity
            const level = Math.min(100, (average / 255) * 100 * 3); // 3x amplification for better visibility
            
            // Log occasionally for debugging
            if (Math.random() < 0.01) { // Log ~1% of the time
                console.log('[AudioLevel] Raw average:', average, 'Calculated level:', level);
            }
            
            setAudioLevel(level);

            animationFrameRef.current = requestAnimationFrame(updateLevel);
        };

        updateLevel();
    }, [isRecording]);

    // Start audio level detection when recording starts
    useEffect(() => {
        if (isRecording && analyserRef.current) {
            console.log('[AudioLevel] Starting detection due to recording state change');
            detectAudioLevel();
        } else if (!isRecording && animationFrameRef.current) {
            console.log('[AudioLevel] Stopping detection due to recording state change');
            cancelAnimationFrame(animationFrameRef.current);
            animationFrameRef.current = undefined;
            setAudioLevel(0);
        }

        return () => {
            if (animationFrameRef.current) {
                cancelAnimationFrame(animationFrameRef.current);
                animationFrameRef.current = undefined;
            }
        };
    }, [isRecording, detectAudioLevel]);

    const connectWebSocket = async () => {
        // Validate token before attempting connection
        dispatch(validateToken());
        
        if (!token) {
            setError('Authentication token not found');
            return false;
        }

        setIsConnecting(true);
        setError(null);

        try {
            console.log('Connecting to WebSocket...');
            
            // Use environment-aware WebSocket URL similar to API_URL
            const getWebSocketUrl = (): string => {
                // If we have an API URL, derive WebSocket URL from it
                const apiUrl = API_URL;
                let wsBaseUrl: string;
                
                if (apiUrl.includes('localhost')) {
                    // Development
                    wsBaseUrl = 'ws://localhost:8000';
                } else if (apiUrl.includes('https://')) {
                    // Production with HTTPS
                    wsBaseUrl = apiUrl.replace('https://', 'wss://');
                } else if (apiUrl.includes('http://')) {
                    // HTTP (shouldn't happen in production)
                    wsBaseUrl = apiUrl.replace('http://', 'ws://');
                } else {
                    // Fallback
                    wsBaseUrl = 'wss://aimeeting.up.railway.app';
                }
                
                return `${wsBaseUrl}/ws/meetings/${meetingId}/stream`;
            };
            
            const wsUrl = getWebSocketUrl();
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
                            segments: message.data.segments.map((segment: any) => ({
                                ...segment,
                                text: decodeHtmlEntities(segment.text || ''),
                                speaker: decodeHtmlEntities(segment.speaker || '')
                            })),
                            start_time: message.data.start_time,
                            end_time: message.data.end_time,
                        };
                        // Pass transcription data up to parent
                        onTranscriptionUpdate(transcriptionData);
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
                    if (event.reason === 'Token has expired' || event.reason === 'Invalid or expired token') {
                        setError('Your session has expired. Please log in again to continue recording.');
                        // Use the dispatch we have available instead of importing
                        dispatch(validateToken()); // This will clear the invalid token
                        setTimeout(() => {
                            window.location.href = '/login';
                        }, 2000); // Give user time to read the message
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

            // Create AnalyserNode for audio level detection
            analyserRef.current = audioContext.createAnalyser();
            analyserRef.current.fftSize = 512; // Smaller FFT for faster updates
            analyserRef.current.smoothingTimeConstant = 0.3; // Less smoothing for more responsive updates
            analyserRef.current.minDecibels = -90;
            analyserRef.current.maxDecibels = -10;
            
            // Connect source to analyser for level detection
            audioSourceRef.current.connect(analyserRef.current);
            console.log('Created and connected AnalyserNode');

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
        if (analyserRef.current) {
            analyserRef.current.disconnect();
            analyserRef.current = null;
        }
        if (animationFrameRef.current) {
            cancelAnimationFrame(animationFrameRef.current);
            animationFrameRef.current = undefined;
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
                    
                    fetchWithAuth(`${API_URL}/meetings/${meetingId}/transcribe`, {
                        method: 'POST',
                        body: formData,
                    })
                    .then(async (uploadResponse) => {
                        if (!uploadResponse.ok) {
                            const errorText = await uploadResponse.text();
                            console.error('[AudioRecorder] Audio upload failed:', errorText);
                            setError('Failed to upload audio: ' + errorText);
                        } else {
                            console.log('[AudioRecorder] Audio upload successful');
                            // Reload stored summaries to include the new one
                            loadAllStoredData();
                        }
                    })
                    .catch((err) => {
                        setError('Failed to upload audio');
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
    }, [meetingId, loadAllStoredData]);

    const fetchSummary = async (meetingId: number) => {
        if (!token) {
            setSummary('Authentication required to fetch summary.');
            setMeetingNotes('Authentication required to fetch meeting notes.');
            setActionItems('Authentication required to fetch action items.');
            console.error('[AudioRecorder] No token available for summary fetch');
            return;
        }
        
        setSummary('Summarizing...');
        setMeetingNotes('Generating meeting notes...');
        setActionItems('Identifying action items...');
        console.log('[AudioRecorder] Starting fetchSummary for meeting', meetingId);
        try {
            const response = await fetchWithAuth(`${API_URL}/api/meeting/${meetingId}/summary`);
            console.log('[AudioRecorder] Summary fetch response:', response.status, response.statusText);
            const contentType = response.headers.get('content-type');
            if (!response.ok) {
                // Try to parse JSON error if possible
                let errorMsg = 'No summary available for this meeting.';
                if (contentType && contentType.includes('application/json')) {
                    try {
                        const data = await response.json();
                        if (data && data.error) {
                            // Check if it's the "no audio files" error and show a more user-friendly message
                            if (data.error.includes('No audio files found for this meeting')) {
                                errorMsg = 'No audio has been recorded or uploaded for this meeting yet. Please record audio or upload an audio file first.';
                            } else {
                                errorMsg = data.error;
                            }
                        }
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
                setMeetingNotes(errorMsg);
                setActionItems(errorMsg);
                return;
            }
            if (contentType && contentType.includes('application/json')) {
                const data = await response.json();
                console.log('[AudioRecorder] Summary fetch data:', data);
                
                // Handle structured response
                if (data.summary !== undefined || data.meeting_notes !== undefined || data.action_items !== undefined) {
                    setSummary(data.summary ? decodeHtmlEntities(data.summary) : 'No summary available for this meeting.');
                    setMeetingNotes(data.meeting_notes ? decodeHtmlEntities(data.meeting_notes) : 'No meeting notes available for this meeting.');
                    setActionItems(data.action_items ? decodeHtmlEntities(data.action_items) : 'No action items identified for this meeting.');
                    console.log('[Summary] Received structured content:', {
                        summary: data.summary,
                        meetingNotes: data.meeting_notes,
                        actionItems: data.action_items
                    });
                    // Reload stored summaries to include the new one
                    loadAllStoredData();
                } else if (data.error) {
                    const errorMsg = data.error || 'No content available for this meeting.';
                    setSummary(errorMsg);
                    setMeetingNotes(errorMsg);
                    setActionItems(errorMsg);
                } else {
                    // Legacy format - single summary field
                    setSummary(data.summary ? decodeHtmlEntities(data.summary) : 'No summary available for this meeting.');
                    setMeetingNotes('No structured meeting notes available.');
                    setActionItems('No action items identified.');
                }
            } else {
                const errorMsg = 'Server error: response is not JSON.';
                setSummary(errorMsg);
                setMeetingNotes(errorMsg);
                setActionItems(errorMsg);
                console.error('[AudioRecorder] Summary fetch: response is not JSON');
            }
        } catch (err) {
            const errorMsg = 'Error summarizing audio';
            setSummary(errorMsg);
            setMeetingNotes(errorMsg);
            setActionItems(errorMsg);
            console.error('[AudioRecorder] Summary fetch error:', err);
        }
    };

    const refineSpeakerDiarization = async (meetingId: number) => {
        if (!token) {
            console.error('[AudioRecorder] No token available for speaker refinement');
            return;
        }
        
        setIsRefiningspeakers(true);
        setSpeakerRefinementProgress('Initializing speaker refinement...');
        console.log('[AudioRecorder] Starting speaker diarization refinement for meeting', meetingId);
        console.log('[AudioRecorder] onTranscriptionsRefresh callback available:', !!onTranscriptionsRefresh);
        
        try {
            setSpeakerRefinementProgress('Processing speakers with simplified approach...');
            
            // Create an AbortController for request cancellation with shorter timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => {
                controller.abort();
            }, 2 * 60 * 1000); // Reduced to 2 minute timeout
            
            const response = await fetchWithAuth(`${API_URL}/meetings/${meetingId}/refine-speakers`, {
                method: 'POST',
                signal: controller.signal,
            });
            
            clearTimeout(timeoutId);
            
            console.log('[AudioRecorder] Speaker refinement response:', response.status, response.statusText);
            
            if (response.ok) {
                setSpeakerRefinementProgress('Updating transcriptions...');
                const data = await response.json();
                console.log('[AudioRecorder] Speaker refinement successful:', data);
                console.log(`[SpeakerRefinement] Processed ${data.audio_files_processed} audio files, updated ${data.transcriptions_updated} transcriptions`);
                
                setSpeakerRefinementProgress('Refreshing transcriptions...');
                
                // Trigger refresh of stored transcriptions in parent component
                if (onTranscriptionsRefresh) {
                    console.log('[AudioRecorder] Triggering transcriptions refresh after speaker refinement');
                    // Add a small delay to ensure database updates are committed
                    setTimeout(() => {
                        onTranscriptionsRefresh();
                        setSpeakerRefinementProgress('Speaker refinement completed successfully!');
                    }, 500);
                }
                
                // Also try direct refresh as backup
                console.log('[AudioRecorder] Also triggering direct transcriptions refresh as backup');
                setTimeout(async () => {
                    try {
                        const refreshResponse = await fetchWithAuth(`${API_URL}/meetings/${meetingId}/transcriptions`);
                        if (refreshResponse.ok) {
                            const refreshData = await refreshResponse.json();
                            console.log('[AudioRecorder] Direct refresh successful, got', refreshData.length, 'transcriptions');
                            // Emit a custom event that the parent can listen to
                            window.dispatchEvent(new CustomEvent('transcriptionsUpdated', { 
                                detail: { transcriptions: refreshData, meetingId } 
                            }));
                        }
                    } catch (err) {
                        console.error('[AudioRecorder] Direct refresh failed:', err);
                    }
                }, 1000);
            } else {
                const errorText = await response.text();
                console.error('[AudioRecorder] Speaker refinement failed:', errorText);
                
                // Check if it's the "no audio files" error and show a more user-friendly message
                if (errorText.includes('No audio files found for this meeting')) {
                    setSpeakerRefinementProgress('No audio files found. Please record or upload audio first.');
                } else {
                    setSpeakerRefinementProgress('Speaker refinement failed. Please try again.');
                }
                
                setTimeout(() => {
                    setSpeakerRefinementProgress('');
                }, 3000);
                throw new Error(`Speaker refinement failed: ${response.status} ${response.statusText}`);
            }
        } catch (err) {
            if (err instanceof Error && err.name === 'AbortError') {
                console.error('[AudioRecorder] Speaker refinement was aborted due to timeout');
                setSpeakerRefinementProgress('Speaker refinement timed out. Using simplified approach next time.');
                // Don't throw error for timeout, just show message
                setTimeout(() => {
                    setSpeakerRefinementProgress('');
                }, 4000);
            } else {
                console.error('[AudioRecorder] Speaker refinement error:', err);
                setSpeakerRefinementProgress('Speaker refinement error. Please try again.');
                setTimeout(() => {
                    setSpeakerRefinementProgress('');
                }, 3000);
                throw err;
            }
        } finally {
            setTimeout(() => {
                setIsRefiningspeakers(false);
                if (!speakerRefinementProgress.includes('completed') && !speakerRefinementProgress.includes('timed out')) {
                    setSpeakerRefinementProgress('');
                }
            }, 2000);
        }
    };

    const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
            // Check if file is an audio file
            if (!file.type.startsWith('audio/')) {
                setError('Please select an audio file');
                return;
            }
            
            // Check file size (limit to 100MB)
            const maxSize = 100 * 1024 * 1024; // 100MB
            if (file.size > maxSize) {
                setError('File size must be less than 100MB');
                return;
            }
            
            setSelectedFile(file);
            setError(null);
        }
    };

    const uploadAudioFile = async () => {
        if (!selectedFile || !token || !meetingId) {
            setError('Please select a file and ensure you are authenticated');
            return;
        }

        setIsUploading(true);
        setUploadProgress(0);
        setError(null);

        try {
            const formData = new FormData();
            formData.append('audio', selectedFile);

            // Create XMLHttpRequest to track upload progress
            const xhr = new XMLHttpRequest();
            
            // Set up progress tracking
            xhr.upload.addEventListener('progress', (event) => {
                if (event.lengthComputable) {
                    const progress = Math.round((event.loaded / event.total) * 100);
                    setUploadProgress(progress);
                }
            });

            // Set up response handling
            const uploadPromise = new Promise<Response>((resolve, reject) => {
                xhr.onload = () => {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        // Create a Response-like object
                        const response = {
                            ok: true,
                            status: xhr.status,
                            statusText: xhr.statusText,
                            json: () => Promise.resolve(JSON.parse(xhr.responseText)),
                            text: () => Promise.resolve(xhr.responseText)
                        } as Response;
                        resolve(response);
                    } else {
                        reject(new Error(`Upload failed: ${xhr.status} ${xhr.statusText}`));
                    }
                };
                xhr.onerror = () => reject(new Error('Upload failed'));
                xhr.onabort = () => reject(new Error('Upload aborted'));
            });

            // Start the upload
            xhr.open('POST', `${API_URL}/meetings/${meetingId}/transcribe`);
            xhr.setRequestHeader('Authorization', `Bearer ${token}`);
            xhr.send(formData);

            // Wait for upload to complete
            const response = await uploadPromise;

            if (response.ok) {
                setUploadProgress(100);
                
                // Clear the selected file
                setSelectedFile(null);
                
                // Reset file input
                const fileInput = document.getElementById('audio-file-input') as HTMLInputElement;
                if (fileInput) {
                    fileInput.value = '';
                }

                // Note: No longer automatically triggering summary and speaker refinement here
                // These will be triggered manually by the "Meeting Ended" button

                // Trigger transcriptions refresh
                if (onTranscriptionsRefresh) {
                    setTimeout(() => {
                        onTranscriptionsRefresh();
                    }, 1000);
                }
            } else {
                const errorText = await response.text();
                console.error('[AudioRecorder] File upload failed:', errorText);
                setError('Failed to upload audio: ' + errorText);
            }
        } catch (error) {
            console.error('[AudioRecorder] File upload error:', error);
            setError(error instanceof Error ? error.message : 'Failed to upload audio file');
        } finally {
            setIsUploading(false);
            setUploadProgress(0);
        }
    };

    const handleMeetingEnded = async () => {
        if (!meetingId || !token) {
            setError('Meeting ID or authentication token not available');
            return;
        }

        // First, check if there are any transcriptions for this meeting
        try {
            const transcriptionsResponse = await fetchWithAuth(`${API_URL}/meetings/${meetingId}/transcriptions`);
            if (transcriptionsResponse.ok) {
                const transcriptionsData = await transcriptionsResponse.json();
                if (!transcriptionsData || transcriptionsData.length === 0) {
                    setError('No audio has been recorded or uploaded for this meeting yet. Please record audio or upload an audio file before ending the meeting.');
                    return;
                }
                console.log(`[AudioRecorder] Found ${transcriptionsData.length} transcriptions for meeting ${meetingId}`);
                
                // Check if all transcriptions are just placeholder transcriptions
                const realTranscriptions = transcriptionsData.filter((t: any) => 
                    !(t.speaker === "System" && t.text && t.text.includes("Audio file uploaded:"))
                );
                
                if (realTranscriptions.length === 0 && transcriptionsData.length > 0) {
                    console.log(`[AudioRecorder] Found ${transcriptionsData.length} placeholder transcriptions, proceeding with summary generation`);
                }
            } else {
                console.warn('[AudioRecorder] Could not check transcriptions, proceeding anyway');
            }
        } catch (error) {
            console.warn('[AudioRecorder] Error checking transcriptions:', error);
            // Continue anyway - the backend will handle the error
        }

        setIsSummarizing(true);
        setMeetingEnded(true);
        
        try {
            console.log('[AudioRecorder] Meeting ended - starting summarization and speaker refinement');
            
            // First, mark the meeting as ended in the database
            try {
                const endMeetingResponse = await fetchWithAuth(`${API_URL}/meetings/${meetingId}/end`, {
                    method: 'POST'
                });
                
                if (endMeetingResponse.ok) {
                    const endMeetingData = await endMeetingResponse.json();
                    console.log('[AudioRecorder] Meeting marked as ended in database:', endMeetingData);
                    setIsMeetingEndedInDatabase(true);
                } else {
                    console.warn('[AudioRecorder] Failed to mark meeting as ended in database:', endMeetingResponse.status);
                }
            } catch (error) {
                console.warn('[AudioRecorder] Error marking meeting as ended:', error);
                // Continue with the process even if this fails
            }
            
            // Use Promise.all to run processes concurrently but with proper error handling
            const promises = [];
            
            // Add speaker refinement with timeout
            const speakerRefinementPromise = new Promise(async (resolve, reject) => {
                try {
                    // Set a timeout for speaker refinement (5 minutes max)
                    const timeoutId = setTimeout(() => {
                        reject(new Error('Speaker refinement timed out after 5 minutes'));
                    }, 5 * 60 * 1000);
                    
                    await refineSpeakerDiarization(meetingId);
                    clearTimeout(timeoutId);
                    resolve('Speaker refinement completed');
                } catch (error) {
                    reject(error);
                }
            });
            
            promises.push(speakerRefinementPromise);
            
            // Wait for speaker refinement to complete first
            try {
                await Promise.race([
                    speakerRefinementPromise,
                    new Promise((_, reject) => 
                        setTimeout(() => reject(new Error('Speaker refinement timeout')), 5 * 60 * 1000)
                    )
                ]);
                console.log('[AudioRecorder] Speaker refinement completed');
            } catch (error) {
                console.warn('[AudioRecorder] Speaker refinement failed or timed out:', error);
                // Continue with summary generation even if speaker refinement fails
            }
            
            // Then fetch summary (which includes meeting notes and action items)
            try {
                await fetchSummary(meetingId);
                console.log('[AudioRecorder] Summary generation completed');
            } catch (error) {
                console.error('[AudioRecorder] Summary generation failed:', error);
                throw new Error('Failed to generate meeting summary');
            }
            
            console.log('[AudioRecorder] Meeting ended process completed successfully');
        } catch (error) {
            console.error('[AudioRecorder] Error in meeting ended process:', error);
            setError(`Failed to process meeting summary: ${error instanceof Error ? error.message : 'Unknown error'}`);
        } finally {
            setIsSummarizing(false);
        }
    };

    useEffect(() => {
        // Load all stored data (summaries, meeting notes, action items) and check meeting status on component mount
        loadAllStoredData();
        checkMeetingStatus();
    }, [meetingId, loadAllStoredData, checkMeetingStatus]);

    useEffect(() => {
        // Cleanup on component unmount only
        return () => {
            stopRecording();
        };
    }, [stopRecording]);

    useEffect(() => {
        if (onTranscriptChange) {
            onTranscriptChange(transcript);
        }
    }, [transcript, onTranscriptChange]);

    useEffect(() => {
        if (onSummaryChange) {
            onSummaryChange(summary, storedSummaries, loadingStoredSummaries);
        }
    }, [summary, storedSummaries, loadingStoredSummaries, onSummaryChange]);

    useEffect(() => {
        if (onMeetingNotesChange) {
            onMeetingNotesChange(meetingNotes, loadingStoredSummaries);
        }
    }, [meetingNotes, loadingStoredSummaries, onMeetingNotesChange]);

    useEffect(() => {
        if (onActionItemsChange) {
            onActionItemsChange(actionItems, loadingStoredSummaries);
        }
    }, [actionItems, loadingStoredSummaries, onActionItemsChange]);

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

            {/* Show meeting ended message if meeting is ended in database */}
            {isMeetingEndedInDatabase ? (
                <Fade in={true}>
                    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3, py: 4 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                            <CheckCircle color="success" sx={{ fontSize: 48 }} />
                            <Typography variant="h4" fontWeight={600} color="success.main">
                                Meeting Ended
                            </Typography>
                        </Box>
                        
                        <Alert 
                            severity="success" 
                            sx={{ 
                                borderRadius: 2,
                                maxWidth: 600,
                                '& .MuiAlert-message': {
                                    textAlign: 'center'
                                }
                            }}
                        >
                            <Typography variant="body1">
                                <strong>This meeting has been completed.</strong><br />
                                You can view the meeting summary, notes, and action items below.
                                Recording and uploading are no longer available for this meeting.
                            </Typography>
                        </Alert>

                        <Chip
                            icon={<CheckCircle />}
                            label="Meeting Completed"
                            color="success"
                            variant="filled"
                            sx={{ fontSize: '1rem', py: 2, px: 3 }}
                        />
                    </Box>
                </Fade>
            ) : (
                <>
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
                                disabled={isConnecting || meetingEnded || isUploading}
                                variant="contained"
                            >
                                {isConnecting ? (
                                    <CircularProgress size={32} sx={{ color: 'white' }} />
                                ) : isRecording ? (
                                    <Stop sx={{ fontSize: 32 }} />
                                ) : (
                                    <Mic sx={{ fontSize: 32 }} />
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
                            color={isRecording ? 'error.main' : meetingEnded ? 'success.main' : 'text.secondary'}
                            fontWeight={500}
                        >
                            {isConnecting ? 'Connecting to server...' : 
                             isRecording ? 'Recording in progress' : 
                             meetingEnded ? 'Meeting ended' :
                             'Ready to record'}
                        </Typography>

                        {/* Audio Visualizer */}
                        <AudioVisualizer
                            isActive={isRecording}
                            audioLevel={audioLevel}
                            barCount={24}
                            height={50}
                            width={280}
                            color={isRecording ? '#ef4444' : '#6366f1'}
                            backgroundColor="rgba(0, 0, 0, 0.02)"
                        />

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
                            {meetingEnded && (
                                <Chip
                                    icon={<CheckCircle />}
                                    label="Meeting Ended"
                                    color="success"
                                    variant="filled"
                                />
                            )}
                            {isSummarizing && (
                                <Chip
                                    icon={<CircularProgress size={16} />}
                                    label="Generating Summary"
                                    color="info"
                                    variant="outlined"
                                />
                            )}
                            {isRefiningspeakers && (
                                <Chip
                                    icon={<CircularProgress size={16} />}
                                    label={speakerRefinementProgress || "Refining Speakers"}
                                    color="info"
                                    variant="outlined"
                                    sx={{ maxWidth: 350 }}
                                />
                            )}
                        </Box>
                    </Box>

                    {/* File Upload Section */}
                    <Divider sx={{ my: 2 }}>
                        <Typography variant="body2" color="text.secondary">
                            OR
                        </Typography>
                    </Divider>

                    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                            <AudioFile color="primary" sx={{ fontSize: 32 }} />
                            <Typography variant="h6" fontWeight={600}>
                                Upload Audio File
                            </Typography>
                        </Box>

                        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, width: '100%', maxWidth: 400 }}>
                            {/* File Input */}
                            <input
                                id="audio-file-input"
                                type="file"
                                accept="audio/*"
                                onChange={handleFileSelect}
                                style={{ display: 'none' }}
                            />
                            
                            <Box sx={{ display: 'flex', gap: 2, width: '100%' }}>
                                <Button
                                    variant="outlined"
                                    component="label"
                                    htmlFor="audio-file-input"
                                    startIcon={<Upload />}
                                    disabled={isUploading || isRecording || meetingEnded}
                                    sx={{ flex: 1 }}
                                >
                                    Choose Audio File
                                </Button>
                                
                                {selectedFile && (
                                    <Button
                                        variant="contained"
                                        onClick={uploadAudioFile}
                                        disabled={isUploading || isRecording || meetingEnded}
                                        startIcon={isUploading ? <CircularProgress size={16} /> : <Upload />}
                                        sx={{ flex: 1 }}
                                    >
                                        {isUploading ? 'Uploading...' : 'Upload Audio'}
                                    </Button>
                                )}
                            </Box>

                            {/* Selected File Info */}
                            {selectedFile && (
                                <Fade in={true}>
                                    <Card sx={{ width: '100%', bgcolor: 'grey.50' }}>
                                        <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                                            <Typography variant="body2" color="text.secondary" gutterBottom>
                                                Selected File:
                                            </Typography>
                                            <Typography variant="body1" fontWeight={500}>
                                                {selectedFile.name}
                                            </Typography>
                                            <Typography variant="caption" color="text.secondary">
                                                Size: {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                                            </Typography>
                                        </CardContent>
                                    </Card>
                                </Fade>
                            )}

                            {/* Upload Progress */}
                            {isUploading && (
                                <Fade in={true}>
                                    <Box sx={{ width: '100%' }}>
                                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                            <Typography variant="body2" color="text.secondary">
                                                Uploading...
                                            </Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                {uploadProgress}%
                                            </Typography>
                                        </Box>
                                        <LinearProgress 
                                            variant="determinate" 
                                            value={uploadProgress} 
                                            sx={{ borderRadius: 1, height: 8 }}
                                        />
                                    </Box>
                                </Fade>
                            )}

                            {/* Upload Status Chips */}
                            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', justifyContent: 'center' }}>
                                {isUploading && (
                                    <Chip
                                        icon={<CircularProgress size={16} />}
                                        label="Processing Upload"
                                        color="info"
                                        variant="outlined"
                                    />
                                )}
                                {selectedFile && !isUploading && (
                                    <Chip
                                        icon={<AudioFile />}
                                        label="File Ready"
                                        color="success"
                                        variant="outlined"
                                    />
                                )}
                            </Box>
                        </Box>
                    </Box>

                    {/* Meeting Ended Button - Moved here after Upload section */}
                    {!isRecording && !meetingEnded && (
                        <Fade in={true}>
                            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
                                {/* Helpful note */}
                                <Alert 
                                    severity="info" 
                                    sx={{ 
                                        borderRadius: 2,
                                        maxWidth: 600,
                                        '& .MuiAlert-message': {
                                            textAlign: 'center'
                                        }
                                    }}
                                >
                                    <Typography variant="body2">
                                        <strong>Ready to end the meeting?</strong><br />
                                        Make sure you've recorded audio or uploaded audio files first. 
                                        The system will then transcribe uploaded files, perform speaker diarization, and generate a summary with meeting notes and action items.
                                    </Typography>
                                </Alert>
                                
                                <Button
                                    variant="contained"
                                    size="large"
                                    onClick={handleMeetingEnded}
                                    disabled={isSummarizing}
                                    startIcon={isSummarizing ? <CircularProgress size={20} /> : <EventAvailable />}
                                    sx={{
                                        background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                                        color: 'white',
                                        px: 4,
                                        py: 1.5,
                                        fontSize: '1.1rem',
                                        fontWeight: 600,
                                        boxShadow: '0 4px 14px 0 rgba(16, 185, 129, 0.3)',
                                        '&:hover': {
                                            background: 'linear-gradient(135deg, #059669 0%, #047857 100%)',
                                            boxShadow: '0 6px 20px 0 rgba(16, 185, 129, 0.4)',
                                        },
                                        '&:disabled': {
                                            background: 'linear-gradient(135deg, #94a3b8 0%, #64748b 100%)',
                                            boxShadow: 'none',
                                        },
                                    }}
                                >
                                    {isSummarizing ? 'Processing Meeting...' : 'End Meeting & Generate Summary'}
                                </Button>
                            </Box>
                        </Fade>
                    )}
                </>
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
