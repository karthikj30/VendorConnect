"""
Migration script to add image column to MenuItem table
"""
from app import app, db
from sqlalchemy import text

def add_image_column():
    with app.app_context():
        try:
            # Check if column already exists
            result = db.session.execute(text(
                "SELECT COUNT(*) FROM pragma_table_info('menu_item') WHERE name='image'"
            ))
            exists = result.scalar()
            
            if exists > 0:
                print("✓ Image column already exists in MenuItem table")
                return
            
            # Add the image column
            db.session.execute(text(
                "ALTER TABLE menu_item ADD COLUMN image VARCHAR(300)"
            ))
            db.session.commit()
            print("✓ Successfully added image column to MenuItem table")
            
        except Exception as e:
            print(f"✗ Error adding image column: {e}")
            db.session.rollback()

if __name__ == '__main__':
    add_image_column()
