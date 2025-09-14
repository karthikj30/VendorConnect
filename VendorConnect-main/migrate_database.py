ka#!/usr/bin/env python3
"""
Database migration script to add email field to existing Vendor table
Run this script before starting the application to update the database schema
"""

import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the app configuration
basedir = os.path.abspath(os.path.dirname(__file__))

# Create a temporary Flask app for migration
app = Flask(__name__, instance_path=os.path.join(basedir, '../instance'))
app.config['SECRET_KEY'] = 'vendorconnect_secret_key_2024'

# Ensure the instance directory exists
os.makedirs(app.instance_path, exist_ok=True)

# Use the same database path as the main app
db_path = os.path.join(app.instance_path, 'vendorconnect.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define the updated Vendor model with email field
class Vendor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)  # Allow NULL for existing records
    location = db.Column(db.String(200), nullable=False)
    business_type = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=None)

def migrate_database():
    """Migrate the database to add email field"""
    try:
        print("Starting database migration...")
        
        # Check if database exists
        if not os.path.exists(db_path):
            print("Database doesn't exist. Creating new database...")
            db.create_all()
            print("✅ Database created successfully!")
            return True
        
        # Check if email column already exists
        with app.app_context():
            # Get table info
            with db.engine.connect() as conn:
                result = conn.execute(db.text("PRAGMA table_info(vendor)"))
                columns = [row[1] for row in result]
                
                if 'email' in columns:
                    print("✅ Email column already exists. No migration needed.")
                    return True
                
                print("Adding email column to vendor table...")
                
                # Add email column (allowing NULL values for existing records)
                conn.execute(db.text("ALTER TABLE vendor ADD COLUMN email VARCHAR(120)"))
                conn.commit()
                
                print("✅ Email column added successfully!")
                print("✅ Database migration completed!")
                return True
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = migrate_database()
    if success:
        print("\n🎉 Migration completed successfully!")
        print("You can now start the application with: python app.py")
    else:
        print("\n💥 Migration failed. Please check the error messages above.")
        sys.exit(1)
