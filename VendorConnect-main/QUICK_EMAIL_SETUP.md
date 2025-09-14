# 🚀 Quick Email Setup for hackathongoo@gmail.com

## ⚡ Quick Start (3 Steps)

### Step 1: Get App Password
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Sign in with `hackathongoo@gmail.com`
3. Enable 2-Factor Authentication if not already enabled
4. Go to "App passwords" → "Mail" → Generate password
5. Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

### Step 2: Run Setup Script
```bash
python setup_email.py
```
Enter the 16-character App Password when prompted.

### Step 3: Test Email
```bash
python test_email.py
```
Enter your email address to receive a test OTP.

## 🎯 That's It!

Your VendorConnect application will now automatically send OTP emails from `hackathongoo@gmail.com` when users request password resets.

## 📧 Email Features

- **Professional Design**: Beautiful HTML email template
- **Security**: OTP expires in 10 minutes
- **Branding**: VendorConnect branding and colors
- **Responsive**: Works on all email clients

## 🔧 Manual Setup (Alternative)

If you prefer to set up manually:

### Option 1: Environment Variables
```bash
# Windows Command Prompt
set MAIL_USERNAME=hackathongoo@gmail.com
set MAIL_PASSWORD=your-16-character-app-password

# Windows PowerShell
$env:MAIL_USERNAME="hackathongoo@gmail.com"
$env:MAIL_PASSWORD="your-16-character-app-password"

# Linux/Mac
export MAIL_USERNAME="hackathongoo@gmail.com"
export MAIL_PASSWORD="your-16-character-app-password"
```

### Option 2: .env File
Create a `.env` file in the project root:
```
MAIL_USERNAME=hackathongoo@gmail.com
MAIL_PASSWORD=your-16-character-app-password
```

### Option 3: Direct in app.py
Update the email configuration in `app.py`:
```python
app.config['MAIL_USERNAME'] = 'hackathongoo@gmail.com'
app.config['MAIL_PASSWORD'] = 'your-16-character-app-password'
```

## 🧪 Testing

1. **Start the application**: `python app.py`
2. **Register a new vendor** with an email address
3. **Go to login page** and click "Forgot Password?"
4. **Enter the email** and check for OTP
5. **Verify the email** looks professional and contains the OTP

## 🚨 Troubleshooting

### Common Issues:

1. **"Authentication failed"**
   - Make sure you're using the App Password, not the regular password
   - Verify 2-Factor Authentication is enabled

2. **"SMTP server error"**
   - Check your internet connection
   - Verify the App Password is correct

3. **"Email not received"**
   - Check spam/junk folder
   - Verify the email address is correct
   - Wait a few minutes for delivery

### Debug Mode:
Add this to `app.py` to see detailed error messages:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📱 Email Preview

The OTP emails will look like this:

```
🍽️ VendorConnect
Street Food Vendor Platform

Password Reset Request

You have requested to reset your password for your VendorConnect account.

Your verification code is:
    123456
    ⏰ Valid for 10 minutes only

⚠️ Security Notice: If you did not request this password reset, 
please ignore this email. Your account remains secure.

This email was sent from hackathongoo@gmail.com
For support, please contact our team.

© 2024 VendorConnect - Empowering Street Food Vendors
Built with ❤️ for India's Street Food Culture
```

## 🎉 Success!

Once set up, users can:
1. Register with their email address
2. Click "Forgot Password?" on login
3. Receive a beautiful OTP email from hackathongoo@gmail.com
4. Enter the OTP and reset their password
5. Login with their new password

The entire process is automated and professional! 🚀
