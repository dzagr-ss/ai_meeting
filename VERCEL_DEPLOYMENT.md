# Vercel Frontend Deployment Fix

## Issues Fixed
The following errors have been resolved:

1. **✅ Import Error**: `'API_URL' is not exported from '../utils/api'`
2. **✅ CSP Error**: `Refused to connect to 'https://aimeeting.up.railway.app/token' because it violates the following Content Security Policy directive`

### 1. API_URL Export Fix
**Added API_URL export** in `frontend/src/utils/api.ts`:
```typescript
// Export the API URL as a constant for backward compatibility
export const API_URL = getApiUrl();
```

### 2. Content Security Policy Fix  
**Updated CSP** in `frontend/public/index.html` to allow Railway backend connections:
```html
connect-src 'self' ws: wss: http://localhost:8000 https://api.openai.com https://aimeeting.up.railway.app *.railway.app;
```

### 3. Vercel Configuration
**Created Vercel configuration** in `frontend/vercel.json`

## Vercel Environment Variables Setup

### Required Environment Variables
Set these in your Vercel dashboard under **Project Settings > Environment Variables**:

```bash
REACT_APP_API_URL=https://aimeeting.up.railway.app
```

### How to Set Environment Variables in Vercel:

1. Go to your Vercel dashboard
2. Select your project
3. Go to **Settings** > **Environment Variables**
4. Add the following variable:
   - **Name**: `REACT_APP_API_URL`
   - **Value**: `https://aimeeting.up.railway.app`
   - **Environment**: Production (and Preview if needed)

## Build Configuration

The `frontend/vercel.json` file is configured with:
- Build command: `npm run build`
- Output directory: `build`
- Proper routing for React SPA
- Environment variables

## Deployment Steps

1. **Push the changes** to your repository
2. **Set environment variables** in Vercel dashboard
3. **Trigger a new deployment** (or it will auto-deploy)

## Troubleshooting

If build still fails:

1. **Check Environment Variables**: Ensure `REACT_APP_API_URL` is set in Vercel
2. **Clear Build Cache**: In Vercel, go to Deployments > ⋯ > Redeploy
3. **Check Logs**: Look at the build logs in Vercel for specific errors

## Expected Build Success

After these changes, the frontend should:
- ✅ Build successfully on Vercel
- ✅ Connect to the Railway backend API
- ✅ Handle environment variables properly
- ✅ Route correctly for React SPA

## Backend URL Update

If your Railway backend URL is different, update the environment variable:
```bash
REACT_APP_API_URL=https://your-actual-railway-url.railway.app
```

## Files Modified

1. `frontend/src/utils/api.ts` - Added `API_URL` export
2. `frontend/vercel.json` - Added Vercel configuration
3. This deployment guide

The frontend should now deploy successfully on Vercel! 🚀 