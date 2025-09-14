# Email Configuration Setup

## Gmail Setup for hackathongoo@gmail.com

The application is configured to send OTP emails from `hackathongoo@gmail.com`. To enable email functionality, you need to configure Gmail SMTP settings:

### Step 1: Access hackathongoo@gmail.com Account
1. Log in to the Gmail account: `hackathongoo@gmail.com`
2. Go to Google Account settings
3. Navigate to Security

### Step 2: Enable 2-Factor Authentication
1. In the Security section, enable 2-Factor Authentication
2. Follow the setup process with a phone number

### Step 3: Generate App Password
1. In Google Account settings, go to Security
2. Under "2-Step Verification", click "App passwords"
3. Select "Mail" as the app
4. Generate a new app password
5. Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

### Step 4: Set Environment Variables
Create a `.env` file in the project root or set environment variables:

```bash
# For Windows (Command Prompt)
set MAIL_USERNAME=hackathongoo@gmail.com
set MAIL_PASSWORD=your-16-character-app-password

# For Windows (PowerShell)
$env:MAIL_USERNAME="hackathongoo@gmail.com"
$env:MAIL_PASSWORD="your-16-character-app-password"

# For Linux/Mac
export MAIL_USERNAME="hackathongoo@gmail.com"
export MAIL_PASSWORD="your-16-character-app-password"
```

### Step 5: Update app.py (Alternative)
If you prefer to hardcode the credentials (not recommended for production):

```python
app.config['MAIL_USERNAME'] = 'hackathongoo@gmail.com'
app.config['MAIL_PASSWORD'] = 'your-16-character-app-password'
```

## Other Email Providers

### Outlook/Hotmail
```python
app.config['MAIL_SERVER'] = 'smtp-mail.outlook.com'
app.config['MAIL_PORT'] = 587
```

### Yahoo
```python
app.config['MAIL_SERVER'] = 'smtp.mail.yahoo.com'
app.config['MAIL_PORT'] = 587
```

## Testing Email Functionality

1. Start the application: `python app.py`
2. Go to the registration page and register with a valid email
3. Go to the login page and click "Forgot Password?"
4. Enter the registered email address
5. Check your email for the OTP
6. Enter the OTP and set a new password

## Troubleshooting

### Common Issues:
1. **Authentication Error**: Make sure you're using an App Password, not your regular password
2. **SMTP Error**: Check your internet connection and firewall settings
3. **Email Not Received**: Check spam folder, verify email address is correct

### Debug Mode:
Add this to your app.py to see detailed error messages:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Security Notes

- Never commit email credentials to version control
- Use environment variables for production
- Consider using a dedicated email service like SendGrid for production
- OTPs expire after 10 minutes for security
