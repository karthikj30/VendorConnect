#!/usr/bin/env python3
"""
Database migration script to add missing columns to customer_order table
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

def migrate_customer_order_table():
    """Migrate the customer_order table to add missing columns"""
    try:
        print("Starting customer_order table migration...")

        # Check if database exists
        if not os.path.exists(db_path):
            print("Database doesn't exist. Creating new database...")
            db.create_all()
            print("✅ Database created successfully!")
            return True

        # Check current columns in customer_order table
        with app.app_context():
            with db.engine.connect() as conn:
                result = conn.execute(db.text("PRAGMA table_info(customer_order)"))
                columns = [row[1] for row in result]

                print(f"Current columns in customer_order: {columns}")

                # Columns to add
                columns_to_add = {
                    'subtotal': 'ALTER TABLE customer_order ADD COLUMN subtotal FLOAT DEFAULT 0.0',
                    'delivery_fee': 'ALTER TABLE customer_order ADD COLUMN delivery_fee FLOAT DEFAULT 40.0',
                    'tax_amount': 'ALTER TABLE customer_order ADD COLUMN tax_amount FLOAT DEFAULT 0.0',
                    'payment_status': "ALTER TABLE customer_order ADD COLUMN payment_status VARCHAR(20) DEFAULT 'pending'",
                    'delivery_instructions': 'ALTER TABLE customer_order ADD COLUMN delivery_instructions VARCHAR(500)',
                    'estimated_delivery_time': 'ALTER TABLE customer_order ADD COLUMN estimated_delivery_time DATETIME',
                    'actual_delivery_time': 'ALTER TABLE customer_order ADD COLUMN actual_delivery_time DATETIME',
                    'updated_at': 'ALTER TABLE customer_order ADD COLUMN updated_at DATETIME'
                }

                added_columns = []
                for col_name, alter_sql in columns_to_add.items():
                    if col_name not in columns:
                        print(f"Adding {col_name} column...")
                        conn.execute(db.text(alter_sql))
                        added_columns.append(col_name)
                    else:
                        print(f"✅ {col_name} column already exists")

                if added_columns:
                    conn.commit()
                    print(f"✅ Added columns: {', '.join(added_columns)}")
                else:
                    print("✅ All required columns already exist")

                print("✅ Customer order table migration completed!")
                return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = migrate_customer_order_table()
    if success:
        print("\n🎉 Migration completed successfully!")
        print("You can now start the application with: python app.py")
    else:
        print("\n💥 Migration failed. Please check the error messages above.")
        sys.exit(1)