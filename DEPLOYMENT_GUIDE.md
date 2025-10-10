# 🚀 Deployment Guide - Virtual Patient Simulator

This guide walks you through deploying the Virtual Patient Simulator using Railway (backend) and Vercel (frontend).

## 📋 Prerequisites

- [x] GitHub account
- [x] Railway account (free tier available)
- [x] Vercel account (free tier available)
- [x] OpenAI API key
- [x] Project code in a GitHub repository

## 🚂 Part 1: Deploy Backend to Railway

### Step 1: Push Code to GitHub

1. Initialize git repository (if not already done):
```bash
cd "C:\Users\acer\Desktop\IRPC_Internship\Virtual_Patient_Simulator"
git init
git add .
git commit -m "Initial commit for deployment"
```

2. Create a GitHub repository and push:
```bash
git remote add origin https://github.com/YOUR_USERNAME/virtual-patient-simulator.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy to Railway

1. **Go to [Railway.app](https://railway.app)** and sign in
2. **Click "Deploy from GitHub repo"**
3. **Select your repository**
4. **Choose the Backend folder** as the root directory
5. **Railway will auto-detect** it's a Python project

### Step 3: Configure Environment Variables

In Railway dashboard, go to **Variables** tab and add:

| Variable Name | Value | Notes |
|---------------|--------|-------|
| `OPENAI_API_KEY` | `sk-your-api-key-here` | Your OpenAI API key |
| `ENVIRONMENT` | `production` | Optional: helps identify environment |

### Step 4: Test Backend Deployment

1. **Get your Railway URL** (something like `https://your-app-name.railway.app`)
2. **Test the health endpoint**: `https://your-app-name.railway.app/health`
3. **Check API docs**: `https://your-app-name.railway.app/docs`

## 🌐 Part 2: Deploy Frontend to Vercel

### Step 1: Deploy to Vercel

1. **Go to [Vercel.com](https://vercel.com)** and sign in
2. **Click "Import Project"**
3. **Select your GitHub repository**
4. **Set Framework Preset**: React
5. **Set Root Directory**: `Frontend`

### Step 2: Configure Environment Variables

In Vercel dashboard, go to **Settings > Environment Variables**:

| Variable Name | Value | Environment |
|---------------|--------|-------------|
| `REACT_APP_API_URL` | `https://your-railway-app.railway.app` | Production |
| `REACT_APP_API_URL` | `https://your-railway-app.railway.app` | Preview |

### Step 3: Update CORS in Backend

1. **Get your Vercel URL** (something like `https://your-app.vercel.app`)
2. **Update Railway environment variables**:

Add new variable in Railway:
- `FRONTEND_URL` = `https://your-app.vercel.app`

3. **Update the CORS configuration** in your backend code.

## 🔄 Part 3: Connect Frontend and Backend

### Update Backend CORS

In Railway, update the `CORS_ORIGINS` environment variable:
```
https://your-app.vercel.app,https://your-app-git-main-username.vercel.app
```

### Update Frontend API URL

The frontend should automatically use the environment variable we set in Vercel.

## 🧪 Part 4: Testing the Deployment

### Backend Tests
```bash
# Health check
curl https://your-railway-app.railway.app/health

# API documentation
open https://your-railway-app.railway.app/docs
```

### Frontend Tests
1. **Open your Vercel URL**: `https://your-app.vercel.app`
2. **Test case selection**: Should load cases from Railway backend
3. **Test chat functionality**: Should communicate with Railway backend
4. **Check browser console**: Should show API calls to Railway URL

### Integration Tests
1. **Start a session**: Frontend → Railway backend
2. **Send chat messages**: Frontend ← → Railway backend ← → OpenAI
3. **End session**: Should save and return summary
4. **Download report**: Should work from summary page

## 📊 Monitoring and Logs

### Railway Logs
```bash
# View real-time logs in Railway dashboard
# Or use Railway CLI
railway logs --follow
```

### Vercel Logs
- Check deployment logs in Vercel dashboard
- Use browser developer tools to check frontend errors

## 💰 Cost Monitoring

### Railway (Free Tier Limits)
- **RAM**: 512MB (monitor in dashboard)
- **CPU**: Shared vCPU
- **Bandwidth**: 100GB/month
- **Runtime**: $5 worth (~100-200 hours)

### Vercel (Free Tier Limits)
- **Bandwidth**: 100GB/month
- **Builds**: 6000 build minutes/month
- **Serverless Functions**: 100GB-hours/month

### OpenAI API Costs
- Monitor usage in OpenAI dashboard
- Set usage limits to avoid unexpected charges

## 🚨 Troubleshooting

### Common Issues

#### 1. CORS Errors
**Problem**: `Access to XMLHttpRequest at 'railway-url' from origin 'vercel-url' has been blocked by CORS policy`

**Solution**: 
- Add your Vercel URL to Railway's allowed origins
- Check environment variables are set correctly

#### 2. API Connection Timeout
**Problem**: Frontend can't reach backend

**Solution**:
- Check Railway app is running
- Verify API URL in frontend environment variables
- Test Railway health endpoint directly

#### 3. Railway App Sleeping
**Problem**: Cold starts causing timeouts

**Solution**: 
- Upgrade to paid Railway plan ($10/month)
- Add a keep-alive service (ping health endpoint every 25 minutes)

#### 4. OpenAI API Errors
**Problem**: Chat not working, API key errors

**Solution**:
- Verify OpenAI API key in Railway environment
- Check OpenAI account has credits
- Monitor API usage limits

### Getting Help
- **Railway**: Check Railway Discord or documentation
- **Vercel**: Check Vercel Discord or documentation  
- **OpenAI**: Check OpenAI documentation and status page

## 🎯 Performance Optimization

### Backend (Railway)
- Monitor RAM usage in Railway dashboard
- Implement session cleanup for memory management
- Consider upgrading to paid plan for better performance

### Frontend (Vercel)
- Use Vercel Analytics to monitor performance
- Optimize bundle size if needed
- Leverage Vercel's Edge Network for faster loading

## 📈 Scaling for 20+ Concurrent Users

If you need to handle 20+ concurrent users:

1. **Upgrade Railway to Developer plan** ($10/month)
2. **Monitor resource usage** during testing
3. **Implement rate limiting** to prevent abuse
4. **Consider Redis** for session storage if needed

## 🔐 Security Best Practices

1. **Never commit API keys** to version control
2. **Use environment variables** for all secrets
3. **Enable HTTPS only** (both platforms do this by default)
4. **Monitor API usage** for unusual patterns
5. **Set OpenAI usage limits** to prevent abuse

---

## 📝 Quick Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] Railway backend deployed
- [ ] OpenAI API key set in Railway
- [ ] Backend health endpoint working
- [ ] Vercel frontend deployed
- [ ] Frontend API URL set in Vercel
- [ ] CORS configured in backend
- [ ] Full integration test completed
- [ ] Monitoring and logs checked

## 🎉 Success!

Your Virtual Patient Simulator should now be running on:
- **Backend**: `https://your-app.railway.app`
- **Frontend**: `https://your-app.vercel.app`
- **API Docs**: `https://your-app.railway.app/docs`
