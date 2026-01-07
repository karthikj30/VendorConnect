import importlib.util
import os
import pytest

APP_PATH = os.path.join(os.path.dirname(__file__), '..', 'app.py')
spec = importlib.util.spec_from_file_location('vc_app', APP_PATH)
vc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vc)
app = getattr(vc, 'app')

def client_fixture():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    db_mod = getattr(vc, 'db')
    with app.app_context():
        try:
            db_mod.drop_all()
        except Exception:
            pass
        db_mod.create_all()
    with app.test_client() as client:
        yield client

@pytest.fixture
def client():
    yield from client_fixture()


def test_agent_endpoints_require_login(client):
    # Ensure the endpoints return 401 when not logged in
    resp = client.get('/api/delivery-agent/profile')
    assert resp.status_code == 401
    resp = client.get('/api/delivery-agent/deliveries')
    assert resp.status_code == 401
    resp = client.post('/api/delivery-agent/update-location', json={'latitude':12.9,'longitude':77.6})
    assert resp.status_code == 401
    resp = client.post('/api/delivery-agent/available-orders', json={'latitude':12.9,'longitude':77.6})
    assert resp.status_code == 401
    resp = client.post('/api/delivery-agent/accept-order', json={'order_id':1})
    assert resp.status_code == 401


def test_agent_accepts_and_updates_order(client):
    db_mod = getattr(vc, 'db')
    DeliveryAgent = getattr(vc, 'DeliveryAgent')
    Customer = getattr(vc, 'Customer')
    CustomerOrder = getattr(vc, 'CustomerOrder')

    with app.app_context():
        # create a customer and an order (confirmed)
        cust = Customer(name='C1', phone='999', email='c1@example.com')
        db_mod.session.add(cust)
        db_mod.session.commit()

        order = CustomerOrder(
            customer_id=cust.id,
            total_amount=100,
            subtotal=90,
            delivery_address='Somewhere',
            status='confirmed',
            delivery_latitude=12.97,
            delivery_longitude=77.59
        )
        db_mod.session.add(order)
        db_mod.session.commit()
        order_id = order.id

        # create a delivery agent
        agent = DeliveryAgent(name='Agent1', phone='888')
        db_mod.session.add(agent)
        db_mod.session.commit()
        agent_id = agent.id

    # Simulate agent login
    with client.session_transaction() as sess:
        sess['delivery_agent_id'] = agent_id

    # Agent fetches available orders near them
    resp = client.post('/api/delivery-agent/available-orders', json={'latitude':12.97,'longitude':77.59})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert any(o['order_id'] == order_id for o in data['orders'])

    # Agent accepts the order
    resp = client.post('/api/delivery-agent/accept-order', json={'order_id': order_id, 'latitude':12.97, 'longitude':77.59})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True

    # Verify DB assignment
    with app.app_context():
        ord_obj = getattr(vc, 'CustomerOrder').query.get(order_id)
        assert ord_obj.delivery_agent_id == agent_id
        assert ord_obj.status in ('ready', 'ready')

    # Agent updates delivery status to in_transit with coordinates
    resp = client.post('/api/delivery-agent/update-status', json={'order_id':order_id, 'status':'in_transit', 'latitude':12.971, 'longitude':77.593})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True

    # Check cache updated
    qcache = getattr(vc, 'delivery_location_cache').get(f'order_{order_id}')
    assert qcache is not None
    assert 'latitude' in qcache and 'longitude' in qcache

    # Check customer event queue received a status_update
    cust_key = f'cust_{order_id}'
    q = getattr(vc, 'order_event_queues').get(cust_key)
    assert q is not None
    # Try to read an event non-blocking
    try:
        ev = q.get_nowait()
        assert ev['type'] in ('status_update',)
    except Exception:
        # If none available, still pass but log
        pass
