#!/usr/bin/env python3
"""
Quick setup script for email configuration
This script helps you set up the email credentials for hackathongoo@gmail.com
"""

import os
import sys

def setup_email_credentials():
    print("🔧 VendorConnect Email Setup")
    print("=" * 40)
    print("This script will help you configure email credentials for hackathongoo@gmail.com")
    print()
    
    print("📋 Prerequisites:")
    print("1. Access to hackathongoo@gmail.com account")
    print("2. 2-Factor Authentication enabled on the account")
    print("3. App Password generated for 'Mail'")
    print()
    
    # Get app password from user
    app_password = input("Enter the 16-character App Password for hackathongoo@gmail.com: ").strip()
    
    if not app_password or len(app_password.replace(' ', '')) != 16:
        print("❌ Invalid App Password. Please enter a valid 16-character App Password.")
        return False
    
    # Remove spaces from app password
    app_password = app_password.replace(' ', '')
    
    print(f"\n📧 Email Configuration:")
    print(f"   Username: hackathongoo@gmail.com")
    print(f"   Password: {'*' * 16}")
    print(f"   Server: smtp.gmail.com")
    print(f"   Port: 587")
    
    # Set environment variable
    os.environ['MAIL_USERNAME'] = 'hackathongoo@gmail.com'
    os.environ['MAIL_PASSWORD'] = app_password
    
    print(f"\n✅ Environment variables set successfully!")
    print(f"✅ MAIL_USERNAME = hackathongoo@gmail.com")
    print(f"✅ MAIL_PASSWORD = {'*' * 16}")
    
    # Create .env file
    env_content = f"""# VendorConnect Email Configuration
MAIL_USERNAME=hackathongoo@gmail.com
MAIL_PASSWORD={app_password}
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print(f"\n📁 Created .env file with email credentials")
    except Exception as e:
        print(f"\n⚠️  Could not create .env file: {e}")
        print("   You can manually create it with the credentials above")
    
    print(f"\n🎉 Setup complete!")
    print(f"📧 OTP emails will now be sent from hackathongoo@gmail.com")
    print(f"🧪 Run 'python test_email.py' to test the email functionality")
    
    return True

def main():
    try:
        setup_email_credentials()
    except KeyboardInterrupt:
        print(f"\n\n❌ Setup cancelled by user")
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")

if __name__ == "__main__":
    main()
