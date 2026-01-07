import pytest
import importlib.util
import os
import time

# Import app module same way other tests do
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
    with app.app_context():
        try:
            db_mod.drop_all()
        except Exception:
            pass
        db_mod.create_all()
    with app.test_client() as client:
        yield client


def _pop_event_from_queue(key, timeout=1.0):
    q = vc.order_event_queues.get(key)
    if not q:
        return None
    try:
        return q.get(timeout=timeout)
    except Exception:
        return None


def test_end_to_end_vendor_supplier_delivery_customer_flow(client):
    db = getattr(vc, 'db')
    Supplier = getattr(vc, 'Supplier')
    DeliveryAgent = getattr(vc, 'DeliveryAgent')
    Customer = getattr(vc, 'Customer')
    CustomerOrder = getattr(vc, 'CustomerOrder')
    Order = getattr(vc, 'Order')

    # Create supplier, agent and customer
    with app.app_context():
        s = Supplier(name='TestSup', phone='000111222', location='here')
        agent = DeliveryAgent(name='DAgent', phone='999888777')
        cust = Customer(name='Cust', phone='123456789')
        db.session.add_all([s, agent, cust])
        db.session.commit()
        supplier_id = s.id
        agent_id = agent.id
        cust_id = cust.id

    # 1) Vendor places a supplier order
    with client.session_transaction() as sess:
        sess['vendor_id'] = 1

    resp = client.post('/api/place-order', json={'supplier_id': supplier_id, 'total_amount': 50, 'items': []})
    assert resp.status_code == 200
    order_id = resp.get_json().get('order_id')
    assert order_id is not None

    # Event for order placed should be published to per-order queue
    ev = _pop_event_from_queue(order_id, timeout=1.0)
    assert ev is not None and ev.get('type') == 'order_placed'

    # 2) Supplier confirms the order
    with client.session_transaction() as sess:
        sess.pop('vendor_id', None)
        sess['supplier_id'] = supplier_id

    resp = client.post(f'/api/supplier/orders/{order_id}/action', json={'action': 'confirm'})
    assert resp.status_code == 200
    assert resp.get_json().get('status') == 'confirmed'

    # Confirm event published to per-order queue
    ev = _pop_event_from_queue(order_id, timeout=1.0)
    assert ev is not None and ev.get('type') == 'status_update'

    # Also supplier-level queue should have received the status update (may have earlier order_placed events)
    sup_key = f"supplier_{supplier_id}"

    # Wait for a status_update event on supplier queue
    found = None
    for _ in range(6):
        sup_ev = _pop_event_from_queue(sup_key, timeout=0.5)
        if not sup_ev:
            break
        if sup_ev.get('type') == 'status_update':
            found = sup_ev
            break
    assert found is not None and found.get('type') == 'status_update'

    # 3) Customer places an order
    with client.session_transaction() as sess:
        sess.pop('supplier_id', None)
        sess['customer_id'] = cust_id

    payload = {'name': 'Cust', 'email': 'cust@example.com', 'phone': '123456789', 'address': 'Some Addr', 'items': [], 'payment': 'cod'}
    resp = client.post('/api/place-order-customer', json=payload)
    assert resp.status_code == 200
    cust_order_id = resp.get_json().get('order_id')
    assert cust_order_id is not None

    # Customer initial event should be available on cust_<id>
    cust_ev = _pop_event_from_queue(f'cust_{cust_order_id}', timeout=1.0)
    assert cust_ev is not None and cust_ev.get('type') == 'status_update'

    # 4) Delivery agent accepts the customer order
    with client.session_transaction() as sess:
        sess['delivery_agent_id'] = agent_id

    resp = client.post('/api/delivery-agent/accept-order', json={'order_id': cust_order_id, 'latitude': 12.97, 'longitude': 77.59})
    assert resp.status_code == 200
    assert resp.get_json().get('order_id') == cust_order_id

    # DB should show order assigned to agent and status ready
    with app.app_context():
        o = db.session.query(CustomerOrder).filter_by(id=cust_order_id).first()
        assert o.delivery_agent_id == agent_id
        assert o.status == 'ready'

    # Cache should have entry for order_{id}
    cache = getattr(vc, 'delivery_location_cache')
    key = f'order_{cust_order_id}'
    assert key in cache and cache[key].get('status') == 'ready'

    # 5) Agent updates status to in_transit
    resp = client.post('/api/delivery-agent/update-status', json={'order_id': cust_order_id, 'status': 'in_transit', 'latitude': 12.98, 'longitude': 77.60})
    assert resp.status_code == 200
    assert 'order_status' in resp.get_json()
    assert resp.get_json().get('order_status') in ('out_for_delivery', 'out_for_delivery')

    # Customer event for status update should be published
    cust_ev2 = _pop_event_from_queue(f'cust_{cust_order_id}', timeout=1.0)
    assert cust_ev2 is not None and cust_ev2.get('type') == 'status_update'

    # 6) Customer SSE endpoint protected
    with client.session_transaction() as sess:
        sess.pop('customer_id', None)
    resp = client.get(f'/api/customer/order/{cust_order_id}/events')
    assert resp.status_code == 401

    with client.session_transaction() as sess:
        sess['customer_id'] = cust_id
    resp = client.get(f'/api/customer/order/{cust_order_id}/events')
    assert resp.status_code == 200
    assert resp.headers.get('Content-Type', '').startswith('text/event-stream')

    # Final DB checks
    with app.app_context():
        # Validate supplier order exists and has confirmed status
        sup_order = Order.query.get(order_id)
        assert sup_order is not None and sup_order.status == 'confirmed'

        # Validate customer order status updated
        corder = CustomerOrder.query.get(cust_order_id)
        assert corder is not None and corder.status in ('out_for_delivery', 'ready', 'delivered', 'confirmed', 'preparing')
