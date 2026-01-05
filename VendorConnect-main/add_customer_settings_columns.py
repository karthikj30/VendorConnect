#!/usr/bin/env python3
"""
Migration script to add customer settings columns to the Customer table
"""

import sqlite3
from sqlalchemy import create_engine, inspect, text

# Database path
DATABASE_PATH = 'instance/vendorconnect.db'

def add_settings_columns():
    """Add settings columns to customer table"""
    
    # Connect to database
    engine = create_engine(f'sqlite:///{DATABASE_PATH}')
    inspector = inspect(engine)
    
    # Get existing columns
    existing_columns = [col['name'] for col in inspector.get_columns('customer')]
    
    print("📋 Existing Customer columns:")
    print(existing_columns)
    print()
    
    # Define new columns to add
    new_columns = {
        'email_notifications': 'BOOLEAN DEFAULT 1',
        'sms_notifications': 'BOOLEAN DEFAULT 1',
        'promo_emails': 'BOOLEAN DEFAULT 0',
        'language': 'VARCHAR(10) DEFAULT "en"',
        'theme': 'VARCHAR(20) DEFAULT "light"',
        'default_instructions': 'TEXT',
        'default_payment': 'VARCHAR(20) DEFAULT "cod"',
        'profile_visibility': 'VARCHAR(20) DEFAULT "private"',
        'data_sharing': 'BOOLEAN DEFAULT 0'
    }
    
    print("🔧 Adding settings columns to Customer table...")
    
    with engine.connect() as conn:
        for column_name, column_type in new_columns.items():
            if column_name not in existing_columns:
                try:
                    sql = f"ALTER TABLE customer ADD COLUMN {column_name} {column_type}"
                    conn.execute(text(sql))
                    conn.commit()
                    print(f"✅ Added column: {column_name}")
                except Exception as e:
                    print(f"⚠️  Column {column_name} might already exist or error: {e}")
            else:
                print(f"ℹ️  Column {column_name} already exists")
    
    print()
    print("🔍 Verifying columns...")
    
    # Verify all columns exist
    inspector = inspect(engine)
    final_columns = [col['name'] for col in inspector.get_columns('customer')]
    
    all_present = all(col in final_columns for col in new_columns.keys())
    
    if all_present:
        print("✅ Migration completed successfully! All settings columns are present.")
    else:
        missing = [col for col in new_columns.keys() if col not in final_columns]
        print(f"⚠️  Some columns are still missing: {missing}")
    
    print()
    print("📊 Final Customer table columns:")
    print(final_columns)

if __name__ == '__main__':
    try:
        add_settings_columns()
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
