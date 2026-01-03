#!/usr/bin/env python3
"""
Migration script to add GSTIN column to Vendor table
"""

from app import app, db
from sqlalchemy import text

def add_gstin_column():
    with app.app_context():
        try:
            # Check if the column already exists
            inspector = db.inspect(db.engine)
            columns = [c['name'] for c in inspector.get_columns('vendor')]
            
            if 'gstin' in columns:
                print("✓ GSTIN column already exists in vendor table")
                return
            
            # Add the gstin column
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE vendor ADD COLUMN gstin VARCHAR(15) DEFAULT NULL'))
                conn.commit()
            
            print("✓ Successfully added GSTIN column to vendor table")
            
        except Exception as e:
            print(f"✗ Error adding GSTIN column: {e}")
            raise

if __name__ == '__main__':
    add_gstin_column()
