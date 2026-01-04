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
