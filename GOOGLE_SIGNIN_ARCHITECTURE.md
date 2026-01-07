# Google Sign-In Architecture & Flow Diagrams

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        VendorConnect App                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Frontend (Browser)                           │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │  vendor_register.html                             │  │   │
│  │  │  ├─ Login/Signup form fields                      │  │   │
│  │  │  ├─ "Sign up with Google" button                 │  │   │
│  │  │  └─ Points to: /vendor/login/google               │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  │                                                            │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │  signup_complete.html                             │  │   │
│  │  │  ├─ Displays Google data (name, email, phone)    │  │   │
│  │  │  ├─ Role selector (Vendor/Supplier/Agent/Cust)  │  │   │
│  │  │  ├─ Conditional role fields                      │  │   │
│  │  │  ├─ Password validator                           │  │   │
│  │  │  └─ Submit form to: /signup/complete             │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  │                                                            │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │  signup_error.html, login_error.html             │  │   │
│  │  │  ├─ Display error messages                        │  │   │
│  │  │  └─ Helpful action buttons                        │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                           ↓                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Backend (Flask Routes)                       │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │  @app.route('/vendor/register')                  │  │   │
│  │  │  └─ Render vendor_register.html                  │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  │                                                            │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │  @app.route('/vendor/login/google')              │  │   │
│  │  │  ├─ Check OAuth client configured                │  │   │
│  │  │  ├─ Set session['oauth_next'] if present         │  │   │
│  │  │  └─ oauth.google.authorize_redirect()            │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  │                                                            │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │  @app.route('/vendor/login/google/callback')     │  │   │
│  │  │  ├─ Get access token from Google                  │  │   │
│  │  │  ├─ Fetch user info (name, email, phone)         │  │   │
│  │  │  ├─ Check if email exists                         │  │   │
│  │  │  ├─ If exists: Set session → redirect dashboard │  │   │
│  │  │  └─ If new: Store in session → /signup/complete │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  │                                                            │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │  @app.route('/signup/complete')                  │  │   │
│  │  │  ├─ GET: Render form with session data           │  │   │
│  │  │  ├─ POST: Validate & create user                 │  │   │
│  │  │  ├─ Check email/phone uniqueness                 │  │   │
│  │  │  ├─ Create user (role-based)                     │  │   │
│  │  │  ├─ Generate JWT & session                       │  │   │
│  │  │  └─ Redirect to dashboard                        │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                           ↓                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Database (SQLite)                            │   │
│  │  ├─ vendor (id, name, email, phone, gstin, etc)         │   │
│  │  ├─ supplier (id, name, email, phone, gstin, etc)       │   │
│  │  ├─ delivery_agent (id, name, email, phone, vehicle)    │   │
│  │  └─ customer (id, name, email, phone, location)         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                           ↓                                      │
└─────────────────────────────────────────────────────────────────┘
                           ↓
       ┌───────────────────────────────────┐
       │    Google OAuth Services          │
       │  (accounts.google.com)            │
       │  ├─ OAuth2 login                  │
       │  ├─ Access token exchange         │
       │  ├─ User info endpoint            │
       │  └─ Profile data retrieval        │
       └───────────────────────────────────┘
```

## Complete OAuth Flow Diagram

```
┌─────────────┐                                    ┌──────────────┐
│   Browser   │                                    │  VendorApp   │
└──────┬──────┘                                    └──────┬───────┘
       │                                                   │
       │ 1. Click "Sign up with Google"                   │
       ├──────────────────────────────────────────────────>│
       │                                                   │
       │ 2. Redirect to Google OAuth                      │
       │<─────────────────────────────────────────────────┤
       │ (Go to: accounts.google.com)                    │
       │                                                   │
       ↓                                                   ↓
┌──────────────────┐                         ┌────────────────────┐
│  Google Login    │                         │   VendorApp        │
│  (User logs in)  │                         │  (Waiting for      │
│                  │                         │   callback)        │
└────────┬─────────┘                         └────────┬───────────┘
         │                                            │
         │ 3. User authenticates                      │
         │ (enters Gmail credentials)                 │
         │                                            │
         │ 4. Redirect to /vendor/login/google/callback
         ├────────────────────────────────────────────>│
         │    (with authorization code)               │
         │                                            │
         │ 5. Exchange code for access token          │
         │<────────────────────────────────────────────┤
         │    (backend to Google API)                 │
         │                                            │
         │ 6. Get user info from Google               │
         │<────────────────────────────────────────────┤
         │    (name, email, phone, picture)           │
         │                                            │
         │ 7. Return to browser                       │
         │<────────────────────────────────────────────┤
         │    (redirect to /signup/complete or        │
         │     dashboard)                             │
         │                                            │
         ↓                                            ↓
    ┌─────────────────────────────────────────────────────────┐
    │  Now on /signup/complete (if new user)                  │
    │  or on /dashboard (if existing user)                    │
    └─────────────────────────────────────────────────────────┘
```

## New User Signup Flow

```
START
  │
  ├─> User clicks "Sign up with Google"
  │     │
  │     ├─> /vendor/login/google
  │     │     └─> oauth.google.authorize_redirect()
  │     │
  │     ├─> [GOOGLE LOGIN PAGE]
  │     │     └─> User enters Gmail credentials
  │     │
  │     ├─> /vendor/login/google/callback
  │     │     ├─> Get access token
  │     │     ├─> oauth.google.get('userinfo')
  │     │     ├─> Extract: email, name, phone
  │     │     │
  │     │     ├─> Query: Does email exist?
  │     │     │     │
  │     │     │     └─> NO ✓ (New user)
  │     │     │
  │     │     └─> Store in session['oauth_user_data']
  │     │
  │     ├─> /signup/complete (GET)
  │     │     ├─> Render form with session data
  │     │     │   ├─ Email: bob@gmail.com (read-only)
  │     │     │   ├─ Name: Bob Smith (editable)
  │     │     │   ├─ Phone: +1234567890 (editable)
  │     │     │   └─ Role selector
  │     │     │
  │     │     └─> User fills form
  │     │         ├─ Selects role (e.g., "Vendor")
  │     │         ├─ Conditional fields appear
  │     │         │  ├─ Business Type
  │     │         │  └─ GSTIN
  │     │         ├─ Enters location
  │     │         └─ Sets password
  │     │
  │     ├─> /signup/complete (POST)
  │     │     ├─> Validate inputs
  │     │     ├─> Check email/phone unique
  │     │     ├─> Hash password
  │     │     ├─ CREATE: vendor record
  │     │     │     ├─ name: "Bob Smith"
  │     │     │     ├─ email: "bob@gmail.com"
  │     │     │     ├─ phone: "+1234567890"
  │     │     │     ├─ gstin: "27AABCH1234A1Z0"
  │     │     │     ├─ business_type: "chaat"
  │     │     │     ├─ location: "Mumbai"
  │     │     │     └─ password_hash: (hashed)
  │     │     ├─> Set session['vendor_id'] = user.id
  │     │     ├─> Generate JWT token
  │     │     ├─> Set cookie with JWT
  │     │     └─> Redirect to /vendor/dashboard
  │     │
  │     └─> /vendor/dashboard
  │           └─> User logged in & dashboard loads
  │
  └─> END ✓ (Account created, user logged in)
```

## Existing User Login Flow

```
START
  │
  ├─> User clicks "Sign up with Google"
  │     │
  │     ├─> /vendor/login/google
  │     │     └─> oauth.google.authorize_redirect()
  │     │
  │     ├─> [GOOGLE LOGIN PAGE]
  │     │     └─> User enters Gmail credentials
  │     │
  │     ├─> /vendor/login/google/callback
  │     │     ├─> Get access token
  │     │     ├─> oauth.google.get('userinfo')
  │     │     ├─> Extract: email, name, phone
  │     │     │
  │     │     ├─> Query: Does email exist?
  │     │     │     │
  │     │     │     └─> YES ✓ (Existing user)
  │     │     │
  │     │     ├─> Fetch user from DB
  │     │     ├─> Set session['vendor_id'] = user.id
  │     │     ├─> Generate JWT token
  │     │     ├─> Set cookie with JWT
  │     │     └─> Redirect to /vendor/dashboard
  │     │
  │     └─> /vendor/dashboard
  │           └─> User logged in & dashboard loads
  │
  └─> END ✓ (User logged in directly, no signup form)
```

## Error Flow Diagram

```
START
  │
  ├─> /vendor/login/google
  │     │
  │     ├─> ERROR: Google OAuth not configured?
  │     │     └─> Return error page with config details
  │     │
  │     ├─> ERROR: authorize_redirect fails?
  │     │     └─> Log exception & return error
  │
  ├─> /vendor/login/google/callback
  │     │
  │     ├─> ERROR: authorize_access_token fails?
  │     │     └─> login_error.html (Authorization failed)
  │     │
  │     ├─> ERROR: Can't fetch userinfo?
  │     │     └─> login_error.html (Failed to fetch user info)
  │     │
  │     ├─> ERROR: No email from Google?
  │     │     └─> login_error.html (Google account has no email)
  │
  ├─> /signup/complete (GET)
  │     │
  │     ├─> ERROR: No session data?
  │     │     └─> signup_error.html (Session expired)
  │
  ├─> /signup/complete (POST)
  │     │
  │     ├─> ERROR: Invalid name?
  │     │     └─> JSON error (Please enter a valid name)
  │     │
  │     ├─> ERROR: Invalid phone?
  │     │     └─> JSON error (Please enter valid phone)
  │     │
  │     ├─> ERROR: Invalid password?
  │     │     └─> JSON error (Password must be 8+ chars)
  │     │
  │     ├─> ERROR: Email already exists?
  │     │     └─> JSON error (409 Conflict)
  │     │
  │     ├─> ERROR: Phone already exists?
  │     │     └─> JSON error (409 Conflict)
  │     │
  │     ├─> ERROR: Vendor GSTIN required?
  │     │     └─> JSON error (GSTIN is required for vendors)
  │     │
  │     ├─> ERROR: Database error?
  │     │     └─> signup_error.html (An unexpected error occurred)
  │
  └─> END with error handling ✓
```

## Database Schema Relationships

```
┌─────────────────────────┐
│       VENDOR            │
├─────────────────────────┤
│ id (PK)                 │
│ name ────────────────┐  │
│ phone                │  │
│ email ◄──────────────┤─────────┐
│ location             │  │       │
│ business_type        │  │       │
│ gstin                │  │       │
│ password_hash        │  │       │
│ created_at           │  │       │
└─────────────────────────┘       │
                                  │
                            Used for:
                            - Duplicate check
                            - Login verification
                            - Profile lookup
                                  │
┌─────────────────────────┐       │
│      SUPPLIER           │       │
├─────────────────────────┤       │
│ id (PK)                 │       │
│ name                    │       │
│ phone                   │       │
│ email ◄─────────────────┼───────┤
│ location                │       │
│ business_name           │       │
│ gstin                   │       │
│ password_hash           │       │
│ created_at              │       │
└─────────────────────────┘       │
                                  │
┌─────────────────────────┐       │
│   DELIVERY_AGENT        │       │
├─────────────────────────┤       │
│ id (PK)                 │       │
│ name                    │       │
│ phone                   │       │
│ email ◄─────────────────┼───────┤
│ location                │       │
│ vehicle_type            │       │
│ vehicle_info            │       │
│ password_hash           │       │
│ created_at              │       │
└─────────────────────────┘       │
                                  │
┌─────────────────────────┐       │
│      CUSTOMER           │       │
├─────────────────────────┤       │
│ id (PK)                 │       │
│ name                    │       │
│ phone                   │       │
│ email ◄─────────────────┴───────┤
│ location                        │
│ password_hash                   │
│ created_at                      │
└─────────────────────────┘       │
                                  │
                            Unique emails prevent:
                            ✓ Duplicate registration
                            ✓ Same email in multiple roles
                            ✓ Account takeover
```

## Password Validation Flow

```
User types password
  │
  ├─> Update event listener
  │     │
  │     ├─> Check: length >= 8?
  │     │     └─> .met / .unmet class
  │     │
  │     ├─> Check: has uppercase [A-Z]?
  │     │     └─> .met / .unmet class
  │     │
  │     ├─> Check: has lowercase [a-z]?
  │     │     └─> .met / .unmet class
  │     │
  │     ├─> Check: has number [0-9]?
  │     │     └─> .met / .unmet class
  │     │
  │     └─> Display real-time feedback
  │
  ├─> Form submission attempt
  │     │
  │     ├─> Check: password == confirm_password?
  │     │     ├─> YES ✓ → Continue
  │     │     └─> NO ✗ → Show error
  │     │
  │     ├─> Check: all requirements met?
  │     │     ├─> YES ✓ → Proceed
  │     │     └─> NO ✗ → Show error
  │     │
  │     └─> Backend validation on POST
  │           ├─> Check length >= 8
  │           ├─> Check not empty
  │           └─> Hash with werkzeug
  │
  └─> END
```

## Role Selection & Conditional Fields

```
User selects role from dropdown
  │
  ├─> Vendor selected?
  │     ├─> Show: Business Type dropdown
  │     ├─> Show: GSTIN input field
  │     └─> Mark as: REQUIRED ✓
  │
  ├─> Supplier selected?
  │     ├─> Show: Business Name input
  │     ├─> Show: GSTIN input (optional)
  │     ├─> Show: Categories input
  │     └─> Mark GSTIN as: OPTIONAL
  │     └─> Mark Categories as: REQUIRED ✓
  │
  ├─> Delivery Agent selected?
  │     ├─> Show: Vehicle Type dropdown
  │     ├─> Show: Vehicle Registration input
  │     └─> Mark both as: REQUIRED ✓
  │
  ├─> Customer selected?
  │     ├─> Show: Nothing extra
  │     └─> All fields already visible
  │
  └─> END - Form ready for input
```

## Session & Token Management

```
After successful signup/login:

┌──────────────────────┐
│  Session Object      │
├──────────────────────┤
│ session['vendor_id'] │ = 123
│   or                 │
│ session['supplier']  │ = 456
│ session['delivery']  │ = 789
│ session['customer']  │ = 101112
│                      │
│ Expires: When        │
│ browser closes or    │
│ logout clicked       │
└──────────────────────┘
         │
         │ JWT Token Created
         │ 
         ├─> payload = {
         │   'user_id': 123,
         │   'role': 'vendor',
         │   'email': 'bob@gmail.com',
         │   'exp': 1704873600
         │ }
         │
         ├─> Encoded with: SECRET_KEY
         │
         ├─> Stored in: httpOnly cookie
         │   (Can't access via JavaScript)
         │
         └─> Verified on: Protected routes
```

---

**Diagram Version**: 1.0
**Last Updated**: January 7, 2026
**All diagrams are ASCII art for terminal compatibility**
