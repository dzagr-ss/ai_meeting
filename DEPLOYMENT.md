# Deployment Guide for Meeting Transcription System

## Overview
This guide provides step-by-step instructions for deploying the Meeting Transcription System to Railway (backend) and Vercel (frontend).

## System Architecture
- **Backend**: FastAPI with ultra-minimal dependencies (366MB Docker image)
- **Frontend**: React with Material-UI and Redux Toolkit
- **Database**: PostgreSQL on Railway
- **Storage**: File uploads via backend API

## Prerequisites
- Railway account
- Vercel account
- GitHub repository for your code
- OpenAI API key
- Google Generative AI API key

## Production Optimizations Applied
- **Ultra-minimal Docker image**: Reduced from 6.8GB to 366MB
- **CPU-only dependencies**: No heavy ML libraries
- **Simplified speaker identification**: Basic logic instead of pyannote.audio
- **OpenAI API integration**: For transcription instead of local WhisperX
- **Environment-aware code**: Gracefully handles missing dependencies

## Backend Deployment (Railway)

### 1. Prepare the Backend

The backend has been optimized with minimal dependencies in `backend/requirements-railway.txt`:

```bash
# Core dependencies only - no heavy ML libraries
fastapi==0.104.1
uvicorn==0.24.0
python-multipart==0.0.6
pydantic==2.5.2
sqlalchemy==2.0.23
psycopg2-binary==2.9.10
openai==1.3.5
google-generativeai
# ... other minimal dependencies
```

### 2. Deploy to Railway

1. **Connect GitHub Repository**:
   - Go to [railway.app](https://railway.app)
   - Click "Start a New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

2. **Configure PostgreSQL Database**:
   ```bash
   # Railway will automatically provide DATABASE_URL
   # No manual setup required
   ```

3. **Set Environment Variables** in Railway dashboard:
   ```
   ENVIRONMENT=production
   DATABASE_URL=<automatically provided by Railway>
   SECRET_KEY=<generate a secure random string>
   OPENAI_API_KEY=<your OpenAI API key>
   GOOGLE_API_KEY=<your Google Generative AI key>
   STORAGE_PATH=/app/storage
   PYTHONUNBUFFERED=1
   PYTHONDONTWRITEBYTECODE=1
   ```

4. **Deploy**:
   - Railway will automatically detect the `railway.toml` configuration
   - Uses the optimized `backend/Dockerfile`
   - Build should complete in under 5 minutes with 366MB image

### 3. Verify Backend Deployment

1. **Check Health Endpoint**:
   ```bash
   curl https://your-railway-domain.railway.app/
   ```

2. **Test API Documentation**:
   ```
   https://your-railway-domain.railway.app/docs
   ```

## Frontend Deployment (Vercel)

### 1. Prepare Frontend Environment

1. **Create `frontend/.env.production`**:
   ```
   VITE_API_URL=https://your-railway-domain.railway.app
   VITE_ENVIRONMENT=production
   ```

### 2. Deploy to Vercel

1. **Connect Repository**:
   - Go to [vercel.com](https://vercel.com)
   - Click "New Project"
   - Import your GitHub repository

2. **Configure Build Settings**:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

3. **Set Environment Variables**:
   ```
   VITE_API_URL=https://your-railway-domain.railway.app
   VITE_ENVIRONMENT=production
   ```

4. **Deploy**:
   - Vercel will automatically build and deploy
   - Takes approximately 2-3 minutes

### 3. Verify Frontend Deployment

1. **Check Application**:
   - Visit your Vercel domain
   - Test login/registration
   - Upload a small audio file

## Automated Deployment Scripts

### Quick Deploy Script
```bash
# Run from project root
./deploy-to-railway.sh
```

### Local Development Setup
```bash
# Run from project root
./setup-local-env.sh
```

## Production Features

### Audio Processing
- **Transcription**: OpenAI Whisper API (cloud-based)
- **Speaker Identification**: Simplified algorithm (no heavy ML)
- **File Formats**: MP3, WAV, M4A via pydub
- **Storage**: Local file system with configurable path

### Authentication
- **JWT-based authentication**
- **Secure password hashing with bcrypt**
- **Session management**

### Database
- **PostgreSQL with SQLAlchemy ORM**
- **Alembic migrations**
- **Connection pooling**

## Monitoring and Maintenance

### Health Checks
- Backend: `GET /` endpoint
- Automatic Railway health monitoring
- 30-second intervals with 5-second startup grace period

### Logs
```bash
# View Railway logs
railway logs --follow

# View local logs
tail -f backend/app.log
```

### Database Management
```bash
# Run migrations (if needed)
railway run alembic upgrade head

# Access database console
railway connect <database-service-name>
```

## Troubleshooting

### Common Issues

1. **Build Timeout (Exit Code 137)**
   - **Solution**: Use the optimized `backend/requirements-railway.txt` file
   - Avoid heavy ML libraries like pytorch-lightning, pyannote.audio

2. **Import Errors in Production**
   - **Solution**: Code includes graceful fallbacks for missing dependencies
   - Check `backend/config.py` environment detection

3. **File Upload Issues**
   - **Solution**: Ensure `STORAGE_PATH` environment variable is set
   - Check directory permissions in container

4. **Database Connection Errors**
   - **Solution**: Verify `DATABASE_URL` is correctly set by Railway
   - Check PostgreSQL service status in Railway dashboard

### Performance Optimization

1. **Backend Performance**:
   - Single worker configuration for Railway's memory limits
   - Async FastAPI endpoints
   - Connection pooling

2. **Frontend Performance**:
   - Code splitting with React lazy loading
   - Optimized build with Vite
   - Static asset optimization

## Cost Estimation

### Railway (Backend + Database)
- **Hobby Plan**: $5/month + usage
- **Pro Plan**: $20/month + usage
- **Database**: Included in plan

### Vercel (Frontend)
- **Hobby Plan**: Free for personal projects
- **Pro Plan**: $20/month for teams

### External APIs
- **OpenAI**: ~$0.006 per minute of audio
- **Google Generative AI**: Free tier available

## Security Considerations

1. **Environment Variables**: Never commit API keys to repository
2. **CORS**: Properly configured for frontend domain
3. **Authentication**: JWT tokens with secure secrets
4. **File Uploads**: Size limits and type validation
5. **Rate Limiting**: Implemented via slowapi

## Scaling Considerations

1. **Backend Scaling**: Railway auto-scales based on traffic
2. **Database**: PostgreSQL can handle moderate loads
3. **File Storage**: Consider cloud storage (S3, GCS) for production scale
4. **CDN**: Vercel provides global CDN for frontend

## Support

For deployment issues:
1. Check Railway/Vercel logs first
2. Verify environment variables
3. Test API endpoints individually
4. Review this deployment guide

Last updated: December 2024 