"""
Migration script to add promo_due column to Vendor table.
"""
from app import app, db
from sqlalchemy import text

def add_promo_due_column():
    with app.app_context():
        try:
            existing = db.session.execute(text("SELECT name FROM pragma_table_info('vendor')")).fetchall()
            column_names = {row[0] for row in existing}

            if 'promo_due' in column_names:
                print("✓ promo_due column already exists")
                return

            db.session.execute(text("ALTER TABLE vendor ADD COLUMN promo_due FLOAT DEFAULT 0.0"))
            db.session.commit()
            print("✓ Added promo_due column to vendor table")
        except Exception as exc:
            db.session.rollback()
            print(f"✗ Error adding promo_due: {exc}")

if __name__ == '__main__':
    add_promo_due_column()
