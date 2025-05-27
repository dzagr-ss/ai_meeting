# Meeting Transcription App

A comprehensive AI-powered meeting assistant that provides real-time transcription, intelligent summaries, and actionable insights from your meetings.

## Features

- Allows microphone selection from the system's list of available input devices
- Real-time audio capture from system's microphone
- Live speech-to-text transcription
- Speaker diarization (speaker separation)
- AI-powered meeting summaries
- Action item extraction
- Meeting insights and analytics
- Integration with video conferencing platforms
- Meeting history and search
- Collaborative features
- Export capabilities (PDF, DOCX)
- User authentication and management

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
6. Access AI-generated summaries and action items
7. Export or share meeting notes as needed

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