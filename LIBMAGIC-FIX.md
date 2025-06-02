# LibMagic Fix for Railway Deployment

## Problem
The backend was failing to start on Railway with the error:
```
ImportError: failed to find libmagic. Check your installation
```

This error occurs because the `python-magic` library requires the system library `libmagic` to be installed, which was missing in the Railway deployment environment.

## Solution

### 1. Updated Dockerfile
- Added `libmagic-dev` and `file` packages to the system dependencies
- Added `build-essential` for compilation support
- Added test script execution during build to verify installation

### 2. Modified main.py
- Changed from immediate import to lazy loading of the `magic` module
- Added `get_magic_module()` function that handles import errors gracefully
- Updated `validate_file_content()` to use the lazy loading approach

### 3. Added Debugging Tools
- `test-libmagic.py`: Comprehensive test script to verify libmagic functionality
- `start-with-debug.sh`: Startup script with detailed system information logging
- `deploy-libmagic-fix.sh`: Deployment helper script

## Files Modified

1. **Dockerfile**: Added system dependencies and test execution
2. **backend/main.py**: Implemented lazy loading for magic module
3. **requirements-railway.txt**: Pinned python-magic version
4. **test-libmagic.py**: New - libmagic testing script
5. **start-with-debug.sh**: New - debug startup script

## Fallback Mechanism

If libmagic still fails to load, the application will:
1. Log the error and continue starting
2. Use Python's `mimetypes` module as a fallback for file type detection
3. Be more lenient with audio file validation

## Testing

To test the fix locally:
```bash
docker build -t stocks-agent-test .
docker run -p 8000:8000 stocks-agent-test
```

## Deployment

1. Run the deployment script:
   ```bash
   ./deploy-libmagic-fix.sh
   ```

2. Commit and push changes:
   ```bash
   git add .
   git commit -m "Fix libmagic import error in Railway deployment"
   git push
   ```

3. Check Railway logs for diagnostic information

## Rollback

If needed, rollback with:
```bash
./rollback-libmagic-fix.sh
```

## Expected Railway Log Output

After deployment, you should see in the logs:
- System package information
- LibMagic test results
- "python-magic library loaded successfully" or fallback messages
- Normal application startup

## Related Issues

- Issue: Railway deployment failing with libmagic ImportError
- Root cause: Missing system library dependencies
- Solution: Install required system packages and implement graceful fallback 