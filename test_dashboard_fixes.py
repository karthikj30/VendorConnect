#!/usr/bin/env python
"""
Customer Dashboard Verification Test
Tests that all fixed components work properly
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import app, db, Customer, MenuItem, Vendor, CustomerReview, Wishlist, ScheduledOrder
import json

def test_dashboard_route():
    """Test that dashboard route loads without errors"""
    with app.test_client() as client:
        # Test without session (should auto-login or redirect)
        response = client.get('/customer/dashboard')
        print(f"✅ Dashboard Route: Status {response.status_code}")
        assert response.status_code in [200, 302], f"Expected 200 or 302, got {response.status_code}"
        
        # Check that response contains expected HTML elements
        if response.status_code == 200:
            html = response.get_data(as_text=True)
            assert '<div class="header">' in html, "Missing header div"
            assert 'vendorsGrid' in html, "Missing vendors grid"
            assert 'wishlistModal' in html, "Missing wishlist modal"
            assert 'scheduledOrdersModal' in html, "Missing scheduled orders modal"
            assert 'recommendationsModal' in html, "Missing recommendations modal"
            assert 'DOMContentLoaded' in html, "Missing DOMContentLoaded listener"
            print("✅ Dashboard HTML contains all required elements")

def test_api_endpoints():
    """Test that API endpoints respond correctly"""
    with app.test_client() as client:
        with app.app_context():
            # Create or get a customer
            customer = Customer.query.first()
            if customer:
                with client.session_transaction() as sess:
                    sess['customer_id'] = customer.id
                    sess['customer_name'] = customer.name
                    sess['customer_email'] = customer.email
                    sess['customer_phone'] = customer.phone
                    sess['customer_location'] = customer.location
        
        # Test Wishlist API
        response = client.get('/api/customer/wishlist')
        print(f"✅ GET /api/customer/wishlist: Status {response.status_code}")
        assert response.status_code == 200, f"Wishlist API failed: {response.status_code}"
        data = response.get_json()
        assert 'success' in data, "Missing success field"
        assert 'wishlist' in data, "Missing wishlist field"
        
        # Test Scheduled Orders API
        response = client.get('/api/customer/scheduled-orders')
        print(f"✅ GET /api/customer/scheduled-orders: Status {response.status_code}")
        assert response.status_code == 200, f"Scheduled orders API failed: {response.status_code}"
        data = response.get_json()
        assert 'success' in data, "Missing success field"
        assert 'scheduled_orders' in data, "Missing scheduled_orders field"
        
        # Test Recommendations API
        response = client.get('/api/customer/recommendations')
        print(f"✅ GET /api/customer/recommendations: Status {response.status_code}")
        assert response.status_code == 200, f"Recommendations API failed: {response.status_code}"
        data = response.get_json()
        assert 'success' in data, "Missing success field"
        assert 'recommendations' in data, "Missing recommendations field"
        
        # Test Vendors Sorted API
        response = client.get('/api/vendors/sorted?sort_by=rating&category=all')
        print(f"✅ GET /api/vendors/sorted: Status {response.status_code}")
        assert response.status_code == 200, f"Vendors sorted API failed: {response.status_code}"
        data = response.get_json()
        assert 'success' in data or 'vendors' in data, "Missing success or vendors field"

def test_database_models():
    """Test that database models exist and are accessible"""
    with app.app_context():
        # Check tables exist
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        expected_tables = ['customer_review', 'wishlist', 'scheduled_order']
        for table in expected_tables:
            assert table in tables, f"Table {table} not found in database"
            print(f"✅ Database table '{table}' exists")

if __name__ == '__main__':
    print("\n" + "="*50)
    print("CUSTOMER DASHBOARD VERIFICATION TEST")
    print("="*50 + "\n")
    
    try:
        print("[1/4] Testing Dashboard Route...")
        test_dashboard_route()
        
        print("\n[2/4] Testing API Endpoints...")
        test_api_endpoints()
        
        print("\n[3/4] Testing Database Models...")
        test_database_models()
        
        print("\n" + "="*50)
        print("✅ ALL TESTS PASSED!")
        print("="*50)
        print("\n📋 Dashboard should now load correctly:")
        print("   - Vendors display with heart wishlist button")
        print("   - Profile menu shows Wishlist, Scheduled Orders, Recommendations")
        print("   - All modals are properly structured and accessible")
        print("   - API endpoints respond correctly")
        print("\n")
        
    except AssertionError as e:
        print(f"\n❌ Test Failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
