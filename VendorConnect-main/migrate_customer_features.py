#!/usr/bin/env python3
"""
Migration script to create new customer feature tables:
- CustomerReview (ratings and reviews)
- Wishlist (favorite vendors/items)
- ScheduledOrder (order scheduling)
"""

from app import app, db

def migrate():
    """Create all new tables"""
    with app.app_context():
        print("🔄 Starting migration for customer features...")
        
        try:
            # Create all tables
            db.create_all()
            
            print("✅ Successfully created all tables!")
            print("\nNew tables created:")
            print("  ✓ CustomerReview - for ratings and reviews")
            print("  ✓ Wishlist - for favorite vendors and items")
            print("  ✓ ScheduledOrder - for scheduled orders")
            print("\n🎉 Migration completed successfully!")
            
        except Exception as e:
            print(f"❌ Error during migration: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

if __name__ == '__main__':
    success = migrate()
    exit(0 if success else 1)
