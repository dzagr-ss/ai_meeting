# Deployment Guide

This guide will help you deploy your Meeting Transcription System to Railway (backend) and Vercel (frontend).

## 🚀 Prerequisites

1. **GitHub Account** - Your code should be in a GitHub repository
2. **Railway Account** - Sign up at [railway.app](https://railway.app)
3. **Vercel Account** - Sign up at [vercel.com](https://vercel.com)
4. **API Keys**:
   - OpenAI API Key (starts with `sk-`)
   - Google Gemini API Key
   - SMTP credentials for email functionality

## ⚡ Quick Deployment (Recommended)

Run the automated deployment preparation script:
```bash
./deploy-to-railway.sh
```

This script will:
- Optimize Docker image for Railway's 4GB limit
- Test the build locally
- Provide step-by-step deployment instructions
- Check environment variables

## 📦 Backend Deployment (Railway)

### Step 1: Prepare Environment Variables

First, generate a secure secret key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 2: Image Size Optimization

**Important**: Railway has a 4GB image size limit. This app uses CPU-only PyTorch and lightweight dependencies to stay under this limit.

**Production Optimizations Applied**:
- ✅ CPU-only PyTorch (vs. CUDA version saves ~3GB)
- ✅ Removed heavy ML libraries (pyannote.audio, speechbrain, pytorch-lightning)
- ✅ Uses OpenAI API for transcription (more reliable than local models)
- ✅ Simplified speaker identification
- ✅ Multi-stage Docker build with cleanup

**Final image size**: ~2.5GB (well under Railway's 4GB limit)

### Step 3: Deploy to Railway

1. **Go to Railway Dashboard**
   - Visit [railway.app](https://railway.app) and sign in
   - Click "New Project"

2. **Connect GitHub Repository**
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Select the `main` branch

3. **Add PostgreSQL Database**
   - In your project dashboard, click "New Service"
   - Select "Database" → "PostgreSQL"
   - Railway will automatically create a database and provide connection details

4. **Configure Environment Variables**
   - Go to your backend service
   - Click on "Variables" tab
   - Add the following environment variables:

   ```bash
   # Required Variables
   DATABASE_URL=postgresql://username:password@host:port/database  # Auto-provided by Railway
   SECRET_KEY=your-generated-secret-key-from-step-1
   OPENAI_API_KEY=sk-your-openai-api-key
   GEMINI_API_KEY=your-google-gemini-api-key
   
   # Email Configuration
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   FROM_EMAIL=your-email@gmail.com
   
   # Production Settings
   ENVIRONMENT=production
   BACKEND_CORS_ORIGINS=https://your-frontend-domain.vercel.app
   FRONTEND_URL=https://your-frontend-domain.vercel.app
   ALLOWED_HOSTS=your-backend-name.railway.app
   STORAGE_PATH=/app/storage
   
   # Features
   SHOW_BACKEND_LOGS=true
   AUTO_CLEANUP_AUDIO_FILES=true
   ```

5. **Add Volume Storage (Recommended)**
   - Go to "Settings" → "Volumes"
   - Add a new volume:
     - Mount Path: `/app/storage`
     - Size: 1GB (or as needed)

6. **Deploy**
   - Railway will automatically build and deploy using the optimized Dockerfile
   - Build time: ~5-10 minutes (reduced from 20+ minutes)
   - Wait for deployment to complete
   - Note your Railway backend URL (e.g., `https://your-backend-name.railway.app`)

### Step 4: Run Database Migrations

Once deployed, you need to run database migrations:

1. **Install Railway CLI**:
   ```bash
   npm install -g @railway/cli
   ```

2. **Run migrations**:
   ```bash
   # Connect to your Railway service
   railway login
   railway link
   
   # Run database migrations
   railway run alembic upgrade head
   ```

## 🌐 Frontend Deployment (Vercel)

### Step 1: Create Environment Variables

Create a `.env.local` file in your frontend directory:
```bash
REACT_APP_API_URL=https://your-backend-name.railway.app
```

### Step 2: Deploy to Vercel

1. **Go to Vercel Dashboard**
   - Visit [vercel.com](https://vercel.com) and sign in
   - Click "New Project"

2. **Import Repository**
   - Select "Import Git Repository"
   - Choose your GitHub repository
   - Select the `frontend` folder as the root directory

3. **Configure Build Settings**
   - Framework Preset: Create React App
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `build`

4. **Add Environment Variables**
   - In the deployment configuration, add:
     ```
     REACT_APP_API_URL = https://your-backend-name.railway.app
     ```

5. **Deploy**
   - Click "Deploy"
   - Vercel will build and deploy your frontend
   - Note your Vercel frontend URL

### Step 3: Update CORS Settings

Go back to Railway and update your backend environment variables:
```bash
BACKEND_CORS_ORIGINS=https://your-actual-vercel-url.vercel.app
FRONTEND_URL=https://your-actual-vercel-url.vercel.app
```

## 🔄 Update Frontend API URL

Update the production fallback in `frontend/src/utils/api.ts`:
```typescript
// Production fallback (update this with your actual Railway URL)
return 'https://your-actual-backend-name.railway.app';
```

## ⚙️ Production Mode Features

Your production deployment includes these optimizations:

### **Lightweight Processing**:
- **Transcription**: Uses OpenAI Whisper API (more reliable)
- **Speaker Identification**: Simplified approach (basic but functional)
- **Audio Processing**: Essential features only
- **File Storage**: Optimized cleanup and management

### **Performance Benefits**:
- ⚡ Faster startup times
- 💾 Lower memory usage
- 🚀 Quicker deployments
- 💰 Reduced costs

### **API Response Example**:
```json
{
  "message": "Meeting Transcription API",
  "version": "1.0.0",
  "mode": "lightweight",
  "features": {
    "transcription": "OpenAI API",
    "speaker_diarization": "simplified",
    "audio_processing": "basic"
  }
}
```

## ✅ Post-Deployment Checklist

### Backend Health Check
1. Visit `https://your-backend-name.railway.app/` - should return a JSON response
2. Check Railway logs for any errors
3. Test authentication by creating a user account
4. Verify it shows `"mode": "lightweight"` in the response

### Frontend Testing
1. Visit your Vercel URL
2. Test user registration and login
3. Create a test meeting
4. Upload a test audio file (transcription via OpenAI API)

### Database Verification
1. Check Railway database metrics
2. Verify tables were created correctly
3. Test CRUD operations

## 🛠️ Local Development Setup

To keep your local development working:

1. **Run the setup script**:
   ```bash
   ./setup-local-env.sh
   ```

2. **Your local environment can use full ML libraries**:
   - Heavy dependencies work in development
   - Full speaker diarization available
   - Local WhisperX processing

## 🚨 Security Considerations

1. **Never commit `.env` files** - they're already in `.gitignore`
2. **Use strong secret keys** - generate new ones for production
3. **Enable HTTPS only** - both Railway and Vercel provide this automatically
4. **Restrict CORS origins** - only allow your frontend domain
5. **Monitor logs** - check Railway logs regularly for issues

## 💰 Cost Estimates

### Railway (Backend + Database)
- **Hobby Plan**: $5/month (includes $5 usage credit)
- **Expected usage**: $8-15/month for low traffic (optimized!)
- **PostgreSQL**: Included in usage
- **Volume Storage**: $0.25/GB/month

### Vercel (Frontend)
- **Free tier**: Perfect for most use cases
- **Generous limits**: 100GB bandwidth, unlimited static requests

### **Total Monthly Cost: $8-20** (reduced from $15-30 with optimizations!)

## 🔧 Troubleshooting

### Common Issues

1. **Image size exceeded limit**:
   - ✅ **Fixed**: Optimized Dockerfile reduces image from 6.8GB to ~2.5GB
   - Uses CPU-only PyTorch and lightweight dependencies

2. **Build failures**:
   - Check Railway build logs
   - Ensure all dependencies are in requirements-production.txt
   - Verify Dockerfile syntax

3. **Database connection issues**:
   - Verify DATABASE_URL is set correctly
   - Check if migrations ran successfully
   - Ensure PostgreSQL service is running

4. **CORS errors**:
   - Update BACKEND_CORS_ORIGINS with correct frontend URL
   - Ensure no trailing slashes in URLs

5. **Frontend API connection**:
   - Verify REACT_APP_API_URL is set correctly
   - Check browser network tab for failed requests
   - Ensure backend is accessible

### Getting Help

1. **Railway**: Check their documentation and Discord community
2. **Vercel**: Excellent documentation and support
3. **Your App**: Check logs in both Railway and browser console

## 🔄 Updates and Maintenance

### Updating the Application
1. **Push to GitHub** - both platforms auto-deploy on git push
2. **Environment variables** - update through platform dashboards
3. **Database migrations** - run via Railway CLI when needed

### Monitoring
1. **Railway**: Built-in metrics and logs
2. **Vercel**: Analytics and performance monitoring
3. **Set up alerts** for downtime or errors

## 🎉 You're Done!

Your Meeting Transcription System should now be running in production with optimized performance and costs!

### **What You Get**:
- ✅ Fast, reliable transcription via OpenAI API
- ✅ Basic speaker identification
- ✅ Full meeting management and tagging
- ✅ Secure authentication and file handling
- ✅ Dark/light theme support
- ✅ Calendar and grid dashboard views
- ✅ Cost-optimized deployment

### **Future Enhancements**:
If you need advanced features later, you can:
- Upgrade Railway plan for larger images
- Add heavy ML libraries back for local speaker diarization
- Implement real-time transcription with WebSocket streaming 