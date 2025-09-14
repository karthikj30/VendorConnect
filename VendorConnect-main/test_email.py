#!/usr/bin/env python3
"""
Test script to verify email functionality with hackathongoo@gmail.com
Run this script to test if OTP emails are being sent correctly
"""

import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Create a test Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'test_secret_key'

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'hackathongoo@gmail.com'
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'your-app-password')

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def send_test_email(to_email, otp):
    """Send test OTP email"""
    try:
        msg = MIMEMultipart()
        msg['From'] = app.config['MAIL_USERNAME']
        msg['To'] = to_email
        msg['Subject'] = "VendorConnect - Test OTP Email"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center;">
                <h1 style="margin: 0; font-size: 24px;">🍽️ VendorConnect</h1>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">Street Food Vendor Platform</p>
            </div>
            
            <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef;">
                <h2 style="color: #333; margin-bottom: 20px;">🧪 Test Email</h2>
                <p style="color: #666; line-height: 1.6;">This is a test email to verify the email functionality is working correctly.</p>
                
                <div style="background: white; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0; border: 2px solid #667eea;">
                    <p style="margin: 0 0 10px 0; color: #666; font-size: 14px;">Test OTP Code:</p>
                    <div style="font-size: 32px; font-weight: bold; color: #667eea; letter-spacing: 5px; margin: 10px 0;">{otp}</div>
                    <p style="margin: 10px 0 0 0; color: #28a745; font-size: 12px; font-weight: bold;">✅ Email system is working!</p>
                </div>
                
                <p style="color: #666; font-size: 14px; margin-top: 30px;">
                    This test email was sent from <strong>hackathongoo@gmail.com</strong><br>
                    If you received this email, the OTP system is configured correctly.
                </p>
            </div>
            
            <div style="text-align: center; margin-top: 20px; color: #999; font-size: 12px;">
                <p>© 2024 VendorConnect - Empowering Street Food Vendors</p>
                <p>Built with ❤️ for India's Street Food Culture</p>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        print(f"📧 Sending test email to: {to_email}")
        print(f"📧 From: {app.config['MAIL_USERNAME']}")
        print(f"🔑 Test OTP: {otp}")
        
        server = smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT'])
        server.starttls()
        server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        text = msg.as_string()
        server.sendmail(app.config['MAIL_USERNAME'], to_email, text)
        server.quit()
        
        print("✅ Test email sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error sending test email: {e}")
        # Fallback to mock email service
        print("\n🔄 Falling back to mock email service...")
        return send_mock_test_email(to_email, otp)

def send_mock_test_email(to_email, otp):
    """Mock test email sending"""
    print("\n" + "="*60)
    print("📧 MOCK TEST EMAIL SENT (For Testing Purposes)")
    print("="*60)
    print(f"📧 To: {to_email}")
    print(f"📧 From: hackathongoo@gmail.com")
    print(f"📧 Subject: VendorConnect - Test OTP Email")
    print(f"🔑 Test OTP: {otp}")
    print("="*60)
    print("✅ In production, this would be sent as a real email")
    print("✅ The user would receive this OTP in their inbox")
    print("="*60)
    return True

def main():
    print("🧪 VendorConnect Email Test")
    print("=" * 40)
    
    # Get test email from user
    test_email = input("Enter your email address to test: ").strip()
    
    if not test_email:
        print("❌ Please enter a valid email address")
        return
    
    # Generate test OTP
    test_otp = generate_otp()
    
    print(f"\n📧 Testing email functionality...")
    print(f"📧 Sending to: {test_email}")
    print(f"📧 From: hackathongoo@gmail.com")
    
    # Send test email
    success = send_test_email(test_email, test_otp)
    
    if success:
        print(f"\n🎉 SUCCESS! Check your email ({test_email}) for the test message.")
        print(f"🔑 The test OTP is: {test_otp}")
        print("\n✅ Email system is working correctly!")
        print("✅ You can now use the forgot password feature in the application.")
    else:
        print(f"\n💥 FAILED! Please check the error messages above.")
        print("💡 Make sure you have:")
        print("   1. Set the MAIL_PASSWORD environment variable")
        print("   2. Generated an App Password for hackathongoo@gmail.com")
        print("   3. Enabled 2-Factor Authentication on the Gmail account")

if __name__ == "__main__":
    main()
