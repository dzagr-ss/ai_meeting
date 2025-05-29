# WhisperX Troubleshooting Guide

## Issue: `module 'whisperx' has no attribute 'DiarizationPipeline'`

This error occurs due to changes in WhisperX's API structure in newer versions. The `DiarizationPipeline` class has been moved to a different module.

## Quick Fix

The code has been updated to handle both old and new WhisperX versions automatically. However, if you're still experiencing issues, follow these steps:

### 1. Run the Fix Script

```bash
# Make sure you're in your virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the fix script
python fix_whisperx.py
```

### 2. Manual Installation (Alternative)

If the script doesn't work, try manual installation:

```bash
# Uninstall existing WhisperX
pip uninstall whisperx -y

# Install specific version
pip install git+https://github.com/m-bain/whisperX.git@v3.1.1

# Or try the latest stable version
pip install whisperx==3.1.1
```

### 3. Environment Variables

Make sure you have these environment variables set in your `.env` file:

```bash
# Required for speaker diarization
HUGGINGFACE_TOKEN=your_hugging_face_token_here
# Alternative name (both work)
HF_TOKEN=your_hugging_face_token_here

# Optional WhisperX configuration
WHISPERX_DEVICE=cuda  # or 'cpu' if no GPU
WHISPERX_BATCH_SIZE=16
WHISPERX_COMPUTE_TYPE=float32  # or 'float16', 'int8'
WHISPERX_MODEL_SIZE=base  # or 'small', 'medium', 'large'
```

### 4. Hugging Face Model Access

You need to accept the user agreements for these models:

1. Visit https://hf.co/pyannote/speaker-diarization-3.1 and accept conditions
2. Visit https://hf.co/pyannote/segmentation and accept conditions
3. Create a token at https://hf.co/settings/tokens (read access is sufficient)

### 5. Test Your Installation

```python
import whisperx

# Test basic import
print("WhisperX imported successfully")

# Test DiarizationPipeline
try:
    # Try newer import path
    diarize_model = whisperx.diarize.DiarizationPipeline(
        use_auth_token="your_token", 
        device="cpu"
    )
    print("✅ DiarizationPipeline works with whisperx.diarize")
except AttributeError:
    try:
        # Try older import path
        diarize_model = whisperx.DiarizationPipeline(
            use_auth_token="your_token", 
            device="cpu"
        )
        print("✅ DiarizationPipeline works with whisperx")
    except Exception as e:
        print(f"❌ DiarizationPipeline failed: {e}")
```

## Common Issues and Solutions

### Issue: CUDA Out of Memory

**Solution**: Reduce batch sizes in your environment variables:

```bash
WHISPERX_BATCH_SIZE=4
WHISPERX_COMPUTE_TYPE=int8
```

### Issue: Slow Diarization Performance

**Solutions**:
1. Use GPU instead of CPU: `WHISPERX_DEVICE=cuda`
2. Reduce batch size: `WHISPERX_BATCH_SIZE=4`
3. Use lower precision: `WHISPERX_COMPUTE_TYPE=int8`

### Issue: PyTorch Version Conflicts

**Solution**: Install compatible PyTorch version:

```bash
# For CUDA 11.8
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

# For CPU only
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### Issue: Missing Dependencies

**Solution**: Install all required dependencies:

```bash
pip install -r requirements.txt
```

## Code Changes Made

The backend code has been updated to automatically handle both old and new WhisperX versions:

```python
# Updated code in main.py
try:
    # Try the newer import path first
    diarize_model = whisperx.diarize.DiarizationPipeline(use_auth_token=hf_token, device=device)
except AttributeError:
    # Fallback to older import path
    diarize_model = whisperx.DiarizationPipeline(use_auth_token=hf_token, device=device)
```

## Performance Optimization Tips

1. **Use GPU**: Set `WHISPERX_DEVICE=cuda` if you have a compatible GPU
2. **Optimize Batch Size**: Start with 16, reduce if you get memory errors
3. **Use Appropriate Precision**: `int8` for speed, `float32` for accuracy
4. **Model Size**: Use `base` for speed, `large` for accuracy

## Getting Help

If you're still experiencing issues:

1. Check the logs for specific error messages
2. Verify your Hugging Face token has the right permissions
3. Make sure you've accepted the model user agreements
4. Try running the fix script again
5. Check the WhisperX GitHub repository for known issues

## Version Compatibility

- **WhisperX 3.1.1+**: Uses `whisperx.diarize.DiarizationPipeline`
- **WhisperX < 3.1.1**: Uses `whisperx.DiarizationPipeline`
- **PyTorch**: 2.0+ recommended
- **Python**: 3.8-3.11 supported 