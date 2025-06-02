#!/bin/bash
set -e

echo "=== Railway Deployment Debug Script ==="
echo "Python version: $(python --version)"
echo "Environment: $NODE_ENV"
echo "Working directory: $(pwd)"

echo -e "\n=== System Information ==="
echo "OS: $(uname -a)"
echo "Available packages:"
dpkg -l | grep -E "(libmagic|file)" || echo "No libmagic packages found"

echo -e "\n=== File command test ==="
which file || echo "file command not found"
file --version || echo "file command not working"

echo -e "\n=== Python magic test ==="
python test-libmagic.py || echo "LibMagic test failed"

echo -e "\n=== Comprehensive Application Test ==="
echo "Running comprehensive application startup test..."
if python test-app-startup.py; then
    echo "✅ All application tests passed"
else
    echo "❌ Application tests failed - check details above"
    echo "Attempting to continue with basic startup anyway..."
fi

echo -e "\n=== Directory contents ==="
ls -la

echo -e "\n=== Environment Variables ==="
env | grep -E "(PATH|LD_LIBRARY_PATH|PYTHONPATH|DATABASE|SECRET)" || echo "No relevant env vars found"

echo -e "\n=== Starting application with verbose logging ==="
echo "Starting uvicorn with detailed error reporting..."

# Try to start with Python directly first for better error reporting
python -c "
import uvicorn
import sys
import traceback
import os

try:
    print('Configuring uvicorn server...')
    
    # Get port from environment
    port = int(os.environ.get('PORT', 8000))
    print(f'Port: {port}')
    
    # Start the server with comprehensive logging
    print('Starting uvicorn server...')
    uvicorn.run(
        'main:app', 
        host='0.0.0.0', 
        port=port, 
        log_level='info',
        access_log=True,
        timeout_keep_alive=30
    )
except KeyboardInterrupt:
    print('Server shutdown requested')
    sys.exit(0)
except Exception as e:
    print('❌ Uvicorn startup failed:')
    print(f'Error type: {type(e).__name__}')
    print(f'Error message: {str(e)}')
    print('Full traceback:')
    traceback.print_exc()
    sys.exit(1)
" 