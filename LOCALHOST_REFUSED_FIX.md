# Localhost Refused to Connect - Complete Troubleshooting Guide

## 🚨 The Problem

When clicking "Sign up with Google" you see:
```
localhost refused to connect
```

This error means the browser cannot connect to `http://localhost:5000`.

---

## ✅ Solution 1: Flask App Not Running

### Check if App is Running

```bash
# Terminal should show something like:
# WARNING in app.run_with_reloader
#  * Running on http://127.0.0.1:5000
#  * Debugger is active!

# If you DON'T see this message, app is not running.
```

### Start the App

```bash
# Navigate to the app directory
cd /workspaces/VendorConnect/VendorConnect-main

# Start Flask
python app.py

# Should see output:
# * Running on http://127.0.0.1:5000
# * Press CTRL+C to quit
```

### Verify App Started

1. **Method 1**: Check Terminal Output
   - Look for message: `Running on http://127.0.0.1:5000`
   - If missing: App didn't start

2. **Method 2**: Visit Home Page
   - Open browser
   - Go to: `http://localhost:5000`
   - Should see VendorConnect home page
   - If error: App not running

3. **Method 3**: Check Port Usage
   ```bash
   # Check if port 5000 is in use
   lsof -i :5000
   
   # Should show python process
   # If nothing: Port is free
   # If shows another process: Port in use
   ```

---

## ✅ Solution 2: Port Already in Use

### Identify the Issue

```bash
# Check which process is using port 5000
lsof -i :5000

# Output might look like:
# COMMAND   PID  USER  FD  TYPE DEVICE SIZE NODE NAME
# python  12345  user  3u  IPv4  xxxx  0t0  TCP localhost:5000 (LISTEN)
```

### Fix Options

#### Option A: Kill the Old Process
```bash
# Kill the process using port 5000
kill 12345

# Or use stronger kill
kill -9 12345

# Then start app again
python app.py
```

#### Option B: Use Different Port
```bash
# Start Flask on different port (e.g., 5001)
python app.py --port 5001

# Then visit: http://localhost:5001/vendor/register
```

#### Option C: Use Flask Environment
```bash
# Set custom port via environment variable
export FLASK_ENV=development
export FLASK_PORT=5001
python app.py
```

---

## ✅ Solution 3: Wrong URL

### Verify URL Format

| Status | URL | Works? |
|--------|-----|--------|
| ✅ Correct | `http://localhost:5000/vendor/register` | YES |
| ❌ Wrong | `http://127.0.0.1:5000/vendor/register` | Sometimes |
| ❌ Wrong | `https://localhost:5000/vendor/register` | NO (HTTPS) |
| ❌ Wrong | `localhost:5000/vendor/register` | NO (Missing http://) |

### How to Get Correct URL

1. **From Terminal Output**:
   ```
   Look for: * Running on http://127.0.0.1:5000
   
   Replace 127.0.0.1 with localhost:
   http://localhost:5000
   ```

2. **Add Path**:
   ```
   http://localhost:5000 + /vendor/register
   = http://localhost:5000/vendor/register
   ```

3. **Bookmark It**:
   ```
   Save as bookmark for easy access
   ```

---

## ✅ Solution 4: Network/Firewall Issues

### Check if Local Port is Accessible

```bash
# From Terminal (while Flask is running):
curl http://localhost:5000/vendor/register

# Should see HTML content (long output)
# If error: Server might be blocking or firewall issue
```

### Check Firewall

#### Windows
```bash
# Check if port 5000 is open
netstat -ano | findstr :5000

# If blocked, add exception:
# Settings → Privacy & Security → Firewall → Allow app through firewall
```

#### Mac
```bash
# Check if port 5000 is open
lsof -i :5000

# System Preferences → Security & Privacy → Firewall Options
# Add Python to allowed apps
```

#### Linux
```bash
# Check firewall
sudo ufw status

# If port 5000 blocked, allow it:
sudo ufw allow 5000/tcp

# Or allow for Flask specifically:
sudo ufw allow from 127.0.0.1 to any port 5000
```

---

## ✅ Solution 5: Browser Issues

### Try Different Browser

```
❌ Not working in Chrome? Try Firefox
❌ Not working in Firefox? Try Safari or Edge
❌ Problem persists? Likely server issue
```

### Clear Browser Cache

1. **Chrome**:
   - Settings → Privacy and Security → Clear browsing data
   - Select "All time"
   - Check "Cookies and other site data"
   - Click "Clear data"

2. **Firefox**:
   - Settings → Privacy & Security → Cookies and Site Data
   - Click "Clear Data"

3. **Safari**:
   - Develop → Empty Web Storage
   - Shift+Cmd+Delete (macOS)

### Use Incognito/Private Mode

```
Opens fresh session without cached data
Chrome: Ctrl+Shift+N (Windows) or Cmd+Shift+N (Mac)
Firefox: Ctrl+Shift+P (Windows) or Cmd+Shift+P (Mac)
Safari: Cmd+Shift+N (Mac)
```

---

## ✅ Solution 6: Google OAuth Not Configured

### Check Environment Variables

```bash
# Print environment variables
echo $GOOGLE_CLIENT_ID
echo $GOOGLE_CLIENT_SECRET

# If blank: NOT SET
# If shows value: PROPERLY SET
```

### Set Missing Variables

```bash
# Get credentials from Google Cloud Console
# Then set them:

export GOOGLE_CLIENT_ID="your-client-id-here"
export GOOGLE_CLIENT_SECRET="your-client-secret-here"

# Verify they're set:
echo $GOOGLE_CLIENT_ID
echo $GOOGLE_CLIENT_SECRET

# Both should output values (not blank)
```

### Restart App After Setting Variables

```bash
# Important: Restart Flask for vars to take effect
# Press Ctrl+C to stop
# Then run again:
python app.py
```

---

## 🔍 Comprehensive Diagnostic Script

```bash
#!/bin/bash
# Copy and run this to diagnose issues

echo "🔍 Diagnosing localhost refused to connect..."
echo ""

echo "1. Checking if Flask is running on port 5000..."
if lsof -i :5000 > /dev/null 2>&1; then
    echo "   ✅ Port 5000 is in use"
    lsof -i :5000
else
    echo "   ❌ Port 5000 is FREE (Flask not running!)"
    echo "   💡 Start Flask: python app.py"
fi

echo ""
echo "2. Checking if port 5000 is accessible..."
if curl -s http://localhost:5000 > /dev/null 2>&1; then
    echo "   ✅ Port 5000 is accessible"
else
    echo "   ❌ Port 5000 is not accessible"
    echo "   💡 Check firewall or Flask app status"
fi

echo ""
echo "3. Checking Google OAuth variables..."
if [ -n "$GOOGLE_CLIENT_ID" ]; then
    echo "   ✅ GOOGLE_CLIENT_ID is set"
else
    echo "   ❌ GOOGLE_CLIENT_ID is NOT set"
fi

if [ -n "$GOOGLE_CLIENT_SECRET" ]; then
    echo "   ✅ GOOGLE_CLIENT_SECRET is set"
else
    echo "   ❌ GOOGLE_CLIENT_SECRET is NOT set"
fi

echo ""
echo "4. Testing database connection..."
if [ -f "instance/vendorconnect.db" ]; then
    echo "   ✅ Database file exists"
else
    echo "   ❌ Database file not found"
fi

echo ""
echo "5. Checking Python dependencies..."
python -c "import flask, authlib, sqlalchemy" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "   ✅ All dependencies installed"
else
    echo "   ❌ Missing dependencies"
    echo "   💡 Run: pip install -r requirements.txt"
fi

echo ""
echo "Diagnostic complete! 🎉"
```

### Run the Diagnostic

```bash
# Save as diagnose.sh
bash diagnose.sh

# Or run directly:
bash < diagnose.sh
```

---

## 📋 Step-by-Step Fix Guide

### Fix for Fresh Start

```bash
# Step 1: Navigate to app
cd /workspaces/VendorConnect/VendorConnect-main

# Step 2: Kill any existing Flask process
pkill -f "python app.py" 2>/dev/null

# Step 3: Set Google OAuth credentials
export GOOGLE_CLIENT_ID="your-client-id"
export GOOGLE_CLIENT_SECRET="your-client-secret"

# Step 4: Start Flask
python app.py

# Step 5: Open browser
# Visit: http://localhost:5000/vendor/register

# Step 6: Test
# Click "Sign up with Google"
```

---

## 🆘 Still Not Working?

### Check Server Logs

```bash
# Look at terminal output where Flask is running
# Should see logs like:

[2026-01-07 12:34:56,789] DEBUG in app: Initiating Google OAuth...
[2026-01-07 12:34:57,123] INFO in werkzeug: 127.0.0.1 - - [07/Jan/2026 12:34:56]
"GET /vendor/login/google HTTP/1.1" 302 -
```

### Check Browser Console

```
1. Open browser
2. Press F12 (Developer Tools)
3. Go to Console tab
4. Look for red error messages
5. Screenshot and investigate
```

### Check Network Tab

```
1. Open browser Developer Tools (F12)
2. Go to Network tab
3. Click "Sign up with Google"
4. Look for:
   - 302 redirect (OK)
   - 200 response (OK)
   - 404/500 errors (NOT OK)
```

### Enable Debug Logging

```python
# Add to app.py before running:
import logging
logging.basicConfig(level=logging.DEBUG)

# Then run:
python app.py

# All debug logs will print to terminal
```

---

## 🎯 Issue Checklist

```
If you see "localhost refused to connect":

□ Is Flask running? 
  Yes → Check step 2
  No → Start Flask: python app.py

□ Is port 5000 in use?
  Yes → Check if it's Flask
  No → Start Flask

□ Can you access http://localhost:5000?
  Yes → Check step 3
  No → Check firewall/port

□ Are Google vars set?
  Yes → Check step 4
  No → Set Google credentials

□ Is there an error page?
  Yes → Read error message
  No → Check browser console

□ Does error say "redirect_uri_mismatch"?
  Yes → Update Google Cloud Console redirect URIs
  No → Check other errors
```

---

## 📞 Support Escalation

### If Nothing Works

1. **Save Terminal Output**
   ```bash
   # Run Flask with log output saved
   python app.py > flask.log 2>&1
   
   # Let it run for 30 seconds
   # Then press Ctrl+C
   
   # Check the log file:
   cat flask.log
   ```

2. **Create System Info Report**
   ```bash
   echo "=== System Info ===" > report.txt
   uname -a >> report.txt
   python --version >> report.txt
   echo "=== Flask Status ===" >> report.txt
   lsof -i :5000 >> report.txt 2>&1
   echo "=== Environment ===" >> report.txt
   echo "GOOGLE_CLIENT_ID: $GOOGLE_CLIENT_ID" >> report.txt
   echo "GOOGLE_CLIENT_SECRET: [SET]" >> report.txt
   
   # Share report.txt
   cat report.txt
   ```

3. **Check Documentation**
   - Read: `GOOGLE_OAUTH_SETUP.md`
   - Read: `GOOGLE_SIGNIN_QUICK_REFERENCE.md`

---

## ✅ Success Signs

When working correctly, you should see:

```
✅ Terminal shows:
   * Running on http://127.0.0.1:5000

✅ Browser shows:
   VendorConnect registration page
   "Sign up with Google" button

✅ Clicking button takes you to:
   Google login page (accounts.google.com)

✅ After Google login, you see:
   Signup completion form (prefilled with data)

✅ Database shows new user:
   SELECT * FROM vendor;
   (new row with your email)
```

---

## 🔗 Related Guides

- **Setup Guide**: `GOOGLE_OAUTH_SETUP.md`
- **Testing Guide**: `GOOGLE_SIGNUP_TESTING.md`
- **Quick Reference**: `GOOGLE_SIGNIN_QUICK_REFERENCE.md`
- **Architecture**: `GOOGLE_SIGNIN_ARCHITECTURE.md`

---

**Last Updated**: January 7, 2026
**Version**: 1.0 (Complete Troubleshooting Guide)

**Remember**: "Localhost refused to connect" = Server not running
Start Flask and 90% of issues disappear! 🚀
