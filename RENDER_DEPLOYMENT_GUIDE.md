# VendorConnect - Render Deployment Guide

## 🚀 Complete Step-by-Step Guide to Deploy VendorConnect on Render

### Prerequisites
- GitHub account
- Render account (free tier available)
- Your VendorConnect project files

---

## Step 1: Prepare Your Project for GitHub

### 1.1 Initialize Git Repository (if not already done)
```bash
cd VendorConnect-main
git init
git add .
git commit -m "Initial commit - VendorConnect project"
```

### 1.2 Create GitHub Repository
1. Go to [GitHub.com](https://github.com) and sign in
2. Click the "+" icon in the top right corner
3. Select "New repository"
4. Name it: `vendorconnect-app`
5. Make it **Public** (required for free Render tier)
6. Don't initialize with README (since you already have files)
7. Click "Create repository"

### 1.3 Push Your Code to GitHub
```bash
git remote add origin https://github.com/YOUR_USERNAME/vendorconnect-app.git
git branch -M main
git push -u origin main
```

---

## Step 2: Deploy to Render

### 2.1 Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up using your GitHub account
3. Verify your email address

### 2.2 Create New Web Service
1. In your Render dashboard, click **"New +"**
2. Select **"Web Service"**
3. Connect your GitHub account if not already connected
4. Select your `vendorconnect-app` repository
5. Click **"Connect"**

### 2.3 Configure Deployment Settings

#### Basic Settings:
- **Name**: `vendorconnect-app` (or your preferred name)
- **Environment**: `Python 3`
- **Region**: Choose closest to your users (e.g., Oregon for US, Frankfurt for Europe)
- **Branch**: `main`
- **Root Directory**: Leave empty (or set to `VendorConnect-main` if your app is in a subfolder)

#### Build & Deploy Settings:
- **Build Command**: 
  ```bash
  pip install -r requirements.txt
  ```
- **Start Command**: 
  ```bash
  gunicorn app:app
  ```

#### Advanced Settings:
- **Python Version**: `3.11.0` (as specified in runtime.txt)
- **Auto-Deploy**: `Yes` (automatically deploys when you push to main branch)

### 2.4 Environment Variables (Optional)
If you need any environment variables, add them in the "Environment" section:
- `FLASK_ENV`: `production`
- `SECRET_KEY`: `your-secret-key-here` (for production security)

### 2.5 Deploy
1. Click **"Create Web Service"**
2. Render will automatically:
   - Clone your repository
   - Install dependencies from requirements.txt
   - Build your application
   - Deploy it to a public URL

---

## Step 3: Verify Deployment

### 3.1 Check Build Logs
1. In your Render dashboard, click on your service
2. Go to the "Logs" tab
3. Watch the build process - it should complete without errors

### 3.2 Test Your Application
1. Once deployed, you'll get a URL like: `https://vendorconnect-app.onrender.com`
2. Visit the URL to test your application
3. Test key features:
   - Home page loads
   - Vendor registration works
   - Vendor login works
   - Chatbot functionality
   - Product browsing

---

## Step 4: Custom Domain (Optional)

### 4.1 Add Custom Domain
1. In your Render service dashboard
2. Go to "Settings" tab
3. Scroll to "Custom Domains"
4. Add your domain (e.g., `vendorconnect.com`)
5. Follow DNS configuration instructions

---

## Step 5: Monitor and Maintain

### 5.1 Monitor Performance
- Check Render dashboard for uptime and performance metrics
- Monitor logs for any errors
- Set up alerts for downtime

### 5.2 Update Your Application
1. Make changes to your code locally
2. Test changes locally
3. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Update: description of changes"
   git push origin main
   ```
4. Render will automatically redeploy

---

## 🔧 Troubleshooting Common Issues

### Issue 1: Build Fails
**Problem**: Build command fails during deployment
**Solution**: 
- Check that all dependencies are in requirements.txt
- Ensure Python version matches runtime.txt
- Check build logs for specific error messages

### Issue 2: App Crashes on Startup
**Problem**: Application starts but crashes immediately
**Solution**:
- Check start command is correct: `gunicorn app:app`
- Verify all imports work correctly
- Check environment variables

### Issue 3: Database Issues
**Problem**: SQLite database not working
**Solution**:
- SQLite works on Render but data is ephemeral
- Consider upgrading to PostgreSQL for persistent data
- Check file permissions and paths

### Issue 4: Static Files Not Loading
**Problem**: CSS/JS/images not loading
**Solution**:
- Ensure static files are in the correct directory
- Check Flask static file configuration
- Verify file paths in templates

---

## 📊 Render Free Tier Limitations

### What's Included:
- ✅ 750 hours of build time per month
- ✅ 512MB RAM
- ✅ Automatic deployments from GitHub
- ✅ Custom domains
- ✅ HTTPS certificates

### Limitations:
- ⚠️ Service sleeps after 15 minutes of inactivity
- ⚠️ Cold start takes ~30 seconds
- ⚠️ No persistent file storage (SQLite data resets)
- ⚠️ Limited to 1 concurrent request

### Upgrading:
- **Starter Plan**: $7/month - No sleep, 512MB RAM
- **Standard Plan**: $25/month - 1GB RAM, better performance

---

## 🎯 Production Recommendations

### 1. Database Upgrade
For production use, consider upgrading to PostgreSQL:
```python
# In app.py, replace SQLite with PostgreSQL
import os
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///vendorconnect.db')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
```

### 2. Environment Variables
Set these in Render dashboard:
- `SECRET_KEY`: Strong secret key for sessions
- `FLASK_ENV`: `production`
- `DATABASE_URL`: If using PostgreSQL

### 3. Security
- Use environment variables for sensitive data
- Enable HTTPS (automatic on Render)
- Implement proper error handling
- Add input validation

---

## 🚀 Your Application is Live!

Once deployed, your VendorConnect application will be available at:
`https://your-app-name.onrender.com`

### Key Features Available:
- ✅ Vendor registration and login
- ✅ Product catalog with images
- ✅ Intelligent chatbot with voice support
- ✅ Multi-language support (English, Hindi, Bengali, Tamil)
- ✅ Group ordering system
- ✅ Price alerts and notifications
- ✅ Mobile-responsive design

### Next Steps:
1. Test all functionality thoroughly
2. Share the URL with users
3. Monitor performance and user feedback
4. Consider upgrading to paid plan for better performance
5. Add PostgreSQL database for data persistence

---

## 📞 Support

If you encounter any issues:
1. Check Render documentation: [render.com/docs](https://render.com/docs)
2. Review build logs in Render dashboard
3. Test locally first before deploying
4. Check Flask application logs

**Happy Deploying! 🎉**
