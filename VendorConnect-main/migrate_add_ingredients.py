"""
Migration script to add ingredients column to MenuItem table
"""
import sys
sys.path.insert(0, '/workspaces/VendorConnect/VendorConnect-main')

from app import app, db
from sqlalchemy import inspect, text

with app.app_context():
    inspector = inspect(db.engine)
    columns = [c['name'] for c in inspector.get_columns('menu_item')]
    
    print("📋 Current MenuItem columns:", columns)
    
    if 'ingredients' in columns:
        print("✅ 'ingredients' column already exists!")
    else:
        print("➕ Adding 'ingredients' column to MenuItem table...")
        try:
            # SQLite doesn't support ALTER COLUMN directly, so we add the new column
            db.session.execute(text('''
                ALTER TABLE menu_item ADD COLUMN ingredients TEXT
            '''))
            db.session.commit()
            print("✅ Successfully added 'ingredients' column!")
            
            # Verify the column was added
            inspector = inspect(db.engine)
            new_columns = [c['name'] for c in inspector.get_columns('menu_item')]
            print("✅ Updated MenuItem columns:", new_columns)
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            db.session.rollback()

print("\n✅ Migration completed!")
