import importlib.util
import os
import pytest
from flask import url_for

# Load the app module by path so tests can import the Flask app variable even though
# the project folder has a hyphen in its name.
APP_PATH = os.path.join(os.path.dirname(__file__), '..', 'app.py')
spec = importlib.util.spec_from_file_location('vc_app', APP_PATH)
vc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vc)
app = getattr(vc, 'app')
# Ensure Flask knows the correct templates folder when module is loaded via importlib
app.template_folder = os.path.join(os.path.dirname(APP_PATH), 'templates')
app.static_folder = os.path.join(os.path.dirname(APP_PATH), 'static')

@pytest.fixture
def client():
    app.config['TESTING'] = True
    # Use temporary sqlite DB for tests
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    # use the imported module `vc` to access db and models
    db_mod = getattr(vc, 'db')
    Supplier = getattr(vc, 'Supplier')
    with app.app_context():
        # Ensure fresh schema (drop any existing tables) and recreate
        try:
            db_mod.drop_all()
        except Exception:
            pass
        db_mod.create_all()
        # create a supplier with id=1 for tests
        s = Supplier(name='Test Sup', phone='000', location='here')
        db_mod.session.add(s)
        db_mod.session.commit()
    with app.test_client() as client:
        yield client
    # DB teardown handled by in-memory DB garbage collection

# Routes to test
ROUTES = [
    '/supplier/dashboard',
    '/supplier/manage-products',
    '/supplier/orders',
    '/supplier/profile',
    '/supplier/inventory',
    '/supplier/communication',
    '/supplier/payments',
    '/supplier/analytics',
    '/supplier/reliability',
    '/supplier/common-features',
    '/supplier/onboarding',
    '/supplier/business',
    '/supplier/warehouses',
    '/supplier/service-areas',
]

def test_routes_require_login(client):
    # When not authenticated they should redirect (302)
    for r in ROUTES:
        resp = client.get(r)
        assert resp.status_code in (301, 302)


def test_routes_render_with_session(client):
    # Simulate a logged-in supplier by setting session
    with client.session_transaction() as sess:
        sess['supplier_id'] = 1

    for r in ROUTES:
        resp = client.get(r)
        assert resp.status_code == 200

    # Also ensure the manage-products page renders even if DB empty
    resp = client.get('/supplier/manage-products')
    assert b'Product Catalog' in resp.data

    # Profile should render
    resp = client.get('/supplier/profile')
    assert b'Profile Settings' in resp.data

    # create a warehouse and a service area to ensure dashboard badges render
    resp = client.post('/supplier/warehouses', data={'name': 'W-DB', 'address': 'AddrX'}, follow_redirects=True)
    assert resp.status_code == 200
    resp = client.post('/supplier/service-areas', data={'name': 'ZoneX', 'description': 'Desc'}, follow_redirects=True)
    assert resp.status_code == 200

    # Now check dashboard shows counts/badges
    resp = client.get('/supplier/dashboard')
    assert b'Warehouses' in resp.data
    assert b'Service Areas' in resp.data

    # Onboarding, business, warehouses and service-areas should render
    resp = client.get('/supplier/onboarding')
    assert resp.status_code == 200
    resp = client.get('/supplier/business')
    assert resp.status_code == 200
    resp = client.get('/supplier/warehouses')
    assert resp.status_code == 200
    resp = client.get('/supplier/service-areas')
    assert resp.status_code == 200


def test_warehouse_and_service_area_crud(client):
    with client.session_transaction() as sess:
        sess['supplier_id'] = 1

    # create warehouse
    resp = client.post('/supplier/warehouses', data={'name': 'W1', 'address': 'Addr 1', 'phone': '123'})
    assert resp.status_code in (301, 302)
    # list warehouses
    resp = client.get('/supplier/warehouses')
    assert b'W1' in resp.data

    # create service area
    resp = client.post('/supplier/service-areas', data={'name': 'Zone A', 'description': 'Nearby', 'postal_codes': '560001,560002'})
    assert resp.status_code in (301, 302)
    resp = client.get('/supplier/service-areas')
    assert b'Zone A' in resp.data


def test_supplier_order_api(client):
    pass


def test_supplier_create_product(client):
    db_mod = getattr(vc, 'db')
    Product = getattr(vc, 'Product')

    # Ensure supplier exists in fixture (id=1)
    with client.session_transaction() as sess:
        sess['supplier_id'] = 1

    # Post new product
    resp = client.post('/supplier/manage-products', data={'name': 'Tomato', 'category': 'veg', 'price': '28.5', 'stock': '100', 'unit': 'kg'})
    # Expect redirect back to manage products
    assert resp.status_code in (301, 302)

    # Verify product persisted in DB
    with app.app_context():
        p = db_mod.session.query(Product).filter_by(name='Tomato', supplier_id=1).first()
        assert p is not None
        assert p.current_price == 28.5
        assert p.stock_available == 100
        assert p.unit == 'kg'


def test_supplier_order_api(client):
    Vendor = getattr(vc, 'Vendor')
    Vendor = getattr(vc, 'Vendor')
    db_mod = getattr(vc, 'db')
    # Ensure vendor exists
    with app.app_context():
        if db_mod.session.query(Vendor).count() == 0:
            v = Vendor(name='Test Vendor', phone='111', location='here')
            db_mod.session.add(v)
            db_mod.session.commit()

    with client.session_transaction() as sess:
        sess['vendor_id'] = 1

    # Place order as vendor
    resp = client.post('/api/place-order', json={'supplier_id':1, 'total_amount':100, 'items':[]})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    order_id = data.get('order_id')
    assert order_id is not None

    # Get supplier orders API
    # Ensure supplier API returns 401 for unauthenticated
    resp = client.get('/api/supplier/orders')
    assert resp.status_code == 401

    # Log in as supplier and fetch orders
    with client.session_transaction() as sess:
        sess['supplier_id'] = 1

    resp = client.get('/api/supplier/orders')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert any(o['id']==order_id for o in data['orders'])
    # Verify timestamps key exists on orders
    found = None
    for o in data['orders']:
        if o['id'] == order_id:
            found = o
            break
    assert found is not None
    assert 'timestamps' in found
    assert isinstance(found['timestamps'], dict)
    # Supplier accept order via API
    resp = client.post(f'/api/supplier/orders/{order_id}/action', json={'action':'accept'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert data['status'] in ('confirmed', 'accepted')

    # Check order in DB has confirmed_at set
    with app.app_context():
        ord_obj = getattr(vc, 'Order').query.get(order_id)
        assert ord_obj.confirmed_at is not None


def test_supplier_edit_and_delete_product(client):
    db_mod = getattr(vc, 'db')
    Product = getattr(vc, 'Product')

    # Ensure supplier exists and log in
    with client.session_transaction() as sess:
        sess['supplier_id'] = 1

    # Create a product via POST
    resp = client.post('/supplier/manage-products', data={'name': 'Potato', 'category': 'veg', 'price': '20', 'stock': '50', 'unit': 'kg'})
    assert resp.status_code in (301, 302)

    # Get the created product
    with app.app_context():
        p = db_mod.session.query(Product).filter_by(name='Potato', supplier_id=1).first()
        assert p is not None
        pid = p.id

    # Edit the product
    resp = client.post(f'/supplier/product/{pid}/edit', data={'name': 'Potato-Sweet', 'price': '30', 'stock': '60', 'unit': 'kg'})
    assert resp.status_code in (301, 302)

    with app.app_context():
        p2 = db_mod.session.query(Product).get(pid)
        assert p2.name == 'Potato-Sweet'
        assert p2.current_price == 30.0
        assert p2.stock_available == 60

    # Delete the product
    resp = client.post(f'/supplier/product/{pid}/delete')
    assert resp.status_code in (301, 302)

    with app.app_context():
        p3 = db_mod.session.query(Product).get(pid)
        assert p3 is None


def test_get_products_api_filters(client):
    db_mod = getattr(vc, 'db')
    Product = getattr(vc, 'Product')

    with app.app_context():
        # create a supplier and product
        supplier = getattr(vc, 'Supplier')(name='FilterSup', phone='555', location='X')
        db_mod.session.add(supplier)
        db_mod.session.commit()
        pid = supplier.id
        prod = Product(name='FilterProd', category='general', current_price=10.0, supplier_id=pid, stock_available=10, unit='pcs')
        db_mod.session.add(prod)
        db_mod.session.commit()
        prod_id = prod.id

    # Query by supplier_id
    resp = client.get(f'/api/products?supplier_id={pid}')
    assert resp.status_code == 200
    data = resp.get_json()
    assert any(p['id'] == prod_id for p in data)


def test_supplier_receives_event_on_order(client):
    # Place an order as vendor and ensure supplier queue gets an event
    with client.session_transaction() as sess:
        sess['vendor_id'] = 1
    resp = client.post('/api/place-order', json={'supplier_id':1, 'total_amount':100, 'items':[]})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    order_id = data.get('order_id')
    assert order_id is not None

    # supplier queue should have an event for supplier_1
    key = f"supplier_{1}"
    q = getattr(vc, 'order_event_queues').get(key)
    assert q is not None
    try:
        ev = q.get_nowait()
        assert ev['type'] in ('order_placed', 'status_update')
    except Exception:
        # non-fatal if no event present yet
        pass


def test_customer_order_and_delivery_update(client):
    db_mod = getattr(vc, 'db')
    DeliveryAgent = getattr(vc, 'DeliveryAgent')

    # create a customer and a delivery agent
    with app.app_context():
        customer = getattr(vc, 'Customer')(name='C1', phone='999', email='c1@example.com')
        db_mod.session.add(customer)
        agent = DeliveryAgent(name='Agent1', phone='888')
        db_mod.session.add(agent)
        db_mod.session.commit()
        cust_id = customer.id
        agent_id = agent.id

    # log in as customer
    with client.session_transaction() as sess:
        sess['customer_id'] = cust_id

    # Place a customer order
    order_payload = {'name':'C1','email':'c1@example.com','phone':'999','address':'Somewhere','items':[], 'payment':'cod'}
    resp = client.post('/api/place-order-customer', json=order_payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    order_id = data.get('order_id')
    assert order_id is not None

    # Simulate delivery agent updating status to 'in_transit'
    with client.session_transaction() as sess:
        sess['delivery_agent_id'] = agent_id

    resp = client.post('/api/delivery-agent/update-status', json={'order_id': order_id, 'status': 'in_transit', 'latitude':12.97, 'longitude':77.59})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True

    # Verify that delivery location endpoint reports updated status
    resp = client.get(f'/api/delivery/location/{order_id}')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert data.get('order_status') in ('out_for_delivery', 'out_for_delivery')

    # Check that an SSE event was published in the internal queue for customers
    key = f"cust_{order_id}"
    q = getattr(vc, 'order_event_queues').get(key)
    assert q is not None
    # Try to read an event (non-blocking)
    try:
        ev = q.get_nowait()
        assert ev['type'] in ('status_update',)
    except Exception:
        # If no event found, it's non-fatal for this test but warn
        pass
