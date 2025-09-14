#!/usr/bin/env python3
"""
Quick fix script for email configuration
This will help you set up email credentials quickly
"""

import os
import sys

def main():
    print("🔧 Quick Email Fix for VendorConnect")
    print("=" * 50)
    print()
    
    print("📧 Current Issue: OTP emails are failing to send")
    print("🔍 Root Cause: Gmail credentials not properly configured")
    print()
    
    print("🎯 Solution Options:")
    print("1. Use hackathongoo@gmail.com (if you have access)")
    print("2. Use your own Gmail account")
    print("3. Use a different email provider")
    print()
    
    choice = input("Choose option (1/2/3): ").strip()
    
    if choice == "1":
        setup_hackathongoo()
    elif choice == "2":
        setup_own_gmail()
    elif choice == "3":
        setup_other_provider()
    else:
        print("❌ Invalid choice. Please run the script again.")
        return
    
    print("\n🧪 Testing email configuration...")
    test_email()

def setup_hackathongoo():
    print("\n📧 Setting up hackathongoo@gmail.com")
    print("=" * 40)
    
    print("📋 Prerequisites:")
    print("1. Access to hackathongoo@gmail.com")
    print("2. 2-Factor Authentication enabled")
    print("3. App Password generated")
    print()
    
    app_password = input("Enter 16-character App Password: ").strip()
    
    if len(app_password.replace(' ', '')) != 16:
        print("❌ Invalid App Password length. Please try again.")
        return
    
    # Update email_config.py
    config_content = f"""# Email Configuration for VendorConnect
# Update these values with the correct credentials

# Gmail SMTP Configuration
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True

# Email Credentials - UPDATE THESE VALUES
MAIL_USERNAME = 'hackathongoo@gmail.com'
MAIL_PASSWORD = '{app_password.replace(' ', '')}'  # App Password

# Test Configuration
TEST_EMAIL = 'askotal07@gmail.com'  # Email to test with
"""
    
    try:
        with open('email_config.py', 'w') as f:
            f.write(config_content)
        print("✅ email_config.py updated successfully!")
    except Exception as e:
        print(f"❌ Error updating config: {e}")

def setup_own_gmail():
    print("\n📧 Setting up your own Gmail account")
    print("=" * 40)
    
    email = input("Enter your Gmail address: ").strip()
    app_password = input("Enter 16-character App Password: ").strip()
    
    if len(app_password.replace(' ', '')) != 16:
        print("❌ Invalid App Password length. Please try again.")
        return
    
    # Update email_config.py
    config_content = f"""# Email Configuration for VendorConnect
# Update these values with the correct credentials

# Gmail SMTP Configuration
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True

# Email Credentials - UPDATE THESE VALUES
MAIL_USERNAME = '{email}'
MAIL_PASSWORD = '{app_password.replace(' ', '')}'  # App Password

# Test Configuration
TEST_EMAIL = 'askotal07@gmail.com'  # Email to test with
"""
    
    try:
        with open('email_config.py', 'w') as f:
            f.write(config_content)
        print("✅ email_config.py updated successfully!")
    except Exception as e:
        print(f"❌ Error updating config: {e}")

def setup_other_provider():
    print("\n📧 Setting up other email provider")
    print("=" * 40)
    print("This requires manual configuration in email_config.py")
    print("Please edit the file manually with your email provider settings.")

def test_email():
    try:
        # Import the test function
        from test_email import send_test_email, generate_otp
        import random
        import string
        
        test_email = input("Enter email to test (or press Enter for askotal07@gmail.com): ").strip()
        if not test_email:
            test_email = "askotal07@gmail.com"
        
        otp = generate_otp()
        print(f"\n📧 Sending test email to: {test_email}")
        print(f"🔑 Test OTP: {otp}")
        
        success = send_test_email(test_email, otp)
        
        if success:
            print("✅ Email sent successfully!")
            print("🎉 Email configuration is working!")
            print("✅ You can now use the forgot password feature.")
        else:
            print("❌ Email failed to send.")
            print("💡 Please check your credentials and try again.")
            
    except Exception as e:
        print(f"❌ Error testing email: {e}")

if __name__ == "__main__":
    main()
