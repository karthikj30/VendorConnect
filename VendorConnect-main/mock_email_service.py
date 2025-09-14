#!/usr/bin/env python3
"""
Mock email service for testing purposes
This will simulate sending emails without actually sending them
"""

import os
import sys
from datetime import datetime

def send_mock_otp_email(email, otp):
    """Mock email sending - just prints the OTP to console"""
    print("\n" + "="*60)
    print("📧 MOCK EMAIL SENT (For Testing Purposes)")
    print("="*60)
    print(f"📧 To: {email}")
    print(f"📧 From: hackathongoo@gmail.com")
    print(f"📧 Subject: VendorConnect - Password Reset OTP")
    print(f"🔑 OTP Code: {otp}")
    print(f"⏰ Expires: 10 minutes from now")
    print("="*60)
    print("✅ In production, this would be sent as a real email")
    print("✅ The user would receive this OTP in their inbox")
    print("="*60)
    
    # Also save to a file for easy access
    with open('otp_log.txt', 'a') as f:
        f.write(f"{datetime.now()}: OTP {otp} sent to {email}\n")
    
    return True

def test_mock_email():
    """Test the mock email service"""
    print("🧪 Testing Mock Email Service")
    print("="*40)
    
    test_email = input("Enter email to test: ").strip()
    if not test_email:
        test_email = "askotal07@gmail.com"
    
    otp = "123456"  # Mock OTP
    success = send_mock_otp_email(test_email, otp)
    
    if success:
        print("\n✅ Mock email service is working!")
        print("✅ You can now test the forgot password flow")
        print("✅ Check the console output above for the OTP")
    else:
        print("\n❌ Mock email service failed")

if __name__ == "__main__":
    test_mock_email()
