"""
Migration script to add reward_points column to Customer table.
This column tracks points earned from self-pickup distance rewards.
"""

from app import app, db
from sqlalchemy import text, inspect

def add_reward_points_column():
    """Add reward_points column to Customer table if it doesn't exist"""
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('customer')]
            
            if 'reward_points' in columns:
                print("✓ reward_points column already exists")
                return True
            
            print("➤ Adding reward_points column to customer table...")
            db.session.execute(
                text("ALTER TABLE customer ADD COLUMN reward_points FLOAT DEFAULT 0.0")
            )
            db.session.commit()
            print("✓ reward_points column added successfully")
            return True
            
        except Exception as exc:
            db.session.rollback()
            print(f"✗ Error adding reward_points: {exc}")
            return False

if __name__ == '__main__':
    print("=" * 60)
    print("Customer Table Migration: Add Reward Points Support")
    print("=" * 60)
    
    success = add_reward_points_column()
    
    if success:
        print("\n✓ Migration completed successfully!")
        print("  • Customers can now earn points from self-pickup distance")
        print("  • Points unlock tiered coupon rewards")
        print("  • Rewards visible on customer dashboard")
    else:
        print("\n✗ Migration failed - please check the error above")
