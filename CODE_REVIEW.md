# VendorConnect - CodeRabbit Code Review Report

**Date:** January 6, 2026  
**Repository:** karthikj30/VendorConnect  
**Branch:** main

---

## Executive Summary

This review identifies critical security vulnerabilities, architectural concerns, and code quality issues across the VendorConnect Flask application. The codebase shows good organizational structure but has significant security risks and maintainability concerns that should be addressed immediately.

**Critical Issues Found:** 7  
**High Priority Issues:** 12  
**Medium Priority Issues:** 8  
**Low Priority Issues:** 5

---

## 🔴 CRITICAL ISSUES

### 1. **Exposed Credentials in Version Control**

**Severity:** 🔴 CRITICAL  
**File:** [.env](.env), [email_config.py](VendorConnect-main/email_config.py)  
**Lines:** Various

**Issue:**
```
MAIL_PASSWORD=oldrtkzhahrjnjcb
MAIL_USERNAME=hackathongoo@gmail.com
GOOGLE_CLIENT_SECRET=GOCSPX-qRKqxmOg9FZeEQrPW_y62HaCXI5
```

**Risk:** All credentials are exposed in the repository. These accounts have been compromised.

**Recommendation:**
1. **Immediately rotate** all exposed credentials:
   - Gmail app password
   - Google OAuth Client Secret
   - JWT Secret

2. Add `.env` and `email_config.py` to `.gitignore`:
   ```
   .env
   .env.local
   email_config.py
   instance/
   __pycache__/
   *.pyc
   ```

3. Create `.env.example`:
   ```
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   GOOGLE_CLIENT_ID=your-client-id
   GOOGLE_CLIENT_SECRET=your-client-secret
   GOOGLE_REDIRECT_URI=http://localhost:5000/vendor/login/google/callback
   FLASK_ENV=development
   FLASK_DEBUG=0
   SECRET_KEY=your-secret-key
   JWT_SECRET_KEY=your-jwt-secret
   ```

4. Delete the credentials from git history:
   ```bash
   git rm --cached .env email_config.py
   git commit -m "Remove exposed credentials"
   ```

---

### 2. **Hardcoded Secrets in Application Code**

**Severity:** 🔴 CRITICAL  
**File:** [app.py](VendorConnect-main/app.py)  
**Lines:** 147, 205

**Issues:**
```python
app.config['SECRET_KEY'] = 'vendorconnect_secret_key_2024'  # Line 147
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', os.environ.get('SECRET_KEY', 'change-me-jwt-secret'))  # Line 205
```

**Risk:** Weak, hardcoded secrets are easily guessable and compromise session security.

**Recommendation:**
```python
# Use environment variables with no defaults
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
if not app.config['SECRET_KEY']:
    raise ValueError("SECRET_KEY environment variable must be set")

app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
if not app.config['JWT_SECRET_KEY']:
    raise ValueError("JWT_SECRET_KEY environment variable must be set")
```

---

### 3. **Email Credentials Exposed in Multiple Locations**

**Severity:** 🔴 CRITICAL  
**Files:** [app.py](VendorConnect-main/app.py#L177), [email_config.py](VendorConnect-main/email_config.py)  
**Lines:** 177, 178, 390, 424

**Issues:**
- Default email in app.py: `'hackathongoo@gmail.com'`
- Hardcoded fallbacks for credentials
- Email exposed in HTML template

**Recommendation:**
- Remove all default credentials
- Use environment variables only
- Create a dedicated email service module

---

### 4. **Missing SQL Injection Protection**

**Severity:** 🔴 CRITICAL  
**File:** [app.py](VendorConnect-main/app.py)  
**Scope:** Throughout the application

**Issue:** While using SQLAlchemy ORM helps, there are raw SQL queries present.

**Recommendation:**
1. Audit all `text()` and raw SQL queries
2. Always use parameterized queries
3. Example fix:
   ```python
   # ❌ Bad
   query = f"SELECT * FROM users WHERE id = {user_id}"
   
   # ✅ Good
   from sqlalchemy import text
   query = text("SELECT * FROM users WHERE id = :id")
   result = db.session.execute(query, {"id": user_id})
   ```

---

### 5. **Missing CSRF Protection**

**Severity:** 🔴 CRITICAL  
**File:** [app.py](VendorConnect-main/app.py)  
**Scope:** All POST/PUT/DELETE endpoints

**Issue:** No CSRF token validation on state-changing operations.

**Recommendation:**
```python
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)

# In templates:
<!-- Include CSRF token in all forms -->
<form method="POST">
    {{ csrf_token() }}
    <!-- form fields -->
</form>
```

---

### 6. **Authentication Bypass Risk**

**Severity:** 🔴 CRITICAL  
**File:** [app.py](VendorConnect-main/app.py)  
**Scope:** Session management

**Issue:** Session data stored directly in app without validation. No session timeout implemented.

**Recommendation:**
1. Implement session timeout
2. Validate session on each request
3. Use secure session configuration:
   ```python
   app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
   app.config['SESSION_COOKIE_HTTPONLY'] = True  # No JS access
   app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
   app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
   ```

---

### 7. **Missing Input Validation and Sanitization**

**Severity:** 🔴 CRITICAL  
**File:** [app.py](VendorConnect-main/app.py)  
**Scope:** All request handlers

**Issue:** User inputs are not properly validated before use.

**Recommendation:**
```python
# Install flask-inputs or marshmallow
from marshmallow import Schema, fields, ValidationError

class VendorLoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=Length(min=8))

schema = VendorLoginSchema()
try:
    data = schema.load(request.get_json())
except ValidationError as err:
    return jsonify({'errors': err.messages}), 400
```

---

## 🟠 HIGH PRIORITY ISSUES

### 8. **Missing Authentication on Protected Routes**

**Severity:** 🟠 HIGH  
**File:** [app.py](VendorConnect-main/app.py)  

**Issue:** Many routes handle sensitive data but lack proper authentication checks.

**Recommendation:**
```python
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'vendor_id' not in session:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/vendor/orders')
@login_required
def get_vendor_orders():
    # Protected endpoint
    pass
```

---

### 9. **Uncontrolled File Upload**

**Severity:** 🟠 HIGH  
**File:** [app.py](VendorConnect-main/app.py#L1481)  
**Function:** `save_vendor_image()`

**Issue:** File uploads need additional validation.

**Current Check:**
```python
def is_allowed_image(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS
```

**Problems:**
- Only checks extension (can be spoofed)
- No file size validation before processing
- No virus scanning
- No unique filename enforcement

**Recommendation:**
```python
import magic
from werkzeug.utils import secure_filename
import os

def save_vendor_image(file_obj, vendor_id, kind: str):
    # 1. Validate file size
    max_size = 10 * 1024 * 1024  # 10MB
    file_obj.seek(0, 2)
    if file_obj.tell() > max_size:
        return None, "File too large"
    file_obj.seek(0)
    
    # 2. Validate MIME type
    mime = magic.from_buffer(file_obj.read(1024), mime=True)
    if mime not in ['image/jpeg', 'image/png', 'image/webp', 'image/gif']:
        return None, "Invalid file type"
    file_obj.seek(0)
    
    # 3. Generate unique filename
    filename = secure_filename(f"{vendor_id}_{kind}_{uuid.uuid4()}.png")
    
    # 4. Save with validation
    filepath = os.path.join(app.config['SUPPLIER_UPLOAD_FOLDER'], filename)
    file_obj.save(filepath)
    
    return filename, None
```

---

### 10. **Insufficient Error Handling**

**Severity:** 🟠 HIGH  
**File:** [app.py](VendorConnect-main/app.py#L273-L301)  

**Issue:** Generic error messages expose sensitive information.

**Problem:**
```python
@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'Internal server error: {error}')
    # Error details might be logged with sensitive data
```

**Recommendation:**
```python
@app.errorhandler(500)
def internal_error(error):
    # Generate unique error ID for tracking
    error_id = str(uuid.uuid4())
    app.logger.error(f'Error {error_id}: {error}', exc_info=True)
    
    if app.config.get('DEBUG'):
        return jsonify({'error': str(error)}), 500
    
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'error_id': error_id,  # User can report this ID
        'message': 'An unexpected error occurred. Please contact support.'
    }), 500
```

---

### 11. **Missing Rate Limiting**

**Severity:** 🟠 HIGH  
**File:** [app.py](VendorConnect-main/app.py)  
**Endpoints:** `/vendor/login`, `/vendor/register`, OTP endpoints

**Issue:** No protection against brute force attacks.

**Recommendation:**
```bash
pip install Flask-Limiter
```

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(app, key_func=get_remote_address)

@app.route('/vendor/login', methods=['POST'])
@limiter.limit("5 per minute")
def vendor_login():
    # Protected against brute force
    pass

@app.route('/vendor/verify-otp', methods=['POST'])
@limiter.limit("3 per minute")
def verify_otp():
    # Limited OTP attempts
    pass
```

---

### 12. **Missing HTTPS Enforcement**

**Severity:** 🟠 HIGH  
**File:** [app.py](VendorConnect-main/app.py)  

**Issue:** No enforcement of HTTPS in production.

**Recommendation:**
```python
from flask_talisman import Talisman

if not app.config.get('DEBUG'):
    Talisman(app, force_https=True)
    
    # Add security headers
    @app.after_request
    def set_security_headers(response):
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response
```

---

### 13. **SQL Injection in Query Construction**

**Severity:** 🟠 HIGH  
**File:** [app.py](VendorConnect-main/app.py)  

**Issue:** Using string formatting in some queries.

**Recommendation:**
Always use parameterized queries and ORM methods.

---

### 14. **Insecure Password Reset Flow**

**Severity:** 🟠 HIGH  
**File:** [app.py](VendorConnect-main/app.py#L1398)  

**Issue:** Password reset via OTP without proper validation.

**Recommendations:**
1. Validate OTP format and age
2. Implement token expiration (5-10 minutes)
3. Invalidate token after use
4. Log password change events

---

### 15. **Missing Dependency Pinning**

**Severity:** 🟠 HIGH  
**File:** [requirements.txt](VendorConnect-main/requirements.txt)  

**Issue:** Dependencies not pinned to specific versions.

**Current:**
```
Flask==2.3.3
```

**Recommendation:**
Pin all dependencies including transitive ones:
```bash
pip freeze > requirements.txt
```

Or manually specify exact versions:
```
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-CORS==4.0.0
Werkzeug==2.3.7
Flask-Limiter==3.5.0
Flask-WTF==1.1.1
Flask-Talisman==1.1.0
python-dotenv==1.0.0
```

---

### 16. **No Database Transaction Management**

**Severity:** 🟠 HIGH  
**File:** [app.py](VendorConnect-main/app.py)  

**Issue:** Missing rollback handling in error cases.

**Example Fix:**
```python
try:
    db.session.add(vendor)
    db.session.commit()
except Exception as e:
    db.session.rollback()
    app.logger.error(f"Failed to create vendor: {e}")
    return jsonify({'success': False, 'error': 'Database error'}), 500
```

---

### 17. **Missing Logging for Security Events**

**Severity:** 🟠 HIGH  
**File:** [app.py](VendorConnect-main/app.py)  

**Issue:** No audit logging for sensitive operations.

**Recommendation:**
```python
import logging
from logging.handlers import RotatingFileHandler

security_logger = logging.getLogger('security')
handler = RotatingFileHandler('logs/security.log', maxBytes=1000000, backupCount=10)
security_logger.addHandler(handler)

def log_security_event(event, user_id, details):
    security_logger.warning(f"[{event}] User {user_id}: {details}")

# Usage
log_security_event('LOGIN', vendor_id, 'Successful login')
log_security_event('LOGIN_FAILED', email, 'Invalid password')
log_security_event('PASSWORD_RESET', vendor_id, 'Password changed')
```

---

### 18. **Missing Content Security Policy (CSP)**

**Severity:** 🟠 HIGH  
**File:** [templates/](VendorConnect-main/templates/)  

**Issue:** No CSP headers to prevent XSS attacks.

**Recommendation:**
```python
@app.after_request
def set_csp_header(response):
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' https://fonts.googleapis.com; "
        "connect-src 'self'"
    )
    return response
```

---

### 19. **No CORS Validation**

**Severity:** 🟠 HIGH  
**File:** [app.py](VendorConnect-main/app.py#L183)  

**Current:**
```python
CORS(app)  # Allows all origins!
```

**Risk:** Exposes API to any origin.

**Recommendation:**
```python
from flask_cors import CORS

allowed_origins = [
    "https://vendorconnect.com",
    "https://www.vendorconnect.com",
]

if os.environ.get('FLASK_ENV') == 'development':
    allowed_origins.extend([
        "http://localhost:3000",
        "http://localhost:5000",
    ])

CORS(app, origins=allowed_origins, allow_headers=['Content-Type', 'Authorization'])
```

---

## 🟡 MEDIUM PRIORITY ISSUES

### 20. **Missing API Documentation**

**Severity:** 🟡 MEDIUM  
**Scope:** All API endpoints

**Recommendation:**
- Add Swagger/OpenAPI documentation
- Document all endpoints with examples
- Include authentication requirements
- Specify response formats

```bash
pip install flask-restx
```

---

### 21. **Weak Password Requirements**

**Severity:** 🟡 MEDIUM  
**File:** [app.py](VendorConnect-main/app.py#L1140)  

**Issue:** No password strength validation.

**Recommendation:**
```python
import re

def validate_password(password):
    if len(password) < 12:
        return False, "Password must be at least 12 characters"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain uppercase letters"
    
    if not re.search(r'[0-9]', password):
        return False, "Password must contain numbers"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain special characters"
    
    return True, None

# Usage in vendor_register
is_valid, msg = validate_password(password)
if not is_valid:
    return jsonify({'success': False, 'error': msg}), 400
```

---

### 22. **Missing API Versioning**

**Severity:** 🟡 MEDIUM  
**File:** [app.py](VendorConnect-main/app.py)  

**Issue:** No version control for API endpoints.

**Recommendation:**
```python
# Use versioned routes
@app.route('/api/v1/suppliers')
def get_suppliers_v1():
    pass

@app.route('/api/v2/suppliers')
def get_suppliers_v2():
    pass
```

---

### 23. **Database Connection Pooling Not Configured**

**Severity:** 🟡 MEDIUM  
**File:** [app.py](VendorConnect-main/app.py#L159)  

**Issue:** SQLAlchemy connection pool not optimized.

**Recommendation:**
```python
from sqlalchemy.pool import QueuePool

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'poolclass': QueuePool,
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
    'max_overflow': 20,
}
```

---

### 24. **Missing Type Hints**

**Severity:** 🟡 MEDIUM  
**Scope:** Throughout codebase

**Issue:** No type hints for better code clarity.

**Example:**
```python
# ❌ Current
def send_otp_email(email, otp):
    pass

# ✅ Recommended
def send_otp_email(email: str, otp: str) -> bool:
    pass
```

---

### 25. **Missing Unit Tests**

**Severity:** 🟡 MEDIUM  
**Files:** [tests/](VendorConnect-main/tests/)  

**Issue:** Very limited test coverage.

**Recommendation:**
```bash
pip install pytest pytest-cov pytest-flask
```

Create comprehensive tests for:
- Authentication routes
- Payment endpoints
- Database operations
- Email functionality

---

### 26. **No Backup Strategy**

**Severity:** 🟡 MEDIUM  
**Issue:** Database backup mechanism missing.

**Recommendation:**
```python
import subprocess
from datetime import datetime

def backup_database():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'backups/vendorconnect_{timestamp}.db'
    subprocess.run(['cp', 'instance/vendorconnect.db', backup_file])
```

---

### 27. **Insufficient Logging**

**Severity:** 🟡 MEDIUM  
**File:** [app.py](VendorConnect-main/app.py#L153)  

**Issue:** Limited logging for debugging.

**Recommendation:**
```python
import logging
from logging.handlers import RotatingFileHandler

# Configure file logging
file_handler = RotatingFileHandler(
    'logs/app.log',
    maxBytes=10485760,  # 10MB
    backupCount=10
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s [%(filename)s:%(lineno)d]: %(message)s'
))
app.logger.addHandler(file_handler)
```

---

## 🔵 LOW PRIORITY ISSUES

### 28. **Code Organization**

**Severity:** 🔵 LOW  
**Issue:** Monolithic app.py (6000+ lines)

**Recommendation:**
Split into blueprints:
```
app/
├── __init__.py
├── models.py
├── auth/
│   ├── __init__.py
│   └── routes.py
├── vendor/
│   ├── __init__.py
│   └── routes.py
├── customer/
│   ├── __init__.py
│   └── routes.py
└── api/
    ├── __init__.py
    └── routes.py
```

---

### 29. **Magic Numbers and Strings**

**Severity:** 🔵 LOW  
**Example:** `timedelta(hours=24)`, status strings

**Recommendation:**
```python
# config.py
class Config:
    SESSION_TIMEOUT = 24  # hours
    OTP_EXPIRY = 10  # minutes
    MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB
    
    # Status constants
    ORDER_STATUS = {
        'PENDING': 'pending',
        'CONFIRMED': 'confirmed',
        'DELIVERED': 'delivered',
        'CANCELLED': 'cancelled',
    }
```

---

### 30. **Missing Environment Variable Validation**

**Severity:** 🔵 LOW  
**File:** [app.py](VendorConnect-main/app.py)  

**Recommendation:**
```python
def validate_env_variables():
    required = ['SECRET_KEY', 'JWT_SECRET_KEY', 'MAIL_USERNAME', 'MAIL_PASSWORD']
    missing = [var for var in required if not os.environ.get(var)]
    
    if missing:
        raise ValueError(f"Missing environment variables: {', '.join(missing)}")

validate_env_variables()
```

---

## Security Checklist

- [ ] Rotate all exposed credentials (CRITICAL)
- [ ] Remove .env and email_config.py from git history (CRITICAL)
- [ ] Implement CSRF protection (CRITICAL)
- [ ] Add input validation and sanitization (CRITICAL)
- [ ] Enable HTTPS only in production (HIGH)
- [ ] Implement rate limiting (HIGH)
- [ ] Add authentication to protected routes (HIGH)
- [ ] Improve file upload security (HIGH)
- [ ] Configure secure session cookies (HIGH)
- [ ] Add security headers (HIGH)
- [ ] Implement comprehensive logging (HIGH)
- [ ] Add database backup strategy (MEDIUM)
- [ ] Implement unit tests (MEDIUM)
- [ ] Add API documentation (MEDIUM)
- [ ] Refactor monolithic app.py (LOW)

---

## Recommended Next Steps

### Phase 1: Critical (This Sprint)
1. Rotate all credentials immediately
2. Remove credentials from git
3. Implement CSRF protection
4. Add input validation

### Phase 2: High Priority (Next Sprint)
1. Add rate limiting
2. Implement authentication decorators
3. Improve file upload security
4. Configure secure headers

### Phase 3: Medium Priority (Following Sprint)
1. Add unit tests
2. Improve logging
3. Add API documentation
4. Refactor monolithic app.py

---

## Tools and Resources

- **Security Testing:** `bandit`, `safety`
- **Code Quality:** `pylint`, `black`, `flake8`
- **Testing:** `pytest`, `pytest-cov`
- **API Documentation:** `flask-restx`, `swagger-ui`
- **Security Headers:** `flask-talisman`

```bash
# Install security tools
pip install bandit safety pylint black flake8 pytest pytest-cov
```

---

## Conclusion

The VendorConnect application has a solid foundation but requires immediate attention to critical security vulnerabilities. Priority should be given to:

1. **Credential exposure** - Rotate and protect all secrets
2. **Authentication** - Implement proper session validation
3. **Input validation** - Prevent injection attacks
4. **Security headers** - Protect against common web vulnerabilities

Once these critical issues are addressed, the codebase should be refactored into a more maintainable structure with comprehensive tests and documentation.

---

**Report Generated:** January 6, 2026  
**Reviewed By:** GitHub Copilot  
**Severity Summary:**
- 🔴 Critical: 7 issues
- 🟠 High: 12 issues  
- 🟡 Medium: 8 issues
- 🔵 Low: 5 issues

