# 🔧 Fix Email Issue - Step by Step Guide

## 🚨 Current Issue
The OTP email is failing to send because the Gmail credentials are not properly configured.

## ✅ Solution Steps

### Step 1: Access hackathongoo@gmail.com Account
1. Go to [Gmail](https://gmail.com)
2. Sign in with `hackathongoo@gmail.com`
3. If you don't have access, you'll need to:
   - Reset the password, OR
   - Use a different Gmail account that you have access to

### Step 2: Enable 2-Factor Authentication
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Click on "2-Step Verification"
3. Follow the setup process with your phone number
4. Complete the verification

### Step 3: Generate App Password
1. In Google Account Security, go to "App passwords"
2. Select "Mail" as the app
3. Generate a new 16-character password
4. Copy the password (e.g., `abcd efgh ijkl mnop`)

### Step 4: Update Configuration
Open `email_config.py` and replace `YOUR_APP_PASSWORD_HERE` with your actual App Password:

```python
MAIL_PASSWORD = 'abcd efgh ijkl mnop'  # Your actual 16-character password
```

### Step 5: Test Email
Run the test script:
```bash
python test_email.py
```

## 🔄 Alternative: Use Your Own Gmail Account

If you can't access `hackathongoo@gmail.com`, you can use your own Gmail account:

### Option 1: Update email_config.py
```python
MAIL_USERNAME = 'your-email@gmail.com'
MAIL_PASSWORD = 'your-app-password'
```

### Option 2: Update app.py directly
Find this line in `app.py`:
```python
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'hackathongoo@gmail.com')
```
Change it to:
```python
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'your-email@gmail.com')
```

## 🧪 Quick Test

After updating the credentials, test with:
```bash
python test_email.py
```

Enter `askotal07@gmail.com` as the test email address.

## 🎯 Expected Result

You should see:
```
✅ Test email sent successfully!
🎉 SUCCESS! Check your email (askotal07@gmail.com) for the test message.
```

## 🚨 If Still Not Working

1. **Check App Password**: Make sure it's exactly 16 characters
2. **Check 2FA**: Ensure 2-Factor Authentication is enabled
3. **Check Internet**: Make sure you have internet connection
4. **Check Gmail Settings**: Some accounts have additional security restrictions

## 📞 Need Help?

If you're still having issues, you can:
1. Use a different Gmail account that you have full access to
2. Check the Gmail account security settings
3. Try generating a new App Password
4. Make sure the account is not locked or restricted

## 🎉 Once Fixed

After the email is working:
1. Users can register with their email addresses
2. "Forgot Password?" will work properly
3. OTP emails will be sent automatically
4. Users can reset their passwords successfully
