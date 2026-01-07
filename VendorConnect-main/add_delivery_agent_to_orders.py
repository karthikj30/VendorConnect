#!/usr/bin/env python3
"""
Migration script to add delivery_agent_id column to Order table
"""
from app import app, db, Order
import sys

def add_delivery_agent_column():
    """Add delivery_agent_id column to Order table if it doesn't exist"""
    with app.app_context():
        try:
            # Check if column already exists
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('order')]
            
            if 'delivery_agent_id' in columns:
                print("✓ Column 'delivery_agent_id' already exists in Order table")
                return True
            
            # Add the column
            print("Adding 'delivery_agent_id' column to Order table...")
            
            with db.engine.connect() as conn:
                # SQLite syntax
                conn.execute(db.text(
                    "ALTER TABLE 'order' ADD COLUMN delivery_agent_id INTEGER"
                ))
                conn.commit()
            
            print("✓ Successfully added 'delivery_agent_id' column to Order table")
            return True
            
        except Exception as e:
            print(f"✗ Error adding column: {str(e)}")
            return False

if __name__ == '__main__':
    print("=" * 60)
    print("Order Table Migration: Add delivery_agent_id column")
    print("=" * 60)
    
    success = add_delivery_agent_column()
    
    if success:
        print("\n✓ Migration completed successfully!")
        sys.exit(0)
    else:
        print("\n✗ Migration failed!")
        sys.exit(1)
