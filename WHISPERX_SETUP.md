# WhisperX Integration Setup

This project now uses WhisperX for enhanced speaker diarization and transcription of uploaded audio files.

## Features

- **Better Transcription**: More accurate transcription using WhisperX's improved models
- **Speaker Diarization**: Automatic identification and labeling of different speakers
- **Alignment**: Precise word-level timestamps
- **Fallback Support**: Automatically falls back to OpenAI Whisper if WhisperX fails

## Configuration

You can configure WhisperX behavior using environment variables in your `.env` file:

```bash
# Device configuration (cpu, cuda)
WHISPERX_DEVICE=cpu

# Model size (tiny, base, small, medium, large)
WHISPERX_MODEL_SIZE=base

# Batch size for processing (reduce if low on memory)
WHISPERX_BATCH_SIZE=16

# Compute type (float32, float16, int8)
WHISPERX_COMPUTE_TYPE=float32

# HuggingFace token for speaker diarization (optional but recommended)
HUGGINGFACE_TOKEN=your_hf_token_here
```

## Speaker Diarization Setup

For the best speaker diarization results, you need to:

1. **Accept pyannote model conditions**: Visit https://hf.co/pyannote/speaker-diarization-3.1 and accept the user conditions
2. **Get HuggingFace token**: 
   - Go to https://huggingface.co/settings/tokens
   - Create a new token with read permissions
   - Add it to your `.env` file as `HUGGINGFACE_TOKEN=your_token_here`

## GPU Support

If you have a CUDA-compatible GPU:

```bash
WHISPERX_DEVICE=cuda
WHISPERX_COMPUTE_TYPE=float16
WHISPERX_BATCH_SIZE=32
```

## Troubleshooting

### Common Issues

1. **"pyannote" errors**: You need to accept the model conditions and set your HuggingFace token
2. **Memory errors**: Reduce `WHISPERX_BATCH_SIZE` or use a smaller model size
3. **Slow processing**: Consider using GPU if available, or use a smaller model

### Fallback Behavior

If WhisperX fails for any reason, the system will automatically fall back to:
1. OpenAI Whisper for individual files
2. Basic speaker labeling (Speaker_1, Speaker_2, etc.)

## Model Sizes

- **tiny**: Fastest, least accurate
- **base**: Good balance (default)
- **small**: Better accuracy, slower
- **medium**: High accuracy, much slower
- **large**: Best accuracy, very slow

Choose based on your accuracy vs. speed requirements.

## Installation

WhisperX is automatically installed when you run:

```bash
pip install -r requirements.txt
```

The system will detect if WhisperX is available and use it automatically for uploaded audio files. 