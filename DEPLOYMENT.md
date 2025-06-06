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

## 📦 Backend Deployment (Railway)

### Step 1: Prepare Environment Variables

First, generate a secure secret key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 2: Deploy to Railway

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
   - Railway will automatically build and deploy using the Dockerfile
   - Wait for deployment to complete
   - Note your Railway backend URL (e.g., `https://your-backend-name.railway.app`)

### Step 3: Run Database Migrations

Once deployed, you need to run database migrations:

1. **Open Railway CLI or use the web terminal**
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

## ✅ Post-Deployment Checklist

### Backend Health Check
1. Visit `https://your-backend-name.railway.app/` - should return a JSON response
2. Check Railway logs for any errors
3. Test authentication by creating a user account

### Frontend Testing
1. Visit your Vercel URL
2. Test user registration and login
3. Create a test meeting
4. Upload a test audio file

### Database Verification
1. Check Railway database metrics
2. Verify tables were created correctly
3. Test CRUD operations

## 🛠️ Local Development Setup

To keep your local development working:

1. **Create `.env` file in backend directory**:
   ```bash
   cp backend/env.example backend/.env
   # Edit with your local settings
   ```

2. **Create `.env.local` file in frontend directory**:
   ```bash
   cp frontend/env.example frontend/.env.local
   # Set REACT_APP_API_URL=http://localhost:8000
   ```

## 🚨 Security Considerations

1. **Never commit `.env` files** - they're already in `.gitignore`
2. **Use strong secret keys** - generate new ones for production
3. **Enable HTTPS only** - both Railway and Vercel provide this automatically
4. **Restrict CORS origins** - only allow your frontend domain
5. **Monitor logs** - check Railway logs regularly for issues

## 💰 Cost Estimates

### Railway (Backend + Database)
- **Hobby Plan**: $5/month (includes $5 usage credit)
- **Expected usage**: $10-20/month for low traffic
- **PostgreSQL**: Included in usage

### Vercel (Frontend)
- **Free tier**: Perfect for most use cases
- **Generous limits**: 100GB bandwidth, unlimited static requests

### Total Monthly Cost: $10-25

## 🔧 Troubleshooting

### Common Issues

1. **Build failures**:
   - Check Railway build logs
   - Ensure all dependencies are in requirements.txt
   - Verify Dockerfile syntax

2. **Database connection issues**:
   - Verify DATABASE_URL is set correctly
   - Check if migrations ran successfully
   - Ensure PostgreSQL service is running

3. **CORS errors**:
   - Update BACKEND_CORS_ORIGINS with correct frontend URL
   - Ensure no trailing slashes in URLs

4. **Frontend API connection**:
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

Your Meeting Transcription System should now be running in production! Test all functionality and monitor the logs for any issues. 