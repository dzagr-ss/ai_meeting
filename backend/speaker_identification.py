import os
from typing import List, Dict, Any, Union
from pyannote.audio import Pipeline
import whisper
import torch
import torchaudio # Keep torchaudio for potential audio manipulation if needed
from datetime import datetime
import numpy as np # Ensure numpy is imported
from config import settings

class SpeakerIdentifier:
    def __init__(self, hf_token: str):
        """Initialize the speaker identification system.
        
        Args:
            hf_token (str): Hugging Face token for accessing Pyannote.audio and Whisper (if needed)
        """
        self.hf_token = hf_token
        # Initialize the pyannote speaker diarization pipeline (version 3.1)
        self.pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1", # Use version 3.1
            use_auth_token=self.hf_token
        )
        # Initialize Whisper with English model
        self.whisper_model = whisper.load_model("base.en")
        
        # Move models to GPU if available
        if torch.cuda.is_available():
            self.pipeline = self.pipeline.to(torch.device("cuda"))
            self.whisper_model = self.whisper_model.to(torch.device("cuda"))

        self.audio_buffer = np.array([], dtype=np.float32)
        self.buffer_start_time = 0.0
        self.transcription_segments = [] # Store segments with text and speaker labels
        self.sample_rate = 16000 # Assume a fixed sample rate

        # Define a processing interval (e.g., process accumulated audio every X seconds)
        self.processing_interval_duration = 2.0 # seconds - Reduced interval for faster processing
        self.last_process_time = 0.0

    @staticmethod
    def process_single_chunk(
        audio_chunk: np.ndarray,
        chunk_absolute_start_time: float,
        pipeline: Pipeline,
        whisper_model: whisper.Whisper,
        sample_rate: int
    ) -> List[Dict[str, Any]]:
        """Process a single raw audio chunk with diarization and transcription.
        Designed to be called by a worker process.
        
        Args:
            audio_chunk (np.ndarray): Raw audio chunk as a numpy array (float32).
            chunk_absolute_start_time (float): Absolute start time of this chunk in the stream.
            pipeline (Pipeline): Initialized Pyannote pipeline.
            whisper_model (whisper.Whisper): Initialized Whisper model.
            sample_rate (int): Audio sample rate.
            
        Returns:
            List[Dict[str, Any]]: List of new transcription segments with speaker info, with absolute timestamps.
        """
        new_segments = []

        if len(audio_chunk) == 0:
            return new_segments

        try:
            # --- Process the chunk with the Pyannote pipeline ---
            # The pipeline takes a dictionary {'waveform': ..., 'sample_rate': ...}
            waveform = torch.from_numpy(audio_chunk).unsqueeze(0) # Add batch dimension
            audio_info = {'waveform': waveform, 'sample_rate': sample_rate}

            diarization_result = pipeline(audio_info)

            # --- Process diarization and transcription ---
            transcription_result = whisper_model.transcribe(
                audio_chunk,
                language="en",  # Always use English
                task="transcribe"
            )

            # Combine diarization and transcription results
            for transcribed_segment in transcription_result["segments"]:
                # Calculate absolute timestamps for the transcribed segment
                abs_start_time = chunk_absolute_start_time + transcribed_segment["start"]
                abs_end_time = chunk_absolute_start_time + transcribed_segment["end"]
                segment_text = transcribed_segment["text"].strip()

                # Find overlapping speaker in diarization result (relative to chunk start)
                assigned_speaker = "unknown"
                transcribed_mid_time_relative_to_chunk = (transcribed_segment["start"] + transcribed_segment["end"]) / 2.0

                for diarization_segment, _, speaker in diarization_result.itertracks(yield_label=True):
                     if diarization_segment.start <= transcribed_mid_time_relative_to_chunk < diarization_segment.end:
                          assigned_speaker = speaker
                          break

                new_segments.append({
                    "speaker": assigned_speaker,
                    "start_time": abs_start_time,
                    "end_time": abs_end_time,
                    "text": segment_text
                })

        except Exception as e:
            if settings.SHOW_BACKEND_LOGS:
                print(f"Error processing single audio chunk with pipeline/whisper: {e}")
            # In a worker process, we might log and return empty or error segments
            return [] # Return empty list on error for this chunk

        return new_segments

    def get_buffer_duration_seconds(self) -> float:
        """Get the duration of audio currently in the internal buffer in seconds."""
        if self.sample_rate == 0:
            return 0.0
        return len(self.audio_buffer) / self.sample_rate

    def process_audio(self, audio_path: str) -> List[Dict[str, Any]]:
        """Process audio file to identify speakers and transcribe speech.
        
        Args:
            audio_path (str): Path to the audio file
            
        Returns:
            List[Dict[str, Any]]: List of segments with speaker and transcription info
        """
        # This method remains for processing full files
        if settings.SHOW_BACKEND_LOGS:
            print(f"Processing full audio file: {audio_path}")
        # Get speaker diarization
        diarization = self.pipeline(audio_path)
        
        # Get transcription with English language enforced
        transcription = self.whisper_model.transcribe(
            audio_path,
            language="en",  # Always use English
            task="transcribe"
        )
        
        # Process segments
        segments = []
        for segment, track, speaker in diarization.itertracks(yield_label=True):
            # Find corresponding text in transcription
            segment_text = self._get_text_for_time_segment(
                segment.start, 
                segment.end, 
                transcription
            )
            
            segments.append({
                "speaker": speaker,
                "start_time": segment.start,
                "end_time": segment.end,
                "text": segment_text
            })
            
        return segments
    
    def _get_text_for_time_segment(
        self, 
        start_time: float, 
        end_time: float, 
        transcription: Dict[str, Any]
    ) -> str:
        """Get text for a specific time segment from the transcription.
        
        Args:
            start_time (float): Start time in seconds
            end_time (float): End time in seconds
            transcription (Dict[str, Any]): Whisper transcription result
            
        Returns:
            str: Text for the specified time segment
        """
        segment_text = []
        
        for segment in transcription["segments"]:
            # Check for overlap between transcription segment and target time segment
            if (max(segment["start"], start_time) < min(segment["end"], end_time)):
                 segment_text.append(segment["text"])
                
        return " ".join(segment_text)

    def process_audio_chunk(self, audio_chunk: np.ndarray, chunk_start_time: float):
        """
        Process a chunk of audio data for speaker identification and transcription.
        """
        return self.process_single_chunk(
            audio_chunk,
            chunk_start_time,
            self.pipeline,
            self.whisper_model,
            self.sample_rate
        )

class FallbackSpeakerIdentifier:
    """Fallback speaker identifier that works without pyannote.audio models."""
    
    def __init__(self):
        """Initialize the fallback speaker identification system."""
        print("[FallbackSpeakerIdentifier] Using fallback speaker identifier (no diarization)")
        # Initialize only Whisper for transcription
        try:
            import whisper
            self.whisper_model = whisper.load_model("base.en")
            self.has_whisper = True
        except Exception as e:
            print(f"[FallbackSpeakerIdentifier] Could not load Whisper model: {e}")
            self.whisper_model = None
            self.has_whisper = False
        
        self.audio_buffer = np.array([], dtype=np.float32)
        self.buffer_start_time = 0.0
        self.transcription_segments = []
        self.sample_rate = 16000
        self.processing_interval_duration = 2.0
        self.last_process_time = 0.0
        self.speaker_counter = 1  # Simple speaker counter for fallback

    def get_buffer_duration_seconds(self) -> float:
        """Get the duration of audio currently in the internal buffer in seconds."""
        if self.sample_rate == 0:
            return 0.0
        return len(self.audio_buffer) / self.sample_rate

    def process_audio(self, audio_path: str) -> List[Dict[str, Any]]:
        """Process audio file with fallback method (no speaker diarization)."""
        print(f"[FallbackSpeakerIdentifier] Processing audio file: {audio_path}")
        
        if not self.has_whisper:
            return [{
                "speaker": "Speaker_1",
                "start_time": 0.0,
                "end_time": 10.0,
                "text": "Audio processed (transcription unavailable)"
            }]
        
        try:
            # Get transcription only (no diarization)
            transcription = self.whisper_model.transcribe(
                audio_path,
                language="en",  # Always use English
                task="transcribe"
            )
            
            # Process segments with simple speaker assignment
            segments = []
            for i, segment in enumerate(transcription.get("segments", [])):
                # Assign speakers in a round-robin fashion
                speaker_id = f"Speaker_{(i % 3) + 1}"  # Cycle through Speaker_1, Speaker_2, Speaker_3
                
                segments.append({
                    "speaker": speaker_id,
                    "start_time": segment.get("start", 0.0),
                    "end_time": segment.get("end", 0.0),
                    "text": segment.get("text", "").strip()
                })
            
            return segments
            
        except Exception as e:
            print(f"[FallbackSpeakerIdentifier] Error processing audio: {e}")
            return [{
                "speaker": "Speaker_1",
                "start_time": 0.0,
                "end_time": 10.0,
                "text": f"Error processing audio: {str(e)}"
            }]

    def process_audio_chunk(self, audio_chunk: np.ndarray, chunk_start_time: float):
        """Process a chunk of audio data with fallback method."""
        if not self.has_whisper or len(audio_chunk) == 0:
            return []
        
        try:
            # Simple transcription without diarization
            transcription = self.whisper_model.transcribe(
                audio_chunk,
                language="en",  # Always use English
                task="transcribe"
            )
            
            segments = []
            for segment in transcription.get("segments", []):
                # Simple speaker assignment
                speaker_id = f"Speaker_{self.speaker_counter}"
                
                segments.append({
                    "speaker": speaker_id,
                    "start_time": chunk_start_time + segment.get("start", 0.0),
                    "end_time": chunk_start_time + segment.get("end", 0.0),
                    "text": segment.get("text", "").strip()
                })
                
                # Cycle through speakers
                self.speaker_counter = (self.speaker_counter % 3) + 1
            
            return segments
            
        except Exception as e:
            print(f"[FallbackSpeakerIdentifier] Error processing audio chunk: {e}")
            return []

def create_speaker_identifier() -> Union[SpeakerIdentifier, FallbackSpeakerIdentifier]:
    """Create a SpeakerIdentifier instance using the HF_TOKEN environment variable.
    
    Returns:
        Union[SpeakerIdentifier, FallbackSpeakerIdentifier]: Initialized speaker identifier
    """
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        print("[SpeakerIdentifier] HF_TOKEN not set, using fallback speaker identifier")
        return FallbackSpeakerIdentifier()
    
    try:
        print("[SpeakerIdentifier] Attempting to create full speaker identifier with pyannote.audio")
        return SpeakerIdentifier(hf_token)
    except Exception as e:
        print(f"[SpeakerIdentifier] Failed to create full speaker identifier: {e}")
        print("[SpeakerIdentifier] Falling back to simple transcription-only mode")
        return FallbackSpeakerIdentifier()

# Removed example usage
# async def process_realtime_audio(...) 