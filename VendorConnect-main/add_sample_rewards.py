"""
Add sample reward points to customers for testing the rewards feature
"""

from app import app, db, Customer

def add_sample_rewards():
    """Add sample reward points to customers"""
    with app.app_context():
        try:
            # Get all customers
            customers = Customer.query.all()
            
            if not customers:
                print("No customers found in database")
                return False
            
            # Add varying amounts of reward points to customers
            for i, customer in enumerate(customers[:5]):  # First 5 customers
                if i == 0:
                    customer.reward_points = 250  # High points - all coupons
                elif i == 1:
                    customer.reward_points = 120  # Medium points - 2 coupons
                elif i == 2:
                    customer.reward_points = 75   # Low points - 1 coupon
                else:
                    customer.reward_points = 20   # Very low - no coupons yet
                
                print(f"✓ Set {customer.name} reward points to {customer.reward_points}")
            
            db.session.commit()
            print(f"\n✓ Added sample rewards to {len(customers[:5])} customers")
            return True
            
        except Exception as exc:
            db.session.rollback()
            print(f"✗ Error adding sample rewards: {exc}")
            return False

if __name__ == '__main__':
    print("=" * 60)
    print("Add Sample Reward Points for Testing")
    print("=" * 60)
    
    success = add_sample_rewards()
    
    if success:
        print("\n✓ Sample rewards added successfully!")
        print("  • Login as a customer to see your reward coupons")
        print("  • Customers with 50+ points will see 1 coupon")
        print("  • Customers with 100+ points will see 2 coupons")
        print("  • Customers with 200+ points will see 3 coupons")
    else:
        print("\n✗ Failed to add sample rewards")
