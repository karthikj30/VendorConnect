"""
Migration script to create admin table and seed a default admin record.
"""
from app import app, db
from sqlalchemy import text

def add_admin_table():
    with app.app_context():
        try:
            # Create table if it does not exist
            db.session.execute(text(
                """
                CREATE TABLE IF NOT EXISTS admin (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(120) NOT NULL UNIQUE,
                    password_hash VARCHAR(200),
                    balance FLOAT DEFAULT 0.0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            ))

            # Ensure a default admin exists
            result = db.session.execute(text("SELECT id FROM admin LIMIT 1")).fetchone()
            if not result:
                db.session.execute(text(
                    """
                    INSERT INTO admin (name, email, password_hash, balance)
                    VALUES (:name, :email, :password_hash, :balance)
                    """
                ), {
                    'name': 'Platform Admin',
                    'email': 'admin@vendorconnect.com',
                    'password_hash': None,
                    'balance': 0.0
                })
                print("✓ Seeded default admin account (admin@vendorconnect.com)")
            else:
                print("✓ Admin table already has records")

            db.session.commit()
            print("✓ Admin table migration complete")
        except Exception as exc:
            db.session.rollback()
            print(f"✗ Error creating admin table: {exc}")


if __name__ == '__main__':
    add_admin_table()
