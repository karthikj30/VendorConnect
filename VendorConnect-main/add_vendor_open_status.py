"""
Migration script to add is_open column to Vendor table.
"""
from app import app, db
from sqlalchemy import text, inspect

def add_open_status_column():
    with app.app_context():
        try:
            # Check if column already exists using SQLAlchemy inspection API
            inspector = inspect(db.engine)
            columns = inspector.get_columns('vendor')
            column_names = {col['name'] for col in columns}

            if 'is_open' in column_names:
                print("\u2713 is_open column already exists in Vendor table")
                return

            # Add the is_open column with default TRUE
            db.session.execute(text("ALTER TABLE vendor ADD COLUMN is_open BOOLEAN DEFAULT 1"))
            db.session.commit()
            print("\u2713 Successfully added is_open column to Vendor table")
        except Exception as exc:
            db.session.rollback()
            print(f"\u2717 Error updating Vendor table: {exc}")

if __name__ == '__main__':
    add_open_status_column()
