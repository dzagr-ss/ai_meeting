# Development Guide

## Quick Start

### Option 1: Use the development script (Recommended)
```bash
./start-dev.sh
```
This will start both backend and frontend services automatically.

### Option 2: Manual startup

#### Start Backend
```bash
# Activate virtual environment
source venv/bin/activate

# Start backend server
cd backend
python main.py
```

#### Start Frontend (in a new terminal)
```bash
# From project root
cd frontend
npm start

# OR from project root using npm script
npm run start:frontend
```

### Option 3: Using root npm scripts
```bash
# Start frontend
npm start
# or
npm run start:frontend

# Start backend
npm run start:backend
```

## Services

- **Backend**: http://localhost:8000
  - API documentation: http://localhost:8000/docs
  - WebSocket endpoint: ws://localhost:8000/ws/meetings/{meeting_id}/stream

- **Frontend**: http://localhost:3000
  - React development server with hot reload

## Troubleshooting

### WebSocket Issues
If you encounter WebSocket errors like `'introspection'`, the backend has been updated with better error handling. Restart the backend service.

### npm start not working
Make sure you're in the correct directory:
- Run `npm start` from the project root (uses the new script)
- Or run `npm start` from the `frontend/` directory directly

### Virtual Environment Issues
```bash
# Recreate virtual environment if needed
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend Dependencies
```bash
cd frontend
npm install
```

## Development Workflow

1. Start the development environment: `./start-dev.sh`
2. Make changes to your code
3. Frontend will auto-reload on changes
4. Backend needs manual restart for changes
5. Press Ctrl+C to stop all services

## Environment Variables

Make sure you have a `.env` file in the project root with:
```
SECRET_KEY=your_secret_key
OPENAI_API_KEY=your_openai_key
HUGGINGFACE_TOKEN=your_hf_token
DATABASE_URL=your_database_url
``` 