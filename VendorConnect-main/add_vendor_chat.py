#!/usr/bin/env python3
"""
Migration script to add VendorChatMessage table for vendor-to-vendor chat functionality
"""

from app import app, db
from sqlalchemy import text

def add_vendor_chat_table():
    """Add vendor_chat_message table if it doesn't exist"""
    with app.app_context():
        try:
            # Check if table already exists
            result = db.session.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='vendor_chat_message'"
            ))
            if result.fetchone():
                print("✓ vendor_chat_message table already exists")
                return
            
            # Create the vendor_chat_message table
            db.session.execute(text("""
                CREATE TABLE vendor_chat_message (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_id INTEGER NOT NULL,
                    receiver_id INTEGER NOT NULL,
                    message TEXT NOT NULL,
                    is_read BOOLEAN DEFAULT 0 NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sender_id) REFERENCES vendor (id),
                    FOREIGN KEY (receiver_id) REFERENCES vendor (id)
                )
            """))
            
            # Create indexes for better query performance
            db.session.execute(text("""
                CREATE INDEX idx_vendor_chat_sender ON vendor_chat_message(sender_id)
            """))
            
            db.session.execute(text("""
                CREATE INDEX idx_vendor_chat_receiver ON vendor_chat_message(receiver_id)
            """))
            
            db.session.execute(text("""
                CREATE INDEX idx_vendor_chat_created ON vendor_chat_message(created_at)
            """))
            
            db.session.commit()
            print("✓ Successfully created vendor_chat_message table with indexes")
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error creating vendor_chat_message table: {str(e)}")
            raise

if __name__ == '__main__':
    print("Adding VendorChatMessage table...")
    add_vendor_chat_table()
    print("Migration completed!")
