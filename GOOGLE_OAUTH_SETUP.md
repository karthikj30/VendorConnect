# Google Sign-In Implementation Guide

## Overview

The VendorConnect app now supports Google Sign-In for all user roles (Vendor, Supplier, Delivery Agent, Customer) with a seamless multi-step flow:

1. User clicks "Sign up with Google" button
2. Redirected to Google OAuth login
3. Google fetches user data (name, email, phone)
4. Pre-filled form appears for additional details
5. User fills in role-specific information (GSTIN, categories, vehicle type, etc.)
6. User is automatically logged in and redirected to dashboard

## Setup Instructions

### Step 1: Create Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing one)
3. Go to **APIs & Services** → **Credentials**
4. Click **Create Credentials** → **OAuth 2.0 Client ID**
5. Select **Web application**
6. Add Authorized redirect URIs:
   - `http://localhost:5000/vendor/login/google/callback` (for local development)
   - `http://localhost:5000/signup/complete` (if needed)
   - Your production URL + `/vendor/login/google/callback`

7. Copy your **Client ID** and **Client Secret**

### Step 2: Set Environment Variables

For local development, set environment variables:

```bash
export GOOGLE_CLIENT_ID="your-client-id-here"
export GOOGLE_CLIENT_SECRET="your-client-secret-here"
export GOOGLE_REDIRECT_URI="http://localhost:5000/vendor/login/google/callback"
```

For production (Render.com, etc.), add these as environment variables in your deployment settings.

### Step 3: Fix "localhost refused to connect" Error

The error typically means:
- **The app server is not running** - Start with `python app.py`
- **Wrong localhost URL** - Make sure you're using `http://localhost:5000`
- **Port is blocked** - Try a different port: `python app.py --port 5001`
- **Google OAuth not configured** - Check environment variables are set correctly

### Step 4: Verify Setup

1. Start the app: `python app.py`
2. Navigate to: `http://localhost:5000/vendor/register`
3. Click "Sign up with Google"
4. If you get an error page, check:
   - Browser console (F12) for JavaScript errors
   - Terminal logs for Python errors
   - Environment variables are set correctly

## Flow Explanation

### Route Map

| Route | Purpose |
|-------|---------|
| `/vendor/register` | Initial registration form with Google button |
| `/vendor/login/google` | Start Google OAuth flow |
| `/vendor/login/google/callback` | Google redirects here after auth |
| `/signup/complete` | Multi-role signup completion form |
| `/auth/google/callback` | Alternative OAuth endpoint |

### How It Works

1. **User clicks "Sign up with Google"**
   - Button links to `/vendor/login/google`
   - This starts the OAuth2 flow

2. **Google OAuth Callback**
   - Google calls `/vendor/login/google/callback`
   - App verifies the token
   - Fetches user info from Google
   - Checks if email exists (login flow) or new (signup flow)

3. **For Existing Users (Login)**
   - User email found in database
   - Creates JWT token
   - Sets session cookie
   - Redirects to dashboard

4. **For New Users (Signup)**
   - User email not found
   - Stores Google data in session
   - Redirects to `/signup/complete`

5. **Signup Completion**
   - Pre-fills form with Google data (name, email, phone)
   - Shows role selector
   - Conditional fields appear based on selected role
   - User fills additional required fields:
     - **Vendor**: GSTIN, Business Type, Location
     - **Supplier**: Business Name, GSTIN (optional), Categories
     - **Delivery Agent**: Vehicle Type, Vehicle Registration
     - **Customer**: Location (optional)
   - User sets password
   - Account created and user logged in

## Data Fetched from Google

```python
{
    'email': 'user@example.com',           # Required from Google
    'name': 'John Doe',                     # Display name
    'given_name': 'John',                   # First name if needed
    'phone_number': '+1234567890',          # May be empty
    'sub': 'google-unique-id',              # Unique Google ID
    'picture': 'https://...',               # Profile picture URL
}
```

## API Endpoints

### POST /signup/complete

Complete the signup process after Google OAuth.

**Request:**
```json
{
    "role": "Vendor",
    "name": "John Doe",
    "phone": "9876543210",
    "location": "Mumbai",
    "password": "SecurePass123",
    "business_type": "chaat",
    "gstin": "27AABCH1234A1Z0"
}
```

**Response (Success):**
```json
{
    "success": true,
    "message": "Vendor registration successful!",
    "redirect": "/vendor/dashboard"
}
```

**Response (Error):**
```json
{
    "success": false,
    "message": "GSTIN is required for vendors"
}
```

## Role-Specific Requirements

### Vendor
- **Required**: GSTIN, Business Type, Password
- **Optional**: Location
- **Database Fields**: gstin, business_type, location

### Supplier
- **Required**: Categories, Password
- **Optional**: Business Name, GSTIN, Location
- **Database Fields**: business_name, gstin, location

### Delivery Agent
- **Required**: Vehicle Type, Vehicle Registration, Password
- **Optional**: Location
- **Database Fields**: vehicle_type, vehicle_info, location

### Customer
- **Required**: Password
- **Optional**: Location
- **Database Fields**: location

## Error Handling

### Common Issues

1. **"Localhost refused to connect"**
   - Solution: Start Flask server (`python app.py`)
   - Or use correct port if changed

2. **"redirect_uri_mismatch"**
   - Solution: Update Google Cloud Console with correct redirect URI
   - Must match exactly in auth request

3. **"Google OAuth not configured"**
   - Solution: Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` env vars

4. **"Session expired. Please sign in with Google again"**
   - Solution: User session timed out
   - They need to click Google button again

5. **"An account with this email already exists"**
   - Solution: User already has account
   - They should login instead of signup

## Testing Checklist

- [ ] Google button appears on registration page
- [ ] Clicking button redirects to Google login
- [ ] Can login with Google account
- [ ] Returned to signup completion form
- [ ] Form has Google data pre-filled
- [ ] Can select different roles
- [ ] Role-specific fields appear/hide correctly
- [ ] Can fill and submit form
- [ ] New account created in database
- [ ] User logged in and redirected to dashboard
- [ ] Password validation works
- [ ] Error messages display correctly
- [ ] Session properly cleared after signup

## Database Schema

### New Tables/Fields

- `Vendor.gstin` - GSTIN for tax registration
- `Vendor.business_type` - Type of food stall
- `Supplier.business_name` - Supplier business name
- `Supplier.gstin` - Tax ID (optional)
- `DeliveryAgent.vehicle_type` - Type of vehicle
- `DeliveryAgent.vehicle_info` - Registration number
- `Customer.location` - Default location

All user types have:
- `email` - Unique email from Google
- `password_hash` - Set during signup
- `phone` - From Google or user input

## Security Notes

1. **No hardcoded credentials** - Use environment variables
2. **JWT tokens** - Secure session management
3. **Password hashing** - Uses werkzeug
4. **HTTPS in production** - Required by Google OAuth
5. **No sensitive data in cookies** - Httponly flag set

## Troubleshooting

### Check Environment Variables
```bash
echo $GOOGLE_CLIENT_ID
echo $GOOGLE_CLIENT_SECRET
```

### View Detailed Logs
```bash
export FLASK_DEBUG=1
python app.py
```

### Test OAuth Flow
```bash
# 1. Start app
python app.py

# 2. Visit registration page
open http://localhost:5000/vendor/register

# 3. Click "Sign up with Google"
# 4. Check browser console (F12) for errors
# 5. Check terminal for server errors
```

### Database Check
```bash
# Connect to SQLite
sqlite3 instance/vendorconnect.db

# Check if user was created
SELECT * FROM vendor WHERE email = 'your-email@google.com';
SELECT * FROM supplier WHERE email = 'your-email@google.com';
```

## Production Deployment

### Render.com

1. Add environment variables:
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `GOOGLE_REDIRECT_URI=https://your-app.onrender.com/vendor/login/google/callback`

2. Ensure Google Cloud Console has:
   - Authorized redirect: `https://your-app.onrender.com/vendor/login/google/callback`

3. Update any hardcoded URLs to use environment variables

### Vercel/Other Platforms

Similar steps - ensure:
- Redirect URI matches deployment URL
- Environment variables set correctly
- HTTPS is enforced

## Code Examples

### Manual Google OAuth Without Our Form

If you want to use Google Sign-In button directly:

```html
<script src="https://accounts.google.com/gsi/client" async defer></script>
<div id="g_id_onload"
     data-client_id="YOUR_CLIENT_ID"
     data-callback="handleCredentialResponse">
</div>
<div class="g_id_signin" data-type="standard"></div>
```

However, our implementation uses server-side OAuth which is more secure.

## Support

For issues:
1. Check error template displays
2. Review browser console (F12)
3. Check app logs in terminal
4. Verify all environment variables set
5. Clear browser cookies and retry

---

**Last Updated**: January 7, 2026
**Version**: 2.0 (Complete Multi-Role Google OAuth)
