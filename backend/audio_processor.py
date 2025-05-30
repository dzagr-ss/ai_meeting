import numpy as np
import soundfile as sf
import io
from typing import Generator, Optional, Tuple, List, AsyncGenerator
import torch
import torchaudio
from datetime import datetime
import asyncio
from queue import Queue
import threading
import tempfile
import os
import warnings
from config import settings

# Suppress specific warnings
warnings.filterwarnings("ignore", category=UserWarning, module="torchaudio")
warnings.filterwarnings("ignore", category=UserWarning, module="speechbrain")
warnings.filterwarnings("ignore", category=UserWarning, module="pyannote.audio")
warnings.filterwarnings("ignore", category=UserWarning, module="pytorch_lightning")

class AudioChunker:
    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_duration: float = 5.0,
        silence_threshold: float = 0.01,
        silence_duration: float = 2.0,
        min_chunk_duration: float = 1.0
    ):
        """Initialize the audio chunker.
        
        Args:
            sample_rate (int): Audio sample rate
            chunk_duration (float): Maximum duration of a chunk in seconds
            silence_threshold (float): Threshold for silence detection
            silence_duration (float): Duration of silence to trigger chunk split
            min_chunk_duration (float): Minimum duration of a chunk in seconds
        """
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration
        self.min_chunk_duration = min_chunk_duration
        self.buffer = np.array([], dtype=np.float32)
        self.temp_dir = tempfile.mkdtemp()
        self.processed_chunk_yield_count = 0 # Counter for chunks yielded
        
    def get_queued_chunk_count(self) -> int:
        """Get the number of full chunks currently in the buffer."""
        if self.sample_rate * self.chunk_duration == 0:
            return 0
        return len(self.buffer) // int(self.sample_rate * self.chunk_duration)
    
    def is_silence(self, audio_chunk: np.ndarray) -> bool:
        """Check if the audio chunk is silence."""
        return np.max(np.abs(audio_chunk)) < self.silence_threshold
    
    def save_chunk(self, audio_data: np.ndarray, start_time: float, end_time: float) -> str:
        """Save audio chunk to a temporary file."""
        try:
            # Ensure audio data is in the correct format
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
                
            # Normalize audio if needed
            if np.max(np.abs(audio_data)) > 1.0:
                audio_data = audio_data / np.max(np.abs(audio_data))
                
            # Create temporary file
            chunk_file = os.path.join(self.temp_dir, f"chunk_{start_time:.2f}_{end_time:.2f}.wav")
            
            # Convert to torch tensor for better compatibility
            audio_tensor = torch.from_numpy(audio_data).unsqueeze(0)  # Add channel dimension
            torchaudio.save(chunk_file, audio_tensor, self.sample_rate)
            
            return chunk_file
        except Exception as e:
            if settings.SHOW_BACKEND_LOGS:
                print(f"Error saving chunk: {str(e)}")
            # Fallback to soundfile if torchaudio fails
            chunk_file = os.path.join(self.temp_dir, f"chunk_{start_time:.2f}_{end_time:.2f}.wav")
            sf.write(chunk_file, audio_data, self.sample_rate)
            return chunk_file
    
    async def process_audio_stream(self, audio_chunks: List[np.ndarray]) -> AsyncGenerator[Tuple[np.ndarray, float, float], None]:
        """Process audio stream and yield chunks based on silence and duration."""
        try:
            for chunk in audio_chunks:
                # Add chunk to buffer
                buffer_size_before = len(self.buffer)
                if settings.SHOW_BACKEND_LOGS:
                    print(f"[AudioChunker] Buffer size before append: {buffer_size_before}")
                self.buffer = np.append(self.buffer, chunk)
                buffer_size_after_append = len(self.buffer)
                if settings.SHOW_BACKEND_LOGS:
                    print(f"[AudioChunker] Buffer size after append: {buffer_size_after_append}")
                
                # Process buffer while it's long enough
                while len(self.buffer) >= self.sample_rate * self.chunk_duration:
                    chunk_size = int(self.sample_rate * self.chunk_duration)
                    current_chunk = self.buffer[:chunk_size]
                    self.buffer = self.buffer[chunk_size:]
                    buffer_size_after_trim = len(self.buffer)
                    if settings.SHOW_BACKEND_LOGS:
                        print(f"[AudioChunker] Trimmed buffer. Size after trim: {buffer_size_after_trim}")
                    
                    # Calculate timestamps
                    start_time = buffer_size_after_trim / self.sample_rate
                    end_time = start_time + len(current_chunk) / self.sample_rate
                    if settings.SHOW_BACKEND_LOGS:
                        print(f"[AudioChunker] Yielding chunk: start={start_time:.2f}s, end={end_time:.2f}s, chunk_size={len(current_chunk)}")
                    
                    # Check for silence
                    if self.is_silence(current_chunk):
                        if settings.SHOW_BACKEND_LOGS:
                            print(f"[AudioChunker] Chunk is silence. Skipping.")
                        continue
                        
                    self.processed_chunk_yield_count += 1 # Increment count before yielding
                    yield current_chunk, start_time, end_time
        except Exception as e:
            
            print(f"[AudioChunker] Error processing audio stream: {str(e)}")
            raise
                
    def get_processed_chunk_yield_count(self) -> int:
        """Get the total number of processed chunks yielded."""
        return self.processed_chunk_yield_count

    def cleanup(self):
        """Clean up temporary files."""
        try:
            for file in os.listdir(self.temp_dir):
                os.remove(os.path.join(self.temp_dir, file))
            os.rmdir(self.temp_dir)
        except Exception as e:
            print(f"Error cleaning up temporary files: {str(e)}") 