# LibMagic & Dependencies Fix for Railway Deployment

## Problem
The backend was failing to start on Railway with multiple errors:

**Initial Error:**
```
ImportError: failed to find libmagic. Check your installation
```

**Secondary Error (after libmagic fix):**
```
ModuleNotFoundError: No module named 'itsdangerous'
```

These errors occur because:
1. The `python-magic` library requires the system library `libmagic` to be installed
2. Essential Python dependencies required by FastAPI/Starlette were missing from the minimal requirements file

## Solution

### 1. Updated Dockerfile
- Added `libmagic-dev` and `file` packages to the system dependencies
- Added `build-essential` for compilation support
- Added test script execution during build to verify installation

### 2. Modified main.py
- Changed from immediate import to lazy loading of the `magic` module
- Added `get_magic_module()` function that handles import errors gracefully
- Updated `validate_file_content()` to use the lazy loading approach

### 3. Fixed requirements-railway.txt
- Added missing `itsdangerous` dependency (required by Starlette sessions)
- Added other essential dependencies: `starlette`, `typing-extensions`, `click`, `h11`, `anyio`
- Pinned python-magic version for consistency

### 4. Added Debugging Tools
- `test-libmagic.py`: Comprehensive test script to verify libmagic functionality
- `start-with-debug.sh`: Startup script with detailed system and Python environment logging
- `deploy-libmagic-fix.sh`: Deployment helper script

## Files Modified

1. **Dockerfile**: Added system dependencies and test execution
2. **backend/main.py**: Implemented lazy loading for magic module
3. **requirements-railway.txt**: Added missing dependencies and pinned versions
4. **test-libmagic.py**: New - libmagic testing script
5. **start-with-debug.sh**: New - enhanced debug startup script

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
   git commit -m "Fix libmagic and missing dependencies for Railway deployment"
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
- Python dependencies status (FastAPI, Starlette, itsdangerous, etc.)
- "python-magic library loaded successfully" or fallback messages
- Normal application startup

## Dependencies Added

### Essential Runtime Dependencies:
- `itsdangerous==2.1.2` - Required by Starlette for session management
- `starlette==0.27.0` - Web framework (FastAPI dependency)
- `typing-extensions==4.8.0` - Type hints support
- `click==8.1.7` - Command line interface (Uvicorn dependency)
- `h11==0.14.0` - HTTP/1.1 protocol (Uvicorn dependency)
- `anyio==3.7.1` - Async I/O support

### System Dependencies:
- `libmagic1` - Core magic library
- `libmagic-dev` - Development headers
- `file` - File type detection utility
- `build-essential` - Compilation tools

## Related Issues

- **Primary Issue**: Railway deployment failing with libmagic ImportError
- **Secondary Issue**: Missing essential Python dependencies (itsdangerous, etc.)
- **Root Cause**: Incomplete dependency specification in minimal requirements file
- **Solution**: Install required system packages and add missing Python dependencies 