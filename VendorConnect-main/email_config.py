# Email Configuration for VendorConnect
# Credentials come from the environment (.env locally, project settings when
# deployed). Never put real values in this file: it is committed.
import os

# Gmail SMTP Configuration
MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ('1', 'true', 'yes')

# Email Credentials
MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')

# Test Configuration
TEST_EMAIL = os.environ.get('TEST_EMAIL', '')  # Email to test with
