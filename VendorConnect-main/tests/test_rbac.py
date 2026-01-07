import pytest
import importlib.util
import os

# Reuse the same app module import pattern as other tests
APP_PATH = os.path.join(os.path.dirname(__file__), '..', 'app.py')
spec = importlib.util.spec_from_file_location('vc_app', APP_PATH)
vc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vc)
app = getattr(vc, 'app')


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    db_mod = getattr(vc, 'db')
    Supplier = getattr(vc, 'Supplier')
    with app.app_context():
        try:
            db_mod.drop_all()
        except Exception:
            pass
        db_mod.create_all()
        s = Supplier(name='Test Sup', phone='000', location='here')
        db_mod.session.add(s)
        db_mod.session.commit()
    with app.test_client() as client:
        yield client


def test_supplier_json_guards(client):
    # place an order as vendor to create an order_id
    with client.session_transaction() as sess:
        sess['vendor_id'] = 1

    resp = client.post('/api/place-order', json={'supplier_id': 1, 'total_amount': 10, 'items': []})
    assert resp.status_code == 200
    order_id = resp.get_json().get('order_id')
    assert order_id is not None

    # No supplier session -> supplier APIs should be 401
    resp = client.get('/api/supplier/orders')
    assert resp.status_code == 401

    resp = client.get('/api/supplier/events')
    assert resp.status_code == 401

    # Vendor should not be able to access supplier-level endpoints
    # Clear any existing vendor session to simulate an unauthenticated caller
    with client.session_transaction() as sess:
        sess.pop('vendor_id', None)

    resp = client.get(f'/api/order/{order_id}/events')
    assert resp.status_code == 401

    # Vendor should be able to subscribe to order events (vendor-level)
    with client.session_transaction() as sess:
        sess['vendor_id'] = 1

    resp = client.get(f'/api/order/{order_id}/events')
    assert resp.status_code == 200
    assert resp.headers.get('Content-Type', '').startswith('text/event-stream')


def test_customer_and_delivery_guards(client):
    # create customer and place a customer order
    db_mod = getattr(vc, 'db')
    Customer = getattr(vc, 'Customer')

    with app.app_context():
        cust = Customer(name='GuardTest', phone='111222333', email='guard@test.com')
        db_mod.session.add(cust)
        db_mod.session.commit()
        cust_id = cust.id

    # Login as customer and place order
    with client.session_transaction() as sess:
        sess['customer_id'] = cust_id

    resp = client.post('/api/place-order-customer', json={'name': 'GuardTest', 'email': 'guard@test.com', 'phone': '111222333', 'address': 'Addr', 'items': [], 'payment': 'cod'})
    assert resp.status_code == 200
    order_id = resp.get_json().get('order_id')
    assert order_id is not None

    # Clear session -> unauthenticated
    with client.session_transaction() as sess:
        sess.pop('customer_id', None)

    # Customer SSE endpoint should be 401
    resp = client.get(f'/api/customer/order/{order_id}/events')
    assert resp.status_code == 401

    # get_delivery_location is protected by customer_api_required -> should be 401
    resp = client.get(f'/api/delivery/location/{order_id}')
    assert resp.status_code == 401


def test_delivery_agent_api_guard(client):
    # POST to delivery-agent update-status without authentication should be 401
    resp = client.post('/api/delivery-agent/update-status', json={'order_id': 1, 'status': 'in_transit'})
    assert resp.status_code == 401
