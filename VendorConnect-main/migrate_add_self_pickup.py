#!/usr/bin/env python3
"""
Migration script to add delivery_type and pickup_ready_at columns to CustomerOrder table
"""
from app import app, db
from sqlalchemy import text
import sys

def add_self_pickup_fields():
    """Add delivery_type and pickup_ready_at columns to CustomerOrder table if they don't exist"""
    with app.app_context():
        try:
            # Check if delivery_type column exists
            result = db.session.execute(text("PRAGMA table_info(customer_order)"))
            columns = [row[1] for row in result]
            
            if 'delivery_type' not in columns:
                print("➤ Adding delivery_type column to customer_order table...")
                db.session.execute(text(
                    "ALTER TABLE customer_order ADD COLUMN delivery_type VARCHAR(20) DEFAULT 'delivery'"
                ))
                db.session.commit()
                print("✓ delivery_type column added successfully")
            else:
                print("ℹ delivery_type column already exists")
            
            # Check if pickup_ready_at column exists
            result = db.session.execute(text("PRAGMA table_info(customer_order)"))
            columns = [row[1] for row in result]
            
            if 'pickup_ready_at' not in columns:
                print("➤ Adding pickup_ready_at column to customer_order table...")
                db.session.execute(text(
                    "ALTER TABLE customer_order ADD COLUMN pickup_ready_at DATETIME"
                ))
                db.session.commit()
                print("✓ pickup_ready_at column added successfully")
            else:
                print("ℹ pickup_ready_at column already exists")
            
            # Verify the changes
            result = db.session.execute(text("PRAGMA table_info(customer_order)"))
            print("\n📋 Current customer_order table structure:")
            for row in result:
                print(f"  - {row[1]} ({row[2]})")
            
            return True
            
        except Exception as e:
            print(f"\n✗ Error during migration: {str(e)}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    print("=" * 60)
    print("CustomerOrder Table Migration: Add Self-Pickup Support")
    print("=" * 60)
    
    success = add_self_pickup_fields()
    
    if success:
        print("\n✓ Migration completed successfully!")
        print("\nNew features enabled:")
        print("  • Customers can choose self-pickup option")
        print("  • Vendors can mark pickup orders as 'done'")
        print("  • No delivery fee for self-pickup orders")
        sys.exit(0)
    else:
        print("\n✗ Migration failed!")
        sys.exit(1)
