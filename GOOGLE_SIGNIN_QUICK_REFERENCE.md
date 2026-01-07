# Google Sign-In Quick Reference

## 🚀 Get Started in 5 Minutes

### 1. Get Google OAuth Credentials
```
1. Go to console.cloud.google.com
2. Create new project
3. Go to APIs & Services → Credentials
4. Create OAuth 2.0 Client ID (Web)
5. Add redirect: http://localhost:5000/vendor/login/google/callback
6. Copy Client ID and Secret
```

### 2. Set Environment Variables
```bash
export GOOGLE_CLIENT_ID="your-client-id"
export GOOGLE_CLIENT_SECRET="your-client-secret"
```

### 3. Start App
```bash
python app.py
```

### 4. Test Registration
```
Visit: http://localhost:5000/vendor/register
Click: "Sign up with Google"
```

## 📱 What Happens

```
User clicks button
         ↓
Google login appears
         ↓
User signs in with Google
         ↓
Form auto-fills with:
- Name ✓
- Email ✓
- Phone ✓
         ↓
User selects role:
- Vendor → asks for GSTIN
- Supplier → asks for categories
- Delivery → asks for vehicle
- Customer → minimal fields
         ↓
User sets password
         ↓
Account created → Auto-login → Dashboard
```

## ⚙️ Configuration

### Environment Variables
```bash
# Required
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret

# Optional (for production)
GOOGLE_REDIRECT_URI=https://your-domain.com/vendor/login/google/callback
```

### Google Cloud Console Settings
- **Authorized redirect URIs:**
  - Development: `http://localhost:5000/vendor/login/google/callback`
  - Production: `https://your-domain.com/vendor/login/google/callback`

## 🔧 Routes

| Route | Purpose |
|-------|---------|
| `/vendor/register` | Signup page with Google button |
| `/vendor/login/google` | Start OAuth (redirects to Google) |
| `/vendor/login/google/callback` | Google redirects here |
| `/signup/complete` | Fill additional details |

## 📋 Data Flow

### Form Pre-fills With
```javascript
{
  email: "user@gmail.com",      // From Google (read-only)
  name: "John Doe",              // From Google (editable)
  phone: "+1234567890"           // From Google (editable)
}
```

### User Must Fill
- Role (Vendor/Supplier/Delivery/Customer)
- Password (8+ chars, uppercase, lowercase, number)
- Location (optional)
- Role-specific fields:
  - Vendor: GSTIN, Business Type
  - Supplier: Categories
  - Delivery: Vehicle Type, Registration
  - Customer: (none required)

## ✅ Testing Checklist

### Minimal Test (2 min)
- [ ] Click Google button
- [ ] Sign in with Gmail
- [ ] Form loads with data
- [ ] Submit form
- [ ] New account created

### Quick Test (5 min)
- [ ] Test Vendor signup
- [ ] Test Supplier signup
- [ ] Test Delivery Agent signup
- [ ] Test Customer signup

### Full Test (15 min)
- [ ] All roles work
- [ ] Password validation works
- [ ] Error messages clear
- [ ] Existing user logs in directly
- [ ] Mobile responsive

## 🐛 Troubleshooting

### "localhost refused to connect"
```bash
# Solution: Start Flask app
python app.py

# Or check if already running on 5000:
lsof -i :5000
```

### "Google OAuth not configured"
```bash
# Check environment variables
echo $GOOGLE_CLIENT_ID
echo $GOOGLE_CLIENT_SECRET

# They must be set (not empty)
```

### "redirect_uri_mismatch"
```
Problem: URL in Google Cloud doesn't match
Solution: 
1. Go to Google Cloud Console
2. Go to Credentials
3. Click OAuth client ID
4. Verify redirect URI matches exactly:
   http://localhost:5000/vendor/login/google/callback
5. Save and try again
```

### "Session expired"
```
Solution: Just click Google button again
The session timeout is usually 24 hours
```

## 📊 Database Check

```bash
# Connect to database
sqlite3 instance/vendorconnect.db

# Check if user created
SELECT id, name, email, phone FROM vendor 
WHERE email = 'your@gmail.com';

# Check all vendor fields
SELECT * FROM vendor WHERE email = 'your@gmail.com';

# Exit
.quit
```

## 🔐 Security

- ✅ Passwords hashed with PBKDF2
- ✅ Email from Google (trusted)
- ✅ Phone can be user-edited
- ✅ JWT tokens for sessions
- ✅ HTTPS required in production
- ✅ No sensitive data in URLs

## 📚 Full Documentation

- **Setup Guide**: `GOOGLE_OAUTH_SETUP.md`
- **Testing Guide**: `GOOGLE_SIGNUP_TESTING.md`
- **Implementation Details**: `GOOGLE_SIGNIN_IMPLEMENTATION.md`

## 🎯 Role-Specific Fields

### Vendor (Food Stall)
```
Required: GSTIN, Business Type
Optional: Location
Database Fields: gstin, business_type, location
```

### Supplier (Bulk Provider)
```
Required: Categories, Password
Optional: Business Name, GSTIN, Location
Database Fields: business_name, gstin, location
```

### Delivery Agent
```
Required: Vehicle Type, Vehicle Reg, Password
Optional: Location
Database Fields: vehicle_type, vehicle_info, location
```

### Customer (Buyer)
```
Required: Password
Optional: Location
Database Fields: location
```

## 🚀 Production Deployment

### Render.com
```
1. Add Environment Variables:
   - GOOGLE_CLIENT_ID
   - GOOGLE_CLIENT_SECRET
   - GOOGLE_REDIRECT_URI=https://your-app.onrender.com/vendor/login/google/callback

2. Update Google Cloud Console:
   - Add redirect: https://your-app.onrender.com/vendor/login/google/callback

3. Deploy and test
```

### Other Platforms
Same steps - just replace URL with your domain.

## 📞 Support

**Common Questions:**

Q: Do I need to create Google account?
A: No, users sign in with their existing Google/Gmail account.

Q: Is this only for vendors?
A: No! Supports Vendor, Supplier, Delivery Agent, and Customer roles.

Q: What data from Google is used?
A: Name, Email, Phone (if available). That's it.

Q: Can users change email after signup?
A: No, email is locked (from Google). But they can change name/phone.

Q: What if user signs up then tries with different Google?
A: They'll get error "Email already exists" for that role.

Q: How to test without real Google account?
A: Create a test Gmail account (free).

## 🔄 User Login After Signup

**After signup, user is automatically logged in:**
1. ✅ Session set
2. ✅ JWT token created
3. ✅ Redirected to dashboard
4. ✅ No need to login again

**To login later:**
1. Go to `/vendor/login`
2. Enter phone/email + password
3. Or click "Sign up with Google" again (skips form)

## 📈 What's Tracked

```
✅ Email (from Google)
✅ Name (from Google, editable)
✅ Phone (from Google or user-entered)
✅ Role (Vendor/Supplier/Delivery/Customer)
✅ Password (user-created)
✅ Location (user-entered)
✅ Role-specific fields (GSTIN, categories, vehicle, etc.)
✅ Account creation timestamp
```

## 🎓 Example Walkthrough

```
1. Bob visits vendor/register
2. Clicks "Sign up with Google"
3. Signs in with bob@gmail.com
4. Sees form with:
   - Email: bob@gmail.com (locked)
   - Name: Bob Smith (editable)
   - Phone: (blank or from Google)
5. Selects role: "Vendor (Food Stall)"
6. Form shows GSTIN field
7. Enters:
   - Location: Bandra West, Mumbai
   - Business Type: Chaat
   - GSTIN: 27AABCH1234A1Z0
   - Password: MyChaat2024!
8. Clicks "Complete Signup"
9. Account created
10. Auto-logged in
11. Sees vendor dashboard
```

## ✨ Features

- 🎯 One-click signup
- 📝 Pre-filled form (less typing)
- 🔐 Secure (OAuth2)
- 📱 Mobile responsive
- ⚡ Fast (no email verification)
- 🎨 Beautiful UI
- ♿ Accessible
- 🌙 Dark mode support

---

**Version**: 2.0 (Jan 7, 2026)
**Status**: ✅ Production Ready

Quick questions? Check `GOOGLE_OAUTH_SETUP.md` for detailed answers!
