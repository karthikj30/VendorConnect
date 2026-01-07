# Google Sign-In Testing Guide

## Quick Start - Complete Testing in 5 Minutes

### Prerequisites
1. Google account (any Gmail address works)
2. Google OAuth credentials set up
3. Flask app running locally

### Step-by-Step Testing

#### 1. Start the App
```bash
cd /workspaces/VendorConnect/VendorConnect-main
export GOOGLE_CLIENT_ID="your-client-id"
export GOOGLE_CLIENT_SECRET="your-client-secret"
python app.py
```

#### 2. Navigate to Registration Page
```
http://localhost:5000/vendor/register
```

#### 3. Click "Sign up with Google"
- Button should redirect to Google login
- If you see "localhost refused to connect":
  - Check Flask is running
  - Use correct port (default 5000)
  - Check environment variables are set

#### 4. Sign In with Google Account
- Enter your Google credentials
- Allow VendorConnect permissions
- Should be redirected to signup completion form

#### 5. Fill in Details by Role

##### Test as Vendor:
- Role: "Vendor (Food Stall)"
- Name: (pre-filled from Google)
- Phone: 9876543210
- Location: Mumbai
- Business Type: Chaat
- GSTIN: 27AABCH1234A1Z0
- Password: TestPass123

##### Test as Supplier:
- Role: "Supplier (Bulk Provider)"
- Name: (pre-filled)
- Phone: 9876543210
- Location: Mumbai
- Business Name: My Wholesale
- Categories: Vegetables, Fruits
- Password: TestPass123

##### Test as Delivery Agent:
- Role: "Delivery Agent"
- Phone: 9876543210
- Location: Mumbai
- Vehicle Type: 🚗 Car
- Vehicle Registration: KA01AB1234
- Password: TestPass123

##### Test as Customer:
- Role: "Customer (Buyer)"
- Phone: 9876543210
- Location: Mumbai
- Password: TestPass123

#### 6. Verify Account Creation
After submission, you should:
- ✅ See success message
- ✅ Be automatically logged in
- ✅ Be redirected to appropriate dashboard
- ✅ Find new account in database

## Detailed Test Cases

### Test Case 1: Google Data Pre-Fill
**Expected Behavior:**
- Name field has value from Google
- Email field locked/read-only or pre-filled
- Phone field filled if available from Google

**Test Steps:**
1. Sign up with Google
2. Check form displays Google data
3. Verify you can edit name if needed
4. Verify email cannot be changed (it's from Google)

### Test Case 2: Role Switching
**Expected Behavior:**
- Selecting role shows/hides appropriate fields
- Vendor role → shows Business Type + GSTIN
- Supplier role → shows Categories field
- Delivery Agent → shows Vehicle fields
- Customer → minimal fields

**Test Steps:**
1. On signup completion form
2. Change role dropdown multiple times
3. Verify correct fields appear for each role
4. Verify previously hidden fields are hidden

### Test Case 3: Password Validation
**Expected Behavior:**
- Shows real-time validation
- At least 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 number
- Confirm password must match

**Test Steps:**
1. Focus on password field
2. Type "abc" → shows all requirements unmet
3. Type "abcDefgh1" → shows all requirements met
4. Mismatch confirm password → error shows

### Test Case 4: Form Submission Validation
**Expected Behavior:**
- Validates all required fields
- Shows specific error for missing/invalid data
- Doesn't submit until valid

**Test Steps for Vendor:**
1. Don't fill phone → error "Please enter a valid phone number"
2. Fill phone with 5 digits → error
3. Don't fill GSTIN → error "GSTIN is required for vendors"
4. Fill invalid GSTIN → should still work (accepts any 15 chars)

**Test Steps for Delivery Agent:**
1. Don't select vehicle type → error
2. Don't fill vehicle info → error
3. Fill both → should work

### Test Case 5: Duplicate Account Prevention
**Expected Behavior:**
- Cannot create two accounts with same email
- Cannot create two accounts with same phone (within role)
- Error message is clear

**Test Steps:**
1. Sign up as Vendor with email/phone
2. Try to sign up again with same email → error
3. Verify error message: "An account with this email already exists"

### Test Case 6: Login vs Signup Flow
**Expected Behavior:**
- If email exists → straight to dashboard (login flow)
- If email new → go to signup form (signup flow)

**Test Steps - Login:**
1. Create account: test@example.com
2. Logout
3. Go to register page
4. Sign up with Google using same email
5. Should skip signup form and go to dashboard

**Test Steps - Signup:**
1. Use different email
2. Sign up with Google
3. Fill signup form
4. Create new account

### Test Case 7: Error Handling
**Expected Behavior:**
- Network errors show nice error page
- Expired session handled gracefully
- Invalid data shows helpful messages

**Test Steps:**
1. Start signup but let session expire (wait 30+ mins)
2. Try to submit → error "Session expired"
3. Check error page has "Back to Signup" button
4. Click button → goes back to register page

### Test Case 8: Database Integrity
**Expected Behavior:**
- New user records created correctly
- All fields populated
- Phone is unique or allows duplicates (verify design)
- Email is unique

**Test Steps:**
1. Create account with specific email
2. Check database:
   ```bash
   sqlite3 instance/vendorconnect.db
   SELECT * FROM vendor WHERE email = 'new-user@gmail.com';
   ```
3. Verify all fields present and correct

### Test Case 9: Session & Login After Signup
**Expected Behavior:**
- User immediately logged in after signup
- Can access dashboard
- Session persists across page reloads
- Can logout and login with password

**Test Steps:**
1. Complete signup
2. Check you're in dashboard
3. Refresh page → still in dashboard
4. Logout
5. Try accessing dashboard → redirected to login
6. Login with email/password → back in dashboard

### Test Case 10: Mobile Responsiveness
**Expected Behavior:**
- Form works on mobile
- Fields stack properly
- Buttons are touch-friendly
- No horizontal scrolling

**Test Steps:**
1. Open signup form on mobile device
2. Or use browser dev tools (F12 → device emulation)
3. Test on iPhone, Android viewport sizes
4. Verify form is usable

## Automated Testing (Optional)

### Test Script
```python
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

def test_google_signup():
    """Automated test for Google signup flow"""
    driver = webdriver.Chrome()
    
    try:
        # Step 1: Navigate to register
        driver.get("http://localhost:5000/vendor/register")
        
        # Step 2: Find Google button
        google_btn = driver.find_element(By.XPATH, 
            "//button[contains(text(), 'Sign')]")
        
        # Step 3: Click and wait
        google_btn.click()
        time.sleep(5)
        
        # Step 4: Check if redirected to Google
        assert "accounts.google.com" in driver.current_url
        
        print("✅ Google signup button works!")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_google_signup()
```

## Debugging Checklist

### "Localhost refused to connect"
- [ ] Flask app is running on 5000
- [ ] No firewall blocking port 5000
- [ ] Try different port if 5000 is in use
- [ ] Check for typos in URL

### "Google OAuth not configured"
- [ ] `GOOGLE_CLIENT_ID` environment variable set
- [ ] `GOOGLE_CLIENT_SECRET` environment variable set
- [ ] No extra spaces or quotes in values
- [ ] Restart Flask after setting variables

### "redirect_uri_mismatch" error
- [ ] Google Cloud Console has correct redirect URI
- [ ] Redirect URI matches deployment URL exactly
- [ ] Try: `http://localhost:5000/vendor/login/google/callback`
- [ ] Check for typos in redirect URI

### Blank form after Google login
- [ ] Check browser console (F12)
- [ ] Check Flask logs in terminal
- [ ] Session may have expired - try again
- [ ] Try incognito/private window

### Form won't submit
- [ ] Check all required fields filled
- [ ] Passwords must match
- [ ] Phone must be 10+ digits
- [ ] Check browser console for JavaScript errors
- [ ] Try different browser

## Performance Testing

### Check Loading Times
```javascript
// In browser console:
performance.timing.loadEventEnd - performance.timing.navigationStart
// Should be < 3000ms
```

### Measure OAuth Redirect Time
1. Note time before clicking Google button
2. Note time when signup form loads
3. Should be < 5 seconds total

## Security Testing

### Test Password Requirements
- [ ] Can't submit password < 8 chars
- [ ] Requires uppercase, lowercase, number
- [ ] Password field masks input
- [ ] Eye button toggles password visibility
- [ ] Confirm password must match

### Test Data Privacy
- [ ] Email is read-only from Google
- [ ] Phone can be edited by user
- [ ] Form data POSTed, not shown in URL
- [ ] No sensitive data in localStorage
- [ ] Session cookies are httpOnly

### Test CSRF Protection
- [ ] Form has CSRF token (if implemented)
- [ ] Can't submit from external sites
- [ ] Post requests are validated

## Cleanup After Testing

### Delete Test Accounts
```bash
sqlite3 instance/vendorconnect.db

DELETE FROM vendor WHERE email = 'test@gmail.com';
DELETE FROM supplier WHERE email = 'test@gmail.com';
DELETE FROM delivery_agent WHERE email = 'test@gmail.com';
DELETE FROM customer WHERE email = 'test@gmail.com';
```

### Clear Browser Cookies
- Dev Tools → Application → Cookies
- Delete localhost cookies
- Or use incognito mode

## Checklist Summary

**Before Deployment:**
- [ ] Google OAuth credentials created
- [ ] Environment variables set
- [ ] Can sign up as Vendor
- [ ] Can sign up as Supplier
- [ ] Can sign up as Delivery Agent
- [ ] Can sign up as Customer
- [ ] Password validation works
- [ ] Database accounts created correctly
- [ ] Users can login after signup
- [ ] Error pages display nicely
- [ ] Mobile responsive
- [ ] No console errors
- [ ] No server errors in logs

**After Deployment:**
- [ ] Test on production URL
- [ ] Verify redirect URI in Google Console updated
- [ ] Test with production database
- [ ] Monitor error logs for 24 hours
- [ ] Test on actual mobile device

---

**Total Test Time**: ~30 minutes (comprehensive)
**Quick Test Time**: ~5 minutes (happy path only)

Good luck with testing! 🚀
