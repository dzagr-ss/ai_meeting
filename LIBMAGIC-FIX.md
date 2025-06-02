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

**Subsequent Issues:**
- Incomplete error tracebacks making diagnosis difficult
- Missing essential Python dependencies
- No comprehensive startup testing

These errors occur because:
1. The `python-magic` library requires the system library `libmagic` to be installed
2. Essential Python dependencies required by FastAPI/Starlette were missing from the minimal requirements file
3. Railway's minimal environment may lack certain packages that work locally

## Solution

### 1. Updated Dockerfile
- Added `libmagic-dev` and `file` packages to the system dependencies
- Added `build-essential` for compilation support
- Added comprehensive test script execution during build to verify installation
- Added build-time import testing to catch issues early

### 2. Modified main.py
- Changed from immediate import to lazy loading of the `magic` module
- Added `get_magic_module()` function that handles import errors gracefully
- Updated `validate_file_content()` to use the lazy loading approach

### 3. Enhanced requirements-railway.txt
- Added missing `itsdangerous` dependency (required by Starlette sessions)
- Added essential dependencies: `starlette`, `typing-extensions`, `click`, `h11`, `anyio`
- Added performance dependencies: `ujson`, `httptools`
- Added utility dependencies: `sniffio`, `idna`, `python-dateutil`
- Pinned all versions for consistency

### 4. Comprehensive Debugging Tools
- `test-libmagic.py`: LibMagic functionality testing
- `test-app-startup.py`: **NEW** - Comprehensive application import and configuration testing
- `start-with-debug.sh`: Enhanced startup script with detailed diagnostics
- `deploy-libmagic-fix.sh`: Deployment helper script

### 5. Advanced Error Isolation
- Build-time testing to catch import issues early
- Runtime comprehensive testing before starting uvicorn
- Detailed error reporting with full tracebacks
- Graceful degradation when possible

## Files Modified

1. **Dockerfile**: Added system dependencies, build-time testing, and comprehensive scripts
2. **backend/main.py**: Implemented lazy loading for magic module
3. **requirements-railway.txt**: Added comprehensive dependency list with pinned versions
4. **test-libmagic.py**: LibMagic testing script
5. **test-app-startup.py**: **NEW** - Comprehensive application testing script
6. **start-with-debug.sh**: Enhanced debug startup script with comprehensive testing

## New Comprehensive Testing

The `test-app-startup.py` script performs comprehensive testing:

1. **Basic Python Imports**: Core Python modules
2. **Web Framework Imports**: FastAPI, Uvicorn, Starlette, Pydantic
3. **Database Imports**: SQLAlchemy, Psycopg2, Alembic
4. **File System Access**: Write permissions, directory access
5. **Environment Configuration**: Required environment variables
6. **Application Imports**: Custom modules (config, database, models, etc.)
7. **Main Module Testing**: FastAPI app instantiation

## Fallback Mechanism

If components still fail to load, the application will:
1. Log detailed error information with full tracebacks
2. Use Python's `mimetypes` module as a fallback for file type detection
3. Continue startup where possible with graceful degradation
4. Provide comprehensive diagnostic information for troubleshooting

## Testing

### Local Testing:
```bash
docker build -t stocks-agent-test .
docker run -p 8000:8000 stocks-agent-test
```

### Manual Testing:
```bash
# Test libmagic
python test-libmagic.py

# Test comprehensive application startup
python test-app-startup.py
```

## Deployment

1. Run the deployment script:
   ```bash
   ./deploy-libmagic-fix.sh
   ```

2. Commit and push changes:
   ```bash
   git add .
   git commit -m "Fix libmagic and missing dependencies with comprehensive testing"
   git push
   ```

3. Check Railway logs for detailed diagnostic information

## Rollback

If needed, rollback with:
```bash
./rollback-libmagic-fix.sh
```

## Expected Railway Log Output

After deployment, you should see comprehensive diagnostics:

### Build Phase:
- System package installation status
- LibMagic test results
- Basic import testing results

### Runtime Phase:
- Comprehensive application testing results
- Detailed dependency status
- Configuration validation
- Environment variable status
- File system access verification
- Full error tracebacks if issues occur

## Dependencies Added

### Essential Runtime Dependencies:
- `itsdangerous==2.1.2` - Required by Starlette for session management
- `starlette==0.27.0` - Web framework (FastAPI dependency)
- `typing-extensions==4.8.0` - Type hints support
- `click==8.1.7` - Command line interface (Uvicorn dependency)
- `h11==0.14.0` - HTTP/1.1 protocol (Uvicorn dependency)
- `anyio==3.7.1` - Async I/O support
- `sniffio==1.3.0` - Async library detection
- `idna==3.4` - International domain name support

### Performance Dependencies:
- `ujson==5.8.0` - Fast JSON parsing
- `httptools==0.6.0` - Fast HTTP parsing
- `python-dateutil==2.8.2` - Enhanced date handling

### System Dependencies:
- `libmagic1` - Core magic library
- `libmagic-dev` - Development headers
- `file` - File type detection utility
- `build-essential` - Compilation tools

## Troubleshooting

If the application still fails to start after these fixes:

1. **Check Build Logs**: Look for build-time test failures
2. **Check Runtime Logs**: Review comprehensive test results
3. **Identify Failed Tests**: Focus on specific failing components
4. **Environment Issues**: Verify Railway environment variables
5. **Database Issues**: Check DATABASE_URL configuration

## Related Issues

- **Primary Issue**: Railway deployment failing with libmagic ImportError
- **Secondary Issue**: Missing essential Python dependencies (itsdangerous, etc.)
- **Tertiary Issue**: Incomplete error reporting making diagnosis difficult
- **Root Cause**: Incomplete dependency specification and insufficient error handling
- **Solution**: Comprehensive dependency management, extensive testing, and detailed error reporting 