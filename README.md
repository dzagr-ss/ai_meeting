# Stocks Agent - Meeting Transcription System

A comprehensive meeting transcription and analysis system with real-time audio processing, speaker identification, and AI-powered summaries.

## Features

- Real-time audio transcription using OpenAI Whisper
- Speaker identification and diarization
- AI-powered meeting summaries using Google Gemini
- User authentication and meeting management
- File storage organized by user and meeting

## File Storage Structure

The system now organizes meeting audio files by username to improve organization and security:

### New Structure (v2.0+)
```
/tmp/meetings/
├── user_at_example_com/
│   ├── 1/
│   │   ├── meeting_1_20240101_120000.wav
│   │   └── meeting_1_20240101_130000.wav
│   └── 2/
│       └── meeting_2_20240102_140000.wav
└── another_user_at_domain_com/
    └── 3/
        └── meeting_3_20240103_150000.wav
```

### Legacy Structure (v1.0)
```
/tmp/
├── meeting_1_20240101_120000.wav
├── meeting_1_20240101_130000.wav
└── meeting_2_20240102_140000.wav
```

### Migration

The system automatically migrates files from the legacy structure when they are accessed. You can also manually trigger migration using the admin endpoint:

```bash
POST /admin/migrate-files
```

### File Organization Benefits

1. **User Isolation**: Each user's files are stored in separate directories
2. **Meeting Organization**: Files are grouped by meeting ID within user directories
3. **Security**: Users can only access their own meeting files
4. **Scalability**: Better organization for systems with many users and meetings

## API Endpoints

### File Management
- `GET /admin/file-structure` - View current file organization (admin)
- `POST /admin/migrate-files` - Migrate legacy files to new structure (admin)

### Meeting Management
- `POST /meetings/` - Create a new meeting
- `GET /meetings/` - List user's meetings
- `GET /meetings/{id}/transcriptions` - Get meeting transcriptions
- `POST /meetings/{id}/transcribe` - Upload audio for transcription
- `POST /meetings/{id}/refine-speakers` - Refine speaker diarization using all audio files (automatically refreshes UI)

### Authentication
- `POST /token` - Login and get access token
- `POST /users/` - Register new user

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export OPENAI_API_KEY="your-openai-key"
export GEMINI_API_KEY="your-gemini-key"
export SECRET_KEY="your-secret-key"
```

3. Run the backend:
```bash
cd backend
python main.py
```

4. Run the frontend:
```bash
cd frontend
npm install
npm start
```

## Development

The system uses:
- **Backend**: FastAPI, SQLAlchemy, OpenAI Whisper, Google Gemini
- **Frontend**: React, TypeScript, Material-UI
- **Database**: PostgreSQL (configurable)
- **Audio Processing**: PyAudio, NumPy, SciPy

## File Storage Configuration

By default, files are stored in `/tmp/meetings/`. In production, consider:

1. Using a persistent storage location (not `/tmp/`)
2. Implementing file cleanup policies
3. Adding file size limits
4. Using cloud storage for scalability

## Security Considerations

- Files are organized by user email (sanitized for filesystem)
- Users can only access their own meeting files
- Authentication required for all file operations
- Admin endpoints should be restricted in production

## Project Structure

```
meeting-transcription/
├── frontend/           # React frontend application
├── backend/           # Python FastAPI backend
├── database/          # Database migrations and schemas
├── storage/          # Audio file storage
└── README.md
```

## Setup Instructions

### Backend Setup

1. Create a Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

3. Set up the database:
```bash
alembic upgrade head
```

4. Start the backend server:
```bash
uvicorn main:app --reload
```

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start the development server:
```bash
npm start
```

## Environment Variables

Create a `.env` file in the backend directory with the following variables:
```
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=your_database_url
STORAGE_PATH=your_storage_path
JWT_SECRET=your_jwt_secret
```

## Usage

1. Open your browser and navigate to `http://localhost:3000`
2. Sign in or create an account
3. Start or join a meeting
4. Click "Start Recording" to begin capturing audio
5. View real-time transcription with speaker separation
6. Speaker labels are automatically refined after recording stops
7. Access AI-generated summaries and action items
8. Export or share meeting notes as needed

## Technologies Used

- Frontend:
  - React with TypeScript
  - Material-UI for components
  - WebSocket for real-time updates
  - Redux for state management
  - React Query for data fetching

- Backend:
  - Python FastAPI
  - SQLAlchemy for database ORM
  - Alembic for migrations
  - Whisper API for transcription
  - Pyannote.audio for speaker diarization
  - OpenAI API for summaries and insights
  - JWT for authentication

- Infrastructure:
  - PostgreSQL for database
  - Redis for caching
  - MinIO for file storage
  - Docker for containerization

## API Integration

The application supports integration with:
- Google Calendar


## Contributing

Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE.md file for details 