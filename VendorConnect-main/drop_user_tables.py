#!/usr/bin/env python3
"""
Script to drop all user login database tables
This will delete: Customer, Vendor, Supplier, DeliveryAgent, and Admin tables
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app import app, db
from sqlalchemy import text

def drop_user_tables():
    """Drop all user login tables from the database"""
    with app.app_context():
        try:
            print("🗑️  Starting to drop all user login tables...")
            print("=" * 60)
            
            # List of user tables to drop
            user_tables = [
                'customer',
                'vendor', 
                'supplier',
                'delivery_agent',
                'admin'
            ]
            
            # Drop each table
            for table_name in user_tables:
                try:
                    # Check if table exists first
                    result = db.session.execute(
                        text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                    ).fetchone()
                    
                    if result:
                        db.session.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
                        print(f"✅ Dropped table: {table_name}")
                    else:
                        print(f"⚠️  Table not found: {table_name}")
                        
                except Exception as e:
                    print(f"❌ Error dropping table {table_name}: {str(e)}")
            
            db.session.commit()
            print("\n" + "=" * 60)
            print("✅ All user login tables have been dropped successfully!")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error during table drop operation: {str(e)}")
            return False

if __name__ == '__main__':
    print("\n⚠️  WARNING: This will permanently delete all user login data!")
    print("Tables to be dropped: Customer, Vendor, Supplier, DeliveryAgent, Admin")
    
    confirm = input("\nAre you sure you want to proceed? (yes/no): ").strip().lower()
    
    if confirm == 'yes':
        success = drop_user_tables()
        if success:
            print("\n✅ Operation completed successfully!")
            print("💡 You can now recreate the tables by running the app or migrations.")
        else:
            print("\n❌ Operation failed. Please check the error messages above.")
            sys.exit(1)
    else:
        print("\n❌ Operation cancelled by user.")
        sys.exit(0)
