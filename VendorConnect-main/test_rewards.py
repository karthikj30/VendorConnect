"""
Test script to verify the rewards feature is working correctly
"""

from app import app, db, Customer
import json

def test_rewards_api():
    """Test the rewards API endpoint"""
    with app.app_context():
        with app.test_client() as client:
            # Get all customers
            customers = Customer.query.all()
            
            if not customers:
                print("❌ No customers found - create a customer account first")
                return False
            
            customer = customers[0]
            print(f"Testing rewards for customer: {customer.name}")
            print(f"Current reward points: {customer.reward_points or 0}")
            
            # Simulate logged in session
            with client.session_transaction() as sess:
                sess['customer_id'] = customer.id
                sess['customer_name'] = customer.name
            
            # Test the rewards API
            response = client.get('/api/customer/rewards')
            
            if response.status_code == 200:
                data = json.loads(response.data)
                print(f"\n✓ API Response Status: {response.status_code}")
                print(f"✓ Success: {data.get('success')}")
                print(f"✓ Total Points: {data.get('data', {}).get('totalPoints', 0)}")
                print(f"✓ Number of Coupons: {len(data.get('data', {}).get('coupons', []))}")
                
                if data.get('data', {}).get('coupons'):
                    print("\n📜 Available Coupons:")
                    for coupon in data['data']['coupons']:
                        print(f"  - {coupon['title']}: {coupon['code']} ({coupon['discount']}{'' if coupon['discountType'] == 'amount' else '%'} off)")
                
                return True
            else:
                print(f"❌ API returned status code: {response.status_code}")
                print(f"Response: {response.data}")
                return False

if __name__ == '__main__':
    print("=" * 70)
    print("Testing Rewards & Coupons Feature")
    print("=" * 70)
    
    success = test_rewards_api()
    
    if success:
        print("\n✅ Rewards feature is working correctly!")
        print("\n📍 To see rewards on the customer dashboard:")
        print("  1. Login as a customer")
        print("  2. Navigate to the dashboard")
        print("  3. Scroll down to see 'Your Rewards & Coupons' section")
    else:
        print("\n❌ Rewards feature test failed")
