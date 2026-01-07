#!/usr/bin/env python3
"""
Migration script to add vehicle_type column to DeliveryAgent table
"""
from app import app, db
import sys

def add_vehicle_type_column():
    """Add vehicle_type column to DeliveryAgent table if it doesn't exist"""
    with app.app_context():
        try:
            # Check if column already exists
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('delivery_agent')]
            
            if 'vehicle_type' in columns:
                print("✓ Column 'vehicle_type' already exists in delivery_agent table")
                return True
            
            # Add the column
            print("Adding 'vehicle_type' column to delivery_agent table...")
            
            with db.engine.connect() as conn:
                # SQLite syntax
                conn.execute(db.text(
                    "ALTER TABLE delivery_agent ADD COLUMN vehicle_type VARCHAR(50)"
                ))
                conn.commit()
            
            print("✓ Successfully added 'vehicle_type' column to delivery_agent table")
            return True
            
        except Exception as e:
            print(f"✗ Error adding column: {str(e)}")
            return False

if __name__ == '__main__':
    print("=" * 60)
    print("DeliveryAgent Table Migration: Add vehicle_type column")
    print("=" * 60)
    
    success = add_vehicle_type_column()
    
    if success:
        print("\n✓ Migration completed successfully!")
        sys.exit(0)
    else:
        print("\n✗ Migration failed!")
        sys.exit(1)
