"""
Migration script to add timestamp columns for order status tracking
"""
from app import app, db
from sqlalchemy import inspect, text

def add_timestamp_columns():
    with app.app_context():
        # Get the database engine
        inspector = inspect(db.engine)
        
        # Get existing columns in customer_order table
        existing_columns = [col['name'] for col in inspector.get_columns('customer_order')]
        
        print("Existing columns:", existing_columns)
        
        # Define new columns to add
        new_columns = {
            'confirmed_at': 'DATETIME',
            'preparing_at': 'DATETIME',
            'ready_at': 'DATETIME',
            'picked_up_at': 'DATETIME',
            'out_for_delivery_at': 'DATETIME'
        }
        
        # Add each column if it doesn't exist
        with db.engine.connect() as conn:
            for column_name, column_type in new_columns.items():
                if column_name not in existing_columns:
                    print(f"Adding column: {column_name}")
                    try:
                        conn.execute(text(f"ALTER TABLE customer_order ADD COLUMN {column_name} {column_type}"))
                        conn.commit()
                        print(f"✅ Successfully added '{column_name}' column")
                    except Exception as e:
                        print(f"❌ Error adding '{column_name}': {str(e)}")
                        conn.rollback()
                else:
                    print(f"✅ '{column_name}' column already exists")
        
        print("\n✅ Migration completed!")

if __name__ == '__main__':
    add_timestamp_columns()
