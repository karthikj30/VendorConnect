#!/usr/bin/env python
"""
Migration script to add delivery tracking columns to CustomerOrder table
Checks if columns exist before adding to avoid errors on re-run
"""

from app import app, db
from sqlalchemy import inspect, text, exc

def migrate_delivery_tracking():
    """Add delivery tracking columns to CustomerOrder if they don't exist"""
    with app.app_context():
        try:
            # Get the inspector to check existing columns
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('customer_order')]
            
            print(f"Current columns in customer_order: {columns}\n")
            
            # Check and add delivery_agent_id if missing
            if 'delivery_agent_id' not in columns:
                print("Adding delivery_agent_id column...")
                try:
                    with db.engine.begin() as connection:
                        connection.execute(text('''
                            ALTER TABLE customer_order 
                            ADD COLUMN delivery_agent_id INTEGER
                        '''))
                    print("✓ Added delivery_agent_id column")
                except exc.OperationalError as e:
                    print(f"⚠️ Error adding delivery_agent_id: {str(e)}")
            else:
                print("✓ delivery_agent_id column already exists")
            
            # Check and add delivery_latitude if missing
            if 'delivery_latitude' not in columns:
                print("Adding delivery_latitude column...")
                try:
                    with db.engine.begin() as connection:
                        connection.execute(text('''
                            ALTER TABLE customer_order 
                            ADD COLUMN delivery_latitude FLOAT
                        '''))
                    print("✓ Added delivery_latitude column")
                except exc.OperationalError as e:
                    print(f"⚠️ Error adding delivery_latitude: {str(e)}")
            else:
                print("✓ delivery_latitude column already exists")
            
            # Check and add delivery_longitude if missing
            if 'delivery_longitude' not in columns:
                print("Adding delivery_longitude column...")
                try:
                    with db.engine.begin() as connection:
                        connection.execute(text('''
                            ALTER TABLE customer_order 
                            ADD COLUMN delivery_longitude FLOAT
                        '''))
                    print("✓ Added delivery_longitude column")
                except exc.OperationalError as e:
                    print(f"⚠️ Error adding delivery_longitude: {str(e)}")
            else:
                print("✓ delivery_longitude column already exists")
            
            # Verify columns were added
            inspector = inspect(db.engine)
            new_columns = [col['name'] for col in inspector.get_columns('customer_order')]
            print(f"\n✅ Migration completed!")
            print(f"Updated columns: {new_columns}")
            
        except Exception as e:
            print(f"❌ Migration error: {str(e)}")

if __name__ == '__main__':
    migrate_delivery_tracking()

