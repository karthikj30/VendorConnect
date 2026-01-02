"""
Migration script to add logo and hero_image columns to Vendor table.
"""
from app import app, db
from sqlalchemy import text


def add_brand_columns():
    with app.app_context():
        try:
            # Check if columns already exist
            existing = db.session.execute(text("SELECT name FROM pragma_table_info('vendor')")).fetchall()
            column_names = {row[0] for row in existing}

            added = []

            if 'logo' not in column_names:
                db.session.execute(text("ALTER TABLE vendor ADD COLUMN logo VARCHAR(300)"))
                added.append('logo')

            if 'hero_image' not in column_names:
                db.session.execute(text("ALTER TABLE vendor ADD COLUMN hero_image VARCHAR(300)"))
                added.append('hero_image')

            if not added:
                print("✓ logo and hero_image columns already exist in Vendor table")
                return

            db.session.commit()
            print("✓ Added columns: " + ", ".join(added))
        except Exception as exc:
            db.session.rollback()
            print(f"✗ Error updating Vendor table: {exc}")


if __name__ == '__main__':
    add_brand_columns()
