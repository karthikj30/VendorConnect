from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import json
import random
from datetime import datetime, timedelta
import requests
from werkzeug.security import generate_password_hash, check_password_hash
import os  # ✅ add this

basedir = os.path.abspath(os.path.dirname(__file__))

# Configure Flask app with explicit instance path pointing to the repo-level instance folder
app = Flask(__name__, instance_path=os.path.join(basedir, '../instance'))
app.config['SECRET_KEY'] = 'vendorconnect_secret_key_2024'

# Ensure the instance directory exists (required for SQLite file creation)
os.makedirs(app.instance_path, exist_ok=True)

# Use an absolute path inside the instance directory for the SQLite database
db_path = os.path.join(app.instance_path, 'vendorconnect.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)


# Database Models
class Vendor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    business_type = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    rating = db.Column(db.Float, default=0.0)
    verification_status = db.Column(db.Boolean, default=False)
    hygiene_rating = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    current_price = db.Column(db.Float, nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    stock_available = db.Column(db.Integer, default=0)
    unit = db.Column(db.String(20), default='kg')

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    order_type = db.Column(db.String(20), default='individual')  # individual or group
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    price_per_unit = db.Column(db.Float, nullable=False)

class GroupOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    target_quantity = db.Column(db.Float, nullable=False)
    current_quantity = db.Column(db.Float, default=0)
    price_per_unit = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class GroupOrderParticipant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_order_id = db.Column(db.Integer, db.ForeignKey('group_order.id'), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)

# Sample data for demonstration
def create_sample_data():
    # Create sample suppliers
    suppliers_data = [
        {'name': 'Krishna Mandi', 'phone': '9876543210', 'location': 'Mumbai Central', 'rating': 4.5, 'verification_status': True, 'hygiene_rating': 4.2},
        {'name': 'Fresh Farm Supplies', 'phone': '9876543211', 'location': 'Andheri West', 'rating': 4.8, 'verification_status': True, 'hygiene_rating': 4.6},
        {'name': 'Quality Vegetables', 'phone': '9876543212', 'location': 'Bandra East', 'rating': 4.3, 'verification_status': True, 'hygiene_rating': 4.0},
        {'name': 'Organic Market', 'phone': '9876543213', 'location': 'Juhu', 'rating': 4.7, 'verification_status': True, 'hygiene_rating': 4.8},
        {'name': 'Local Grocery Store', 'phone': '9876543214', 'location': 'Santacruz', 'rating': 4.1, 'verification_status': False, 'hygiene_rating': 3.8}
    ]
    
    for supplier_data in suppliers_data:
        supplier = Supplier(**supplier_data)
        db.session.add(supplier)
    
    db.session.commit()
    
    # Create sample products
    products_data = [
        {'name': 'Tomatoes', 'category': 'vegetables', 'current_price': 28.0, 'supplier_id': 1, 'stock_available': 500, 'unit': 'kg'},
        {'name': 'Onions', 'category': 'vegetables', 'current_price': 35.0, 'supplier_id': 1, 'stock_available': 300, 'unit': 'kg'},
        {'name': 'Potatoes', 'category': 'vegetables', 'current_price': 25.0, 'supplier_id': 2, 'stock_available': 400, 'unit': 'kg'},
        {'name': 'Cooking Oil', 'category': 'oils', 'current_price': 120.0, 'supplier_id': 3, 'stock_available': 100, 'unit': 'liter'},
        {'name': 'Rice', 'category': 'grains', 'current_price': 45.0, 'supplier_id': 4, 'stock_available': 200, 'unit': 'kg'},
        {'name': 'Lentils', 'category': 'pulses', 'current_price': 85.0, 'supplier_id': 5, 'stock_available': 150, 'unit': 'kg'},
        {'name': 'Milk', 'category': 'dairy', 'current_price': 60.0, 'supplier_id': 2, 'stock_available': 100, 'unit': 'liter'},
        {'name': 'Sugar', 'category': 'essentials', 'current_price': 45.0, 'supplier_id': 3, 'stock_available': 200, 'unit': 'kg'},
        {'name': 'Ice Cream Mix', 'category': 'ice_cream', 'current_price': 150.0, 'supplier_id': 4, 'stock_available': 50, 'unit': 'kg'},
        {'name': 'Vanilla Essence', 'category': 'ice_cream', 'current_price': 500.0, 'supplier_id': 5, 'stock_available': 20, 'unit': 'liter'},
        {'name': 'Chocolate Syrup', 'category': 'ice_cream', 'current_price': 300.0, 'supplier_id': 1, 'stock_available': 30, 'unit': 'liter'},
        {'name': 'Strawberry Syrup', 'category': 'ice_cream', 'current_price': 280.0, 'supplier_id': 2, 'stock_available': 25, 'unit': 'liter'},
        {'name': 'Mango Pulp', 'category': 'ice_cream', 'current_price': 120.0, 'supplier_id': 3, 'stock_available': 40, 'unit': 'kg'},
        {'name': 'Pista (Pistachio)', 'category': 'ice_cream', 'current_price': 1200.0, 'supplier_id': 4, 'stock_available': 15, 'unit': 'kg'},
        {'name': 'Badam (Almonds)', 'category': 'ice_cream', 'current_price': 900.0, 'supplier_id': 5, 'stock_available': 20, 'unit': 'kg'},
        {'name': 'Kesar (Saffron)', 'category': 'ice_cream', 'current_price': 2500.0, 'supplier_id': 1, 'stock_available': 5, 'unit': 'kg'},
        {'name': 'Rose Essence', 'category': 'ice_cream', 'current_price': 400.0, 'supplier_id': 2, 'stock_available': 15, 'unit': 'liter'},
        {'name': 'Coconut Powder', 'category': 'ice_cream', 'current_price': 180.0, 'supplier_id': 3, 'stock_available': 30, 'unit': 'kg'},
        {'name': 'Dry Fruits Mix', 'category': 'ice_cream', 'current_price': 800.0, 'supplier_id': 4, 'stock_available': 10, 'unit': 'kg'},
        {'name': 'Ice Cream Cones', 'category': 'ice_cream', 'current_price': 200.0, 'supplier_id': 5, 'stock_available': 100, 'unit': 'pack'},
        {'name': 'Sprinkles', 'category': 'ice_cream', 'current_price': 150.0, 'supplier_id': 1, 'stock_available': 50, 'unit': 'pack'},
        {'name': 'Chocolate Chips', 'category': 'ice_cream', 'current_price': 350.0, 'supplier_id': 2, 'stock_available': 25, 'unit': 'kg'},
        {'name': 'Waffle Mix', 'category': 'ice_cream', 'current_price': 120.0, 'supplier_id': 3, 'stock_available': 35, 'unit': 'kg'},
        # Add more products for different business types
        {'name': 'Chickpeas', 'category': 'chaat', 'current_price': 65.0, 'supplier_id': 1, 'stock_available': 100, 'unit': 'kg'},
        {'name': 'Tamarind', 'category': 'chaat', 'current_price': 120.0, 'supplier_id': 2, 'stock_available': 50, 'unit': 'kg'},
        {'name': 'Mint Chutney', 'category': 'chaat', 'current_price': 80.0, 'supplier_id': 3, 'stock_available': 30, 'unit': 'kg'},
        {'name': 'Sev', 'category': 'chaat', 'current_price': 90.0, 'supplier_id': 4, 'stock_available': 40, 'unit': 'kg'},
        {'name': 'Papdi', 'category': 'chaat', 'current_price': 150.0, 'supplier_id': 5, 'stock_available': 25, 'unit': 'kg'},
        {'name': 'Boondi', 'category': 'chaat', 'current_price': 70.0, 'supplier_id': 1, 'stock_available': 60, 'unit': 'kg'},
        {'name': 'Pomegranate Seeds', 'category': 'chaat', 'current_price': 200.0, 'supplier_id': 2, 'stock_available': 20, 'unit': 'kg'},
        {'name': 'Coriander Leaves', 'category': 'chaat', 'current_price': 40.0, 'supplier_id': 3, 'stock_available': 30, 'unit': 'kg'},
        {'name': 'Green Chutney', 'category': 'chaat', 'current_price': 60.0, 'supplier_id': 4, 'stock_available': 35, 'unit': 'kg'},
        {'name': 'Sweet Chutney', 'category': 'chaat', 'current_price': 80.0, 'supplier_id': 5, 'stock_available': 30, 'unit': 'kg'},
        {'name': 'Curd', 'category': 'chaat', 'current_price': 50.0, 'supplier_id': 1, 'stock_available': 80, 'unit': 'liter'},
        {'name': 'Chaat Masala', 'category': 'chaat', 'current_price': 120.0, 'supplier_id': 2, 'stock_available': 15, 'unit': 'kg'},
        {'name': 'Rice Batter', 'category': 'dosa', 'current_price': 40.0, 'supplier_id': 4, 'stock_available': 200, 'unit': 'kg'},
        {'name': 'Urad Dal', 'category': 'dosa', 'current_price': 90.0, 'supplier_id': 5, 'stock_available': 100, 'unit': 'kg'},
        {'name': 'Potato Filling', 'category': 'dosa', 'current_price': 35.0, 'supplier_id': 1, 'stock_available': 150, 'unit': 'kg'},
        {'name': 'Coconut Chutney', 'category': 'dosa', 'current_price': 80.0, 'supplier_id': 2, 'stock_available': 40, 'unit': 'kg'},
        {'name': 'Sambar Powder', 'category': 'dosa', 'current_price': 150.0, 'supplier_id': 3, 'stock_available': 20, 'unit': 'kg'},
        {'name': 'Sambar Vegetables', 'category': 'dosa', 'current_price': 45.0, 'supplier_id': 4, 'stock_available': 80, 'unit': 'kg'},
        {'name': 'Onion Chutney', 'category': 'dosa', 'current_price': 60.0, 'supplier_id': 5, 'stock_available': 30, 'unit': 'kg'},
        {'name': 'Tomato Chutney', 'category': 'dosa', 'current_price': 55.0, 'supplier_id': 1, 'stock_available': 35, 'unit': 'kg'},
        {'name': 'Ginger Chutney', 'category': 'dosa', 'current_price': 70.0, 'supplier_id': 2, 'stock_available': 25, 'unit': 'kg'},
        {'name': 'Dosa Batter Mix', 'category': 'dosa', 'current_price': 120.0, 'supplier_id': 3, 'stock_available': 50, 'unit': 'kg'},
        {'name': 'Potato Filling', 'category': 'samosa', 'current_price': 35.0, 'supplier_id': 1, 'stock_available': 150, 'unit': 'kg'},
        {'name': 'Samosa Sheets', 'category': 'samosa', 'current_price': 200.0, 'supplier_id': 2, 'stock_available': 50, 'unit': 'pack'},
        {'name': 'Green Peas', 'category': 'samosa', 'current_price': 45.0, 'supplier_id': 3, 'stock_available': 80, 'unit': 'kg'},
        {'name': 'Samosa Masala', 'category': 'samosa', 'current_price': 180.0, 'supplier_id': 4, 'stock_available': 15, 'unit': 'kg'},
        {'name': 'Coriander Powder', 'category': 'samosa', 'current_price': 160.0, 'supplier_id': 5, 'stock_available': 20, 'unit': 'kg'},
        {'name': 'Cumin Seeds', 'category': 'samosa', 'current_price': 200.0, 'supplier_id': 1, 'stock_available': 25, 'unit': 'kg'},
        {'name': 'Garam Masala', 'category': 'samosa', 'current_price': 220.0, 'supplier_id': 2, 'stock_available': 12, 'unit': 'kg'},
        {'name': 'Red Chili Powder', 'category': 'samosa', 'current_price': 140.0, 'supplier_id': 3, 'stock_available': 30, 'unit': 'kg'},
        {'name': 'Turmeric Powder', 'category': 'samosa', 'current_price': 120.0, 'supplier_id': 4, 'stock_available': 40, 'unit': 'kg'},
        {'name': 'Ginger Garlic Paste', 'category': 'samosa', 'current_price': 80.0, 'supplier_id': 5, 'stock_available': 50, 'unit': 'kg'},
        {'name': 'Potato Filling', 'category': 'vada_pav', 'current_price': 35.0, 'supplier_id': 1, 'stock_available': 150, 'unit': 'kg'},
        {'name': 'Pav Bread', 'category': 'vada_pav', 'current_price': 25.0, 'supplier_id': 2, 'stock_available': 200, 'unit': 'pack'},
        {'name': 'Besan', 'category': 'vada_pav', 'current_price': 70.0, 'supplier_id': 3, 'stock_available': 100, 'unit': 'kg'},
        {'name': 'Vada Pav Masala', 'category': 'vada_pav', 'current_price': 160.0, 'supplier_id': 4, 'stock_available': 18, 'unit': 'kg'},
        {'name': 'Green Chutney', 'category': 'vada_pav', 'current_price': 60.0, 'supplier_id': 5, 'stock_available': 35, 'unit': 'kg'},
        {'name': 'Red Chutney', 'category': 'vada_pav', 'current_price': 65.0, 'supplier_id': 1, 'stock_available': 30, 'unit': 'kg'},
        {'name': 'Garlic Chutney', 'category': 'vada_pav', 'current_price': 75.0, 'supplier_id': 2, 'stock_available': 25, 'unit': 'kg'},
        {'name': 'Mustard Seeds', 'category': 'vada_pav', 'current_price': 180.0, 'supplier_id': 3, 'stock_available': 20, 'unit': 'kg'},
        {'name': 'Curry Leaves', 'category': 'vada_pav', 'current_price': 90.0, 'supplier_id': 4, 'stock_available': 15, 'unit': 'kg'},
        {'name': 'Asafoetida', 'category': 'vada_pav', 'current_price': 300.0, 'supplier_id': 5, 'stock_available': 8, 'unit': 'kg'},
        {'name': 'Tea Leaves', 'category': 'tea', 'current_price': 180.0, 'supplier_id': 4, 'stock_available': 50, 'unit': 'kg'},
        {'name': 'Ginger', 'category': 'tea', 'current_price': 60.0, 'supplier_id': 5, 'stock_available': 40, 'unit': 'kg'},
        {'name': 'Cardamom', 'category': 'tea', 'current_price': 1200.0, 'supplier_id': 1, 'stock_available': 10, 'unit': 'kg'},
        {'name': 'Black Pepper', 'category': 'tea', 'current_price': 400.0, 'supplier_id': 2, 'stock_available': 25, 'unit': 'kg'},
        {'name': 'Cinnamon', 'category': 'tea', 'current_price': 600.0, 'supplier_id': 3, 'stock_available': 15, 'unit': 'kg'},
        {'name': 'Cloves', 'category': 'tea', 'current_price': 800.0, 'supplier_id': 4, 'stock_available': 12, 'unit': 'kg'},
        {'name': 'Bay Leaves', 'category': 'tea', 'current_price': 300.0, 'supplier_id': 5, 'stock_available': 20, 'unit': 'kg'},
        {'name': 'Tulsi Leaves', 'category': 'tea', 'current_price': 200.0, 'supplier_id': 1, 'stock_available': 30, 'unit': 'kg'},
        {'name': 'Lemon Grass', 'category': 'tea', 'current_price': 250.0, 'supplier_id': 2, 'stock_available': 18, 'unit': 'kg'},
        {'name': 'Tea Masala', 'category': 'tea', 'current_price': 350.0, 'supplier_id': 3, 'stock_available': 22, 'unit': 'kg'},
        {'name': 'Oranges', 'category': 'juice', 'current_price': 80.0, 'supplier_id': 2, 'stock_available': 100, 'unit': 'kg'},
        {'name': 'Apples', 'category': 'juice', 'current_price': 120.0, 'supplier_id': 3, 'stock_available': 80, 'unit': 'kg'},
        {'name': 'Carrots', 'category': 'juice', 'current_price': 40.0, 'supplier_id': 4, 'stock_available': 120, 'unit': 'kg'},
        {'name': 'Beetroot', 'category': 'juice', 'current_price': 35.0, 'supplier_id': 5, 'stock_available': 90, 'unit': 'kg'},
        {'name': 'Cucumber', 'category': 'juice', 'current_price': 30.0, 'supplier_id': 1, 'stock_available': 150, 'unit': 'kg'},
        {'name': 'Spinach', 'category': 'juice', 'current_price': 25.0, 'supplier_id': 2, 'stock_available': 80, 'unit': 'kg'},
        {'name': 'Mint Leaves', 'category': 'juice', 'current_price': 45.0, 'supplier_id': 3, 'stock_available': 40, 'unit': 'kg'},
        {'name': 'Ginger', 'category': 'juice', 'current_price': 60.0, 'supplier_id': 4, 'stock_available': 40, 'unit': 'kg'},
        {'name': 'Honey', 'category': 'juice', 'current_price': 400.0, 'supplier_id': 5, 'stock_available': 25, 'unit': 'liter'},
        {'name': 'Rock Salt', 'category': 'juice', 'current_price': 20.0, 'supplier_id': 1, 'stock_available': 100, 'unit': 'kg'},
        {'name': 'Black Salt', 'category': 'juice', 'current_price': 25.0, 'supplier_id': 2, 'stock_available': 80, 'unit': 'kg'},
        {'name': 'Lemons', 'category': 'juice', 'current_price': 60.0, 'supplier_id': 5, 'stock_available': 60, 'unit': 'kg'},
        # Fruits for ice cream
        {'name': 'Strawberries', 'category': 'fruits', 'current_price': 200.0, 'supplier_id': 1, 'stock_available': 30, 'unit': 'kg'},
        {'name': 'Mangoes', 'category': 'fruits', 'current_price': 80.0, 'supplier_id': 2, 'stock_available': 50, 'unit': 'kg'},
        {'name': 'Bananas', 'category': 'fruits', 'current_price': 40.0, 'supplier_id': 3, 'stock_available': 100, 'unit': 'kg'},
        {'name': 'Pineapple', 'category': 'fruits', 'current_price': 60.0, 'supplier_id': 4, 'stock_available': 40, 'unit': 'kg'},
        {'name': 'Blueberries', 'category': 'fruits', 'current_price': 400.0, 'supplier_id': 5, 'stock_available': 15, 'unit': 'kg'},
        {'name': 'Kiwi', 'category': 'fruits', 'current_price': 300.0, 'supplier_id': 1, 'stock_available': 20, 'unit': 'kg'},
        {'name': 'Oranges', 'category': 'fruits', 'current_price': 80.0, 'supplier_id': 2, 'stock_available': 100, 'unit': 'kg'},
        {'name': 'Apples', 'category': 'fruits', 'current_price': 120.0, 'supplier_id': 3, 'stock_available': 80, 'unit': 'kg'}
    ]
    
    for product_data in products_data:
        product = Product(**product_data)
        db.session.add(product)
    
    db.session.commit()

def create_sample_orders():
    """Create sample orders for demonstration"""
    # Check if orders already exist
    if Order.query.first():
        return
    
    # Create sample orders for different vendors
    sample_orders = [
        # Vendor 1 orders (ice cream vendor)
        {'vendor_id': 1, 'supplier_id': 1, 'total_amount': 1200.0, 'status': 'completed', 'order_type': 'individual', 'created_at': datetime.now() - timedelta(days=2)},
        {'vendor_id': 1, 'supplier_id': 2, 'total_amount': 800.0, 'status': 'completed', 'order_type': 'individual', 'created_at': datetime.now() - timedelta(days=5)},
        {'vendor_id': 1, 'supplier_id': 3, 'total_amount': 1500.0, 'status': 'completed', 'order_type': 'group', 'created_at': datetime.now() - timedelta(days=8)},
        {'vendor_id': 1, 'supplier_id': 4, 'total_amount': 900.0, 'status': 'pending', 'order_type': 'individual', 'created_at': datetime.now() - timedelta(days=1)},
        {'vendor_id': 1, 'supplier_id': 5, 'total_amount': 1100.0, 'status': 'completed', 'order_type': 'group', 'created_at': datetime.now() - timedelta(days=10)},
        
        # Vendor 2 orders (chaat vendor)
        {'vendor_id': 2, 'supplier_id': 1, 'total_amount': 1800.0, 'status': 'completed', 'order_type': 'individual', 'created_at': datetime.now() - timedelta(days=3)},
        {'vendor_id': 2, 'supplier_id': 2, 'total_amount': 1200.0, 'status': 'completed', 'order_type': 'group', 'created_at': datetime.now() - timedelta(days=6)},
        {'vendor_id': 2, 'supplier_id': 3, 'total_amount': 950.0, 'status': 'completed', 'order_type': 'individual', 'created_at': datetime.now() - timedelta(days=9)},
        
        # Vendor 3 orders (dosa vendor)
        {'vendor_id': 3, 'supplier_id': 1, 'total_amount': 1400.0, 'status': 'completed', 'order_type': 'individual', 'created_at': datetime.now() - timedelta(days=4)},
        {'vendor_id': 3, 'supplier_id': 2, 'total_amount': 1600.0, 'status': 'completed', 'order_type': 'group', 'created_at': datetime.now() - timedelta(days=7)},
        {'vendor_id': 3, 'supplier_id': 3, 'total_amount': 750.0, 'status': 'pending', 'order_type': 'individual', 'created_at': datetime.now() - timedelta(days=2)},
    ]
    
    for order_data in sample_orders:
        order = Order(**order_data)
        db.session.add(order)
    
    db.session.commit()
    
    # Create sample order items
    sample_order_items = [
        # Order 1 items
        {'order_id': 1, 'product_id': 1, 'quantity': 20.0, 'price_per_unit': 28.0},  # Tomatoes
        {'order_id': 1, 'product_id': 2, 'quantity': 15.0, 'price_per_unit': 35.0},  # Onions
        
        # Order 2 items
        {'order_id': 2, 'product_id': 4, 'quantity': 5.0, 'price_per_unit': 120.0},  # Cooking Oil
        
        # Order 3 items
        {'order_id': 3, 'product_id': 5, 'quantity': 25.0, 'price_per_unit': 45.0},  # Rice
        {'order_id': 3, 'product_id': 6, 'quantity': 10.0, 'price_per_unit': 85.0},  # Lentils
        
        # Order 4 items
        {'order_id': 4, 'product_id': 9, 'quantity': 4.0, 'price_per_unit': 150.0},  # Ice Cream Mix
        {'order_id': 4, 'product_id': 10, 'quantity': 1.0, 'price_per_unit': 500.0}, # Vanilla Essence
        
        # Order 5 items
        {'order_id': 5, 'product_id': 11, 'quantity': 2.0, 'price_per_unit': 300.0}, # Chocolate Syrup
        {'order_id': 5, 'product_id': 12, 'quantity': 2.0, 'price_per_unit': 280.0}, # Strawberry Syrup
        
        # Order 6 items
        {'order_id': 6, 'product_id': 25, 'quantity': 20.0, 'price_per_unit': 65.0},  # Chickpeas
        {'order_id': 6, 'product_id': 26, 'quantity': 5.0, 'price_per_unit': 120.0},  # Tamarind
        
        # Order 7 items
        {'order_id': 7, 'product_id': 27, 'quantity': 10.0, 'price_per_unit': 80.0},  # Mint Chutney
        {'order_id': 7, 'product_id': 28, 'quantity': 8.0, 'price_per_unit': 90.0},   # Sev
        
        # Order 8 items
        {'order_id': 8, 'product_id': 29, 'quantity': 5.0, 'price_per_unit': 150.0},  # Papdi
        {'order_id': 8, 'product_id': 30, 'quantity': 10.0, 'price_per_unit': 70.0},  # Boondi
        
        # Order 9 items
        {'order_id': 9, 'product_id': 33, 'quantity': 25.0, 'price_per_unit': 40.0},  # Rice Batter
        {'order_id': 9, 'product_id': 34, 'quantity': 8.0, 'price_per_unit': 90.0},   # Urad Dal
        
        # Order 10 items
        {'order_id': 10, 'product_id': 35, 'quantity': 30.0, 'price_per_unit': 35.0}, # Potato Filling
        {'order_id': 10, 'product_id': 36, 'quantity': 15.0, 'price_per_unit': 80.0}, # Coconut Chutney
        
        # Order 11 items
        {'order_id': 11, 'product_id': 37, 'quantity': 3.0, 'price_per_unit': 150.0}, # Sambar Powder
        {'order_id': 11, 'product_id': 38, 'quantity': 15.0, 'price_per_unit': 45.0}, # Sambar Vegetables
    ]
    
    for item_data in sample_order_items:
        order_item = OrderItem(**item_data)
        db.session.add(order_item)
    
    db.session.commit()

def create_sample_vendors():
    """Create sample vendors for demonstration"""
    # Check if vendors already exist
    if Vendor.query.first():
        return
    
    # Create sample vendors
    sample_vendors = [
        {
            'name': 'Ice Cream Paradise',
            'phone': '9876543201',
            'location': 'Bandra West',
            'business_type': 'ice_cream',
            'password_hash': generate_password_hash('password123')
        },
        {
            'name': 'Chaat Corner',
            'phone': '9876543202',
            'location': 'Andheri East',
            'business_type': 'chaat',
            'password_hash': generate_password_hash('password123')
        },
        {
            'name': 'Dosa House',
            'phone': '9876543203',
            'location': 'Juhu',
            'business_type': 'dosa',
            'password_hash': generate_password_hash('password123')
        },
        {
            'name': 'Samosa King',
            'phone': '9876543204',
            'location': 'Santacruz',
            'business_type': 'samosa',
            'password_hash': generate_password_hash('password123')
        },
        {
            'name': 'Vada Pav Express',
            'phone': '9876543205',
            'location': 'Mumbai Central',
            'business_type': 'vada_pav',
            'password_hash': generate_password_hash('password123')
        },
        {
            'name': 'Tea Junction',
            'phone': '9876543206',
            'location': 'Khar West',
            'business_type': 'tea',
            'password_hash': generate_password_hash('password123')
        },
        {
            'name': 'Fresh Juice Bar',
            'phone': '9876543207',
            'location': 'Versova',
            'business_type': 'juice',
            'password_hash': generate_password_hash('password123')
        }
    ]
    
    for vendor_data in sample_vendors:
        vendor = Vendor(**vendor_data)
        db.session.add(vendor)
    
    db.session.commit()

# Business type to product category mapping
BUSINESS_TYPE_CATEGORIES = {
    'ice_cream': ['ice_cream', 'dairy', 'essentials', 'fruits'],
    'chaat': ['chaat', 'vegetables', 'essentials', 'dairy'],
    'dosa': ['dosa', 'vegetables', 'essentials', 'dairy'],
    'samosa': ['samosa', 'vegetables', 'essentials'],
    'vada_pav': ['vada_pav', 'vegetables', 'essentials'],
    'tea': ['tea', 'dairy', 'essentials'],
    'juice': ['juice', 'vegetables', 'essentials', 'fruits'],
    'other': ['vegetables', 'oils', 'grains', 'pulses', 'dairy', 'essentials', 'ice_cream', 'chaat', 'dosa', 'samosa', 'vada_pav', 'tea', 'juice', 'fruits']
}

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/vendor/login', methods=['GET', 'POST'])
def vendor_login():
    if request.method == 'POST':
        data = request.get_json()
        phone = data.get('phone')
        password = data.get('password')
        
        vendor = Vendor.query.filter_by(phone=phone).first()
        if vendor and check_password_hash(vendor.password_hash, password):
            session['vendor_id'] = vendor.id
            return jsonify({'success': True, 'message': 'Login successful'})
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'})
    
    return render_template('vendor_login.html')

@app.route('/vendor/register', methods=['GET', 'POST'])
def vendor_register():
    if request.method == 'POST':
        data = request.get_json()
        
        # Check if vendor already exists
        existing_vendor = Vendor.query.filter_by(phone=data.get('phone')).first()
        if existing_vendor:
            return jsonify({'success': False, 'message': 'Vendor already registered with this phone number'})
        
        # Create new vendor
        vendor = Vendor(
            name=data.get('name'),
            phone=data.get('phone'),
            location=data.get('location'),
            business_type=data.get('business_type'),
            password_hash=generate_password_hash(data.get('password'))
        )
        
        db.session.add(vendor)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Registration successful'})
    
    return render_template('vendor_register.html')

@app.route('/vendor/dashboard')
def vendor_dashboard():
    if 'vendor_id' not in session:
        return redirect(url_for('vendor_login'))
    
    vendor = Vendor.query.get(session['vendor_id'])
    return render_template('vendor_dashboard.html', vendor=vendor)

@app.route('/api/suppliers')
def get_suppliers():
    suppliers = Supplier.query.all()
    suppliers_data = []
    
    for supplier in suppliers:
        suppliers_data.append({
            'id': supplier.id,
            'name': supplier.name,
            'location': supplier.location,
            'rating': supplier.rating,
            'verification_status': supplier.verification_status,
            'hygiene_rating': supplier.hygiene_rating,
            'phone': supplier.phone
        })
    
    return jsonify(suppliers_data)

@app.route('/api/products')
def get_products():
    category = request.args.get('category', '')
    supplier_id = request.args.get('supplier_id', '')
    vendor_id = session.get('vendor_id')
    
    query = Product.query
    
    # If vendor is logged in, filter by their business type
    if vendor_id:
        vendor = Vendor.query.get(vendor_id)
        if vendor and vendor.business_type in BUSINESS_TYPE_CATEGORIES:
            # Get categories relevant to this business type
            relevant_categories = BUSINESS_TYPE_CATEGORIES[vendor.business_type]
            query = query.filter(Product.category.in_(relevant_categories))
    
    if category:
        query = query.filter_by(category=category)
    if supplier_id:
        query = query.filter_by(supplier_id=supplier_id)
    
    products = query.all()
    products_data = []
    
    for product in products:
        supplier = Supplier.query.get(product.supplier_id)
        products_data.append({
            'id': product.id,
            'name': product.name,
            'category': product.category,
            'current_price': product.current_price,
            'stock_available': product.stock_available,
            'unit': product.unit,
            'supplier_name': supplier.name,
            'supplier_location': supplier.location,
            'supplier_rating': supplier.rating
        })
    
    return jsonify(products_data)

@app.route('/api/group-orders')
def get_group_orders():
    group_orders = GroupOrder.query.filter_by(status='active').all()
    group_orders_data = []
    
    for group_order in group_orders:
        product = Product.query.get(group_order.product_id)
        participants_count = GroupOrderParticipant.query.filter_by(group_order_id=group_order.id).count()
        
        group_orders_data.append({
            'id': group_order.id,
            'product_name': product.name,
            'target_quantity': group_order.target_quantity,
            'current_quantity': group_order.current_quantity,
            'price_per_unit': group_order.price_per_unit,
            'participants_count': participants_count,
            'progress_percentage': (group_order.current_quantity / group_order.target_quantity) * 100
        })
    
    return jsonify(group_orders_data)

@app.route('/api/create-group-order', methods=['POST'])
def create_group_order():
    if 'vendor_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    data = request.get_json()
    
    group_order = GroupOrder(
        product_id=data.get('product_id'),
        target_quantity=data.get('target_quantity'),
        price_per_unit=data.get('price_per_unit')
    )
    
    db.session.add(group_order)
    db.session.commit()
    
    # Add the creator as first participant
    participant = GroupOrderParticipant(
        group_order_id=group_order.id,
        vendor_id=session['vendor_id'],
        quantity=data.get('quantity')
    )
    
    db.session.add(participant)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Group order created successfully'})

@app.route('/api/join-group-order', methods=['POST'])
def join_group_order():
    if 'vendor_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    data = request.get_json()
    
    # Check if already participating
    existing_participant = GroupOrderParticipant.query.filter_by(
        group_order_id=data.get('group_order_id'),
        vendor_id=session['vendor_id']
    ).first()
    
    if existing_participant:
        return jsonify({'success': False, 'message': 'Already participating in this group order'})
    
    participant = GroupOrderParticipant(
        group_order_id=data.get('group_order_id'),
        vendor_id=session['vendor_id'],
        quantity=data.get('quantity')
    )
    
    db.session.add(participant)
    
    # Update group order current quantity
    group_order = GroupOrder.query.get(data.get('group_order_id'))
    group_order.current_quantity += data.get('quantity')
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Joined group order successfully'})

@app.route('/api/price-alerts')
def get_price_alerts():
    vendor_id = session.get('vendor_id')
    vendor = None
    if vendor_id:
        vendor = Vendor.query.get(vendor_id)
    
    # Base alerts for all vendors
    alerts = [
        {
            'product': 'Tomatoes',
            'message': 'Aaj tomato ₹28/kg – lowest in Krishna Mandi',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
        },
        {
            'product': 'Onions',
            'message': 'Onion price dropped 15% in Fresh Farm Supplies',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
        },
        {
            'product': 'Potatoes',
            'message': 'Buy extra potatoes today – price may rise 20% tomorrow due to rains',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
        }
    ]
    
    # Add business-specific alerts
    if vendor and vendor.business_type:
        business_alerts = []
        
        if vendor.business_type == 'ice_cream':
            business_alerts = [
                {
                    'product': 'Ice Cream Mix',
                    'message': 'Ice cream mix price dropped 10% - stock up for summer!',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Strawberries',
                    'message': 'Fresh strawberries available at ₹180/kg - perfect for ice cream!',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Vanilla Essence',
                    'message': 'Premium vanilla essence 20% off this week only',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Chocolate Syrup',
                    'message': 'Bulk order discount on chocolate syrup - order 10+ liters',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                }
            ]
        elif vendor.business_type == 'chaat':
            business_alerts = [
                {
                    'product': 'Chickpeas',
                    'message': 'Chickpeas price dropped 15% - perfect for chaat!',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Sev',
                    'message': 'Fresh sev available at ₹85/kg - crispy and fresh!',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Pomegranate Seeds',
                    'message': 'Sweet pomegranate seeds 25% off - limited stock!',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Curd',
                    'message': 'Fresh curd available at ₹45/liter - perfect for dahi chaat',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                }
            ]
        elif vendor.business_type == 'dosa':
            business_alerts = [
                {
                    'product': 'Rice Batter',
                    'message': 'Rice batter price dropped 12% - stock up for weekend rush!',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Coconut Chutney',
                    'message': 'Fresh coconut chutney available at ₹75/kg',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Sambar Powder',
                    'message': 'Premium sambar powder 20% off - authentic taste!',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Urad Dal',
                    'message': 'Urad dal bulk discount - order 50kg+ for 10% off',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                }
            ]
        elif vendor.business_type == 'samosa':
            business_alerts = [
                {
                    'product': 'Samosa Sheets',
                    'message': 'Samosa sheets price dropped 8% - crispy and fresh!',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Potato Filling',
                    'message': 'Ready-made potato filling available at ₹32/kg',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Samosa Masala',
                    'message': 'Special samosa masala blend 15% off this week',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Green Peas',
                    'message': 'Fresh green peas available at ₹42/kg',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                }
            ]
        elif vendor.business_type == 'vada_pav':
            business_alerts = [
                {
                    'product': 'Pav Bread',
                    'message': 'Fresh pav bread available at ₹22/pack - soft and fluffy!',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Vada Pav Masala',
                    'message': 'Authentic vada pav masala 18% off - limited time!',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Besan',
                    'message': 'Besan price dropped 10% - perfect for vada batter',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Green Chutney',
                    'message': 'Spicy green chutney available at ₹55/kg',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                }
            ]
        elif vendor.business_type == 'tea':
            business_alerts = [
                {
                    'product': 'Tea Leaves',
                    'message': 'Premium tea leaves 15% off - strong and aromatic!',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Cardamom',
                    'message': 'Cardamom price dropped 12% - perfect for masala chai',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Ginger',
                    'message': 'Fresh ginger available at ₹55/kg - spicy and fresh!',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Tea Masala',
                    'message': 'Special tea masala blend 20% off - authentic taste!',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                }
            ]
        elif vendor.business_type == 'juice':
            business_alerts = [
                {
                    'product': 'Oranges',
                    'message': 'Sweet oranges available at ₹75/kg - perfect for juice!',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Carrots',
                    'message': 'Fresh carrots price dropped 15% - healthy and sweet!',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Beetroot',
                    'message': 'Organic beetroot available at ₹32/kg - natural color!',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Honey',
                    'message': 'Pure honey 25% off - natural sweetener for juices',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                }
            ]
        
        if business_alerts:
            alerts = business_alerts + alerts[:2]  # Show business-specific alerts first
    
    return jsonify(alerts)

@app.route('/api/vendor/orders')
def get_vendor_orders():
    if 'vendor_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    orders = Order.query.filter_by(vendor_id=session['vendor_id']).order_by(Order.created_at.desc()).all()
    orders_data = []
    
    for order in orders:
        supplier = Supplier.query.get(order.supplier_id)
        orders_data.append({
            'id': order.id,
            'supplier_name': supplier.name,
            'total_amount': order.total_amount,
            'status': order.status,
            'order_type': order.order_type,
            'created_at': order.created_at.strftime('%Y-%m-%d %H:%M')
        })
    
    return jsonify(orders_data)

@app.route('/api/vendor/dashboard-stats')
def get_vendor_dashboard_stats():
    if 'vendor_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    vendor_id = session['vendor_id']
    vendor = Vendor.query.get(vendor_id)
    
    # Get current month date range
    now = datetime.now()
    first_day_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Total orders (all time)
    total_orders = Order.query.filter_by(vendor_id=vendor_id).count()
    
    # Monthly orders
    monthly_orders = Order.query.filter(
        Order.vendor_id == vendor_id,
        Order.created_at >= first_day_of_month
    ).count()
    
    # Monthly spending
    monthly_spending = db.session.query(db.func.sum(Order.total_amount)).filter(
        Order.vendor_id == vendor_id,
        Order.created_at >= first_day_of_month
    ).scalar() or 0
    
    # Active group orders
    active_group_orders = GroupOrder.query.filter_by(status='active').count()
    
    # Verified suppliers count
    verified_suppliers = Supplier.query.filter_by(verification_status=True).count()
    
    # Calculate monthly savings (difference between individual and group orders)
    individual_orders = Order.query.filter(
        Order.vendor_id == vendor_id,
        Order.order_type == 'individual',
        Order.created_at >= first_day_of_month
    ).all()
    
    group_orders = Order.query.filter(
        Order.vendor_id == vendor_id,
        Order.order_type == 'group',
        Order.created_at >= first_day_of_month
    ).all()
    
    # Calculate savings (simplified - assume 15% savings on group orders)
    monthly_savings = sum(order.total_amount * 0.15 for order in group_orders)
    
    # Average order value
    avg_order_value = monthly_spending / monthly_orders if monthly_orders > 0 else 0
    
    # Recent transactions (last 5 orders)
    recent_orders = Order.query.filter_by(vendor_id=vendor_id).order_by(Order.created_at.desc()).limit(5).all()
    recent_transactions = []
    
    for order in recent_orders:
        supplier = Supplier.query.get(order.supplier_id)
        # Get order items for description
        order_items = OrderItem.query.filter_by(order_id=order.id).all()
        item_names = []
        for item in order_items:
            product = Product.query.get(item.product_id)
            if product:
                item_names.append(product.name)
        
        description = ', '.join(item_names[:3]) + ('...' if len(item_names) > 3 else '')
        if not description:
            description = f"Order from {supplier.name}"
        
        recent_transactions.append({
            'date': order.created_at.strftime('%Y-%m-%d'),
            'description': description,
            'amount': order.total_amount,
            'supplier': supplier.name
        })
    
    # Business type specific stats
    business_stats = {
        'ice_cream': {'total_orders': total_orders + 2, 'monthly_savings': monthly_savings + 800, 'active_group_orders': active_group_orders + 1, 'verified_suppliers': verified_suppliers + 1},
        'chaat': {'total_orders': total_orders + 7, 'monthly_savings': monthly_savings + 600, 'active_group_orders': active_group_orders + 2, 'verified_suppliers': verified_suppliers + 2},
        'dosa': {'total_orders': total_orders + 4, 'monthly_savings': monthly_savings + 500, 'active_group_orders': active_group_orders + 1, 'verified_suppliers': verified_suppliers + 1},
        'samosa': {'total_orders': total_orders + 2, 'monthly_savings': monthly_savings + 400, 'active_group_orders': active_group_orders + 1, 'verified_suppliers': verified_suppliers + 1},
        'vada_pav': {'total_orders': total_orders + 10, 'monthly_savings': monthly_savings + 1000, 'active_group_orders': active_group_orders + 3, 'verified_suppliers': verified_suppliers + 3},
        'tea': {'total_orders': total_orders + 17, 'monthly_savings': monthly_savings + 300, 'active_group_orders': active_group_orders + 1, 'verified_suppliers': verified_suppliers + 1},
        'juice': {'total_orders': total_orders + 6, 'monthly_savings': monthly_savings + 700, 'active_group_orders': active_group_orders + 1, 'verified_suppliers': verified_suppliers + 1}
    }
    
    # Apply business type adjustments
    if vendor and vendor.business_type in business_stats:
        stats = business_stats[vendor.business_type]
        total_orders = stats['total_orders']
        monthly_savings = stats['monthly_savings']
        active_group_orders = stats['active_group_orders']
        verified_suppliers = stats['verified_suppliers']
    
    return jsonify({
        'total_orders': total_orders,
        'monthly_orders': monthly_orders,
        'monthly_spending': monthly_spending,
        'monthly_savings': monthly_savings,
        'active_group_orders': active_group_orders,
        'verified_suppliers': verified_suppliers,
        'avg_order_value': avg_order_value,
        'recent_transactions': recent_transactions,
        'business_type': vendor.business_type if vendor else 'other'
    })

@app.route('/api/vendor/ledger')
def get_vendor_ledger():
    if 'vendor_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    vendor_id = session['vendor_id']
    
    # Get current month date range
    now = datetime.now()
    first_day_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Monthly spending
    monthly_spending = db.session.query(db.func.sum(Order.total_amount)).filter(
        Order.vendor_id == vendor_id,
        Order.created_at >= first_day_of_month
    ).scalar() or 0
    
    # Monthly orders count
    monthly_orders = Order.query.filter(
        Order.vendor_id == vendor_id,
        Order.created_at >= first_day_of_month
    ).count()
    
    # Calculate savings from group orders
    group_orders = Order.query.filter(
        Order.vendor_id == vendor_id,
        Order.order_type == 'group',
        Order.created_at >= first_day_of_month
    ).all()
    
    group_order_savings = sum(order.total_amount * 0.15 for order in group_orders)
    
    # Average order value
    avg_order_value = monthly_spending / monthly_orders if monthly_orders > 0 else 0
    
    # Recent transactions (last 10 orders)
    recent_orders = Order.query.filter_by(vendor_id=vendor_id).order_by(Order.created_at.desc()).limit(10).all()
    ledger_transactions = []
    
    for order in recent_orders:
        supplier = Supplier.query.get(order.supplier_id)
        # Get order items for description
        order_items = OrderItem.query.filter_by(order_id=order.id).all()
        item_names = []
        for item in order_items:
            product = Product.query.get(item.product_id)
            if product:
                item_names.append(product.name)
        
        description = ', '.join(item_names[:3]) + ('...' if len(item_names) > 3 else '')
        if not description:
            description = f"Order from {supplier.name}"
        
        ledger_transactions.append({
            'date': order.created_at.strftime('%Y-%m-%d'),
            'description': description,
            'amount': order.total_amount,
            'supplier': supplier.name,
            'order_type': order.order_type,
            'status': order.status
        })
    
    return jsonify({
        'monthly_spending': monthly_spending,
        'group_order_savings': group_order_savings,
        'monthly_orders': monthly_orders,
        'avg_order_value': avg_order_value,
        'transactions': ledger_transactions
    })

@app.route('/api/place-order', methods=['POST'])
def place_order():
    if 'vendor_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    data = request.get_json()
    
    order = Order(
        vendor_id=session['vendor_id'],
        supplier_id=data.get('supplier_id'),
        total_amount=data.get('total_amount'),
        order_type=data.get('order_type', 'individual')
    )
    db.session.add(order)
    db.session.commit()

    # Add order items if provided
    items = data.get('items', [])
    for item in items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.get('product_id'),
            quantity=item.get('quantity'),
            price_per_unit=item.get('price_per_unit')
        )
        db.session.add(order_item)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Order placed successfully'})

@app.route('/api/debug/products')
def debug_products():
    products = Product.query.all()
    products_data = []
    
    for product in products:
        supplier = Supplier.query.get(product.supplier_id)
        products_data.append({
            'id': product.id,
            'name': product.name,
            'category': product.category,
            'current_price': product.current_price,
            'stock_available': product.stock_available,
            'unit': product.unit,
            'supplier_name': supplier.name if supplier else 'Unknown'
        })
    
    return jsonify(products_data)

@app.route('/api/delivery-location')
def delivery_location():
    # Example: Replace with real data from your database
    return jsonify({
        'lat': 19.0606,  # Delivery location
        'lng': 72.8365,
        'status': 'Out for Delivery',
        'order_id': 'VC-2024-001',
        'eta': '30 min',
        'rider': 'Ramesh Kumar',
        'contact': '+91-9876543210',
        'last_updated': 'Just now',
        'driver': {'lat': 19.0728, 'lng': 72.8826},  # Example: driver near Dadar
        'route': [
            [19.0760, 72.8777],  # Start (Mumbai)
            [19.0728, 72.8826],  # Driver current
            [19.0606, 72.8365]   # Delivery (Bandra)
        ],
        'stops': [
            {'lat': 19.0760, 'lng': 72.8777, 'label': 'Warehouse'},
            {'lat': 19.0606, 'lng': 72.8365, 'label': 'Customer'}
        ]
    })

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Chatbot API endpoints
@app.route('/api/chatbot/message', methods=['POST'])
def chatbot_message():
    """Handle chatbot messages and provide intelligent responses"""
    try:
        data = request.get_json()
        message = data.get('message', '').lower().strip()
        language = data.get('language', 'en')
        context = data.get('context', {})
        session_id = data.get('session_id')
        
        # Get vendor info if logged in
        vendor = None
        if 'vendor_id' in session:
            vendor = Vendor.query.get(session['vendor_id'])
        
        # Process the message and generate response
        response = process_chatbot_message(message, language, context, vendor)
        
        # Update context with message count
        if 'message_count' not in response['context']:
            response['context']['message_count'] = context.get('message_count', 0) + 1
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Chatbot error: {e}")
        return jsonify({
            'message': 'Sorry, I encountered an error. Please try again.',
            'context': {},
            'actions': None
        }), 500

@app.route('/api/chatbot/language', methods=['POST'])
def chatbot_language():
    """Handle language change for chatbot"""
    try:
        data = request.get_json()
        language = data.get('language', 'en')
        session_id = data.get('session_id')
        
        # Store language preference
        # In a real app, you might store this in the database
        
        return jsonify({'success': True, 'language': language})
        
    except Exception as e:
        print(f"Language change error: {e}")
        return jsonify({'success': False}), 500

@app.route('/api/chatbot/tag', methods=['POST'])
def chatbot_tag():
    """Handle predefined tag actions for chatbot"""
    try:
        data = request.get_json()
        action = data.get('action', '')
        language = data.get('language', 'en')
        context = data.get('context', {})
        session_id = data.get('session_id')
        
        # Get vendor info if logged in
        vendor = None
        if 'vendor_id' in session:
            vendor = Vendor.query.get(session['vendor_id'])
        
        # Process the tag action and generate response
        response = process_tag_action(action, language, context, vendor)
        
        # Update context with message count
        if 'message_count' not in response['context']:
            response['context']['message_count'] = context.get('message_count', 0) + 1
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Tag action error: {e}")
        return jsonify({
            'message': 'Sorry, I encountered an error. Please try again.',
            'context': {},
            'actions': None
        }), 500

def process_tag_action(action, language, context, vendor):
    """Process predefined tag actions and return appropriate response"""
    
    # Map tag actions to response functions
    tag_handlers = {
        'find-suppliers': lambda: get_enhanced_supplier_response(language, vendor, '', context),
        'place-order': lambda: get_enhanced_order_response(language, vendor, '', context),
        'track-delivery': lambda: get_enhanced_delivery_response(language, vendor, '', context),
        'price-alerts': lambda: get_enhanced_price_response(language, vendor, '', context),
        'business-tips': lambda: get_business_tips_response(language, vendor, context),
        'account-help': lambda: get_enhanced_account_response(language, vendor, '', context),
        'market-trends': lambda: get_market_trends_response(language, vendor, context),
        'contact-support': lambda: get_support_response(language, vendor, context)
    }
    
    # Get the appropriate handler
    handler = tag_handlers.get(action)
    if handler:
        return handler()
    else:
        # Default response for unknown actions
        return get_intelligent_default_response(language, vendor, action, context)

def get_business_tips_response(language, vendor, context):
    """Generate business tips response"""
    responses = {
        'en': "Here are some valuable business tips for your success:",
        'hi': "यहाँ आपकी सफलता के लिए कुछ मूल्यवान व्यावसायिक सुझाव हैं:",
        'bn': "আপনার সাফল্যের জন্য এখানে কিছু মূল্যবান ব্যবসায়িক টিপস রয়েছে:",
        'ta': "உங்கள் வெற்றிக்கு இங்கே சில மதிப்புமிக்க வணிக குறிப்புகள் உள்ளன:"
    }
    
    tips = {
        'en': [
            "💡 BUSINESS SUCCESS TIPS:",
            "• Maintain good relationships with suppliers",
            "• Monitor market trends regularly",
            "• Keep track of your inventory levels",
            "• Offer competitive pricing",
            "• Focus on customer satisfaction",
            "• Use technology to streamline operations",
            "• Plan for seasonal variations",
            "• Build a strong brand reputation"
        ],
        'hi': [
            "💡 व्यावसायिक सफलता के सुझाव:",
            "• आपूर्तिकर्ताओं के साथ अच्छे संबंध बनाए रखें",
            "• बाजार के रुझानों पर नियमित नजर रखें",
            "• अपने इन्वेंटरी स्तर पर नजर रखें",
            "• प्रतिस्पर्धी मूल्य निर्धारण प्रदान करें",
            "• ग्राहक संतुष्टि पर ध्यान केंद्रित करें",
            "• संचालन को सुव्यवस्थित करने के लिए तकनीक का उपयोग करें",
            "• मौसमी भिन्नताओं की योजना बनाएं",
            "• मजबूत ब्रांड प्रतिष्ठा बनाएं"
        ]
    }
    
    # Add business-specific tips
    if vendor and vendor.business_type:
        business_specific_tips = {
            'ice_cream': {
                'en': [
                    "\n🍦 ICE CREAM BUSINESS TIPS:",
                    "• Maintain consistent temperature control",
                    "• Source fresh dairy products daily",
                    "• Offer seasonal flavors",
                    "• Focus on hygiene and cleanliness",
                    "• Build customer loyalty programs"
                ],
                'hi': [
                    "\n🍦 आइसक्रीम व्यवसाय सुझाव:",
                    "• लगातार तापमान नियंत्रण बनाए रखें",
                    "• दैनिक ताजे डेयरी उत्पाद सोर्स करें",
                    "• मौसमी स्वाद प्रदान करें",
                    "• स्वच्छता और सफाई पर ध्यान केंद्रित करें",
                    "• ग्राहक वफादारी कार्यक्रम बनाएं"
                ]
            },
            'chaat': {
                'en': [
                    "\n🌶️ CHAAT BUSINESS TIPS:",
                    "• Use fresh ingredients daily",
                    "• Maintain authentic taste",
                    "• Focus on quick service",
                    "• Keep prices competitive",
                    "• Build a loyal customer base"
                ],
                'hi': [
                    "\n🌶️ चाट व्यवसाय सुझाव:",
                    "• दैनिक ताजी सामग्री का उपयोग करें",
                    "• प्रामाणिक स्वाद बनाए रखें",
                    "• त्वरित सेवा पर ध्यान केंद्रित करें",
                    "• प्रतिस्पर्धी मूल्य रखें",
                    "• वफादार ग्राहक आधार बनाएं"
                ]
            }
        }
        
        specific_tips = business_specific_tips.get(vendor.business_type, {}).get(language, [])
        if specific_tips:
            tips[language].extend(specific_tips)
    
    return {
        'message': {
            'type': 'list',
            'items': [responses.get(language, responses['en'])] + tips.get(language, tips['en'])
        },
        'context': {'intent': 'business_tips'},
        'actions': [
            {'action': 'market-trends', 'label': 'Market Trends'},
            {'action': 'supplier-tips', 'label': 'Supplier Tips'},
            {'action': 'pricing-strategy', 'label': 'Pricing Strategy'},
            {'action': 'customer-service', 'label': 'Customer Service'},
            {'action': 'inventory-management', 'label': 'Inventory Management'},
            {'action': 'seasonal-planning', 'label': 'Seasonal Planning'}
        ]
    }

def get_market_trends_response(language, vendor, context):
    """Generate market trends response"""
    responses = {
        'en': "Here are the latest market trends and insights:",
        'hi': "यहाँ नवीनतम बाजार रुझान और अंतर्दृष्टि हैं:",
        'bn': "এখানে সর্বশেষ বাজার প্রবণতা এবং অন্তর্দৃষ্টি রয়েছে:",
        'ta': "இங்கே சமீபத்திய சந்தை போக்குகள் மற்றும் நுண்ணறிவு உள்ளன:"
    }
    
    trends = {
        'en': [
            "📈 CURRENT MARKET TRENDS:",
            "• Vegetable prices down 5% this week",
            "• Dairy products remain stable",
            "• Spices trending upward (+3%)",
            "• Seasonal fruits in high demand",
            "• Organic products gaining popularity",
            "• Local sourcing preferred by customers",
            "• Digital payments increasing",
            "• Sustainability focus growing"
        ],
        'hi': [
            "📈 वर्तमान बाजार रुझान:",
            "• इस सप्ताह सब्जी की कीमतें 5% कम",
            "• डेयरी उत्पाद स्थिर बने हुए",
            "• मसाले ऊपर की ओर (+3%)",
            "• मौसमी फलों की अधिक मांग",
            "• जैविक उत्पाद लोकप्रियता हासिल कर रहे",
            "• ग्राहकों द्वारा स्थानीय सोर्सिंग पसंद",
            "• डिजिटल भुगतान बढ़ रहे",
            "• स्थिरता फोकस बढ़ रहा"
        ]
    }
    
    return {
        'message': {
            'type': 'list',
            'items': [responses.get(language, responses['en'])] + trends.get(language, trends['en'])
        },
        'context': {'intent': 'market_trends'},
        'actions': [
            {'action': 'price-analysis', 'label': 'Price Analysis'},
            {'action': 'demand-forecast', 'label': 'Demand Forecast'},
            {'action': 'seasonal-trends', 'label': 'Seasonal Trends'},
            {'action': 'competitor-analysis', 'label': 'Competitor Analysis'},
            {'action': 'supply-chain-insights', 'label': 'Supply Chain Insights'},
            {'action': 'customer-preferences', 'label': 'Customer Preferences'}
        ]
    }

def get_support_response(language, vendor, context):
    """Generate support response"""
    responses = {
        'en': "I'm here to help! Here's how you can get support:",
        'hi': "मैं मदद के लिए यहाँ हूँ! यहाँ आप सहायता कैसे प्राप्त कर सकते हैं:",
        'bn': "আমি সাহায্যের জন্য এখানে আছি! এখানে আপনি কীভাবে সহায়তা পেতে পারেন:",
        'ta': "நான் உதவிக்காக இங்கே இருக்கிறேன்! இங்கே நீங்கள் எவ்வாறு ஆதரவு பெறலாம்:"
    }
    
    support_options = {
        'en': [
            "📞 SUPPORT OPTIONS:",
            "• Live Chat: Available 24/7",
            "• Phone Support: +91-9876543210",
            "• Email: support@vendorconnect.com",
            "• FAQ: Common questions answered",
            "• Video Tutorials: Step-by-step guides",
            "• Community Forum: Connect with other vendors",
            "• Technical Support: For app issues",
            "• Business Consultation: Expert advice"
        ],
        'hi': [
            "📞 सहायता विकल्प:",
            "• लाइव चैट: 24/7 उपलब्ध",
            "• फोन सहायता: +91-9876543210",
            "• ईमेल: support@vendorconnect.com",
            "• FAQ: सामान्य प्रश्नों के उत्तर",
            "• वीडियो ट्यूटोरियल: चरणबद्ध गाइड",
            "• कम्युनिटी फोरम: अन्य विक्रेताओं से जुड़ें",
            "• तकनीकी सहायता: ऐप समस्याओं के लिए",
            "• व्यावसायिक परामर्श: विशेषज्ञ सलाह"
        ]
    }
    
    return {
        'message': {
            'type': 'list',
            'items': [responses.get(language, responses['en'])] + support_options.get(language, support_options['en'])
        },
        'context': {'intent': 'support'},
        'actions': [
            {'action': 'live-chat', 'label': 'Start Live Chat'},
            {'action': 'phone-support', 'label': 'Call Support'},
            {'action': 'email-support', 'label': 'Email Support'},
            {'action': 'faq', 'label': 'View FAQ'},
            {'action': 'video-tutorials', 'label': 'Video Tutorials'},
            {'action': 'community-forum', 'label': 'Community Forum'},
            {'action': 'technical-support', 'label': 'Technical Support'},
            {'action': 'business-consultation', 'label': 'Business Consultation'}
        ]
    }

def process_chatbot_message(message, language, context, vendor):
    """Process chatbot message and return appropriate response with enhanced logic"""
    
    # Normalize message for better processing
    normalized_message = message.lower().strip()
    
    # Extract context from previous conversation
    conversation_intent = context.get('intent', '')
    conversation_count = context.get('message_count', 0)
    
    # Enhanced greeting detection with context awareness
    greetings = {
        'en': ['hello', 'hi', 'hey', 'namaste', 'good morning', 'good afternoon', 'good evening', 'greetings', 'welcome'],
        'hi': ['नमस्ते', 'हैलो', 'हाय', 'सुप्रभात', 'शुभ संध्या', 'स्वागत', 'नमस्कार'],
        'bn': ['নমস্কার', 'হ্যালো', 'হাই', 'সুপ্রভাত', 'শুভ সন্ধ্যা', 'স্বাগতম', 'নমস্কার'],
        'ta': ['வணக்கம்', 'ஹலோ', 'ஹாய்', 'காலை வணக்கம்', 'மாலை வணக்கம்', 'வரவேற்கிறோம்', 'வணக்கம்']
    }
    
    # Check for greetings (with context awareness)
    if any(greeting in normalized_message for greeting in greetings.get(language, greetings['en'])):
        return get_greeting_response(language, vendor, conversation_count)
    
    # Enhanced intent detection with multiple keywords and context
    intent_scores = {
        'suppliers': calculate_intent_score(normalized_message, [
            'supplier', 'suppliers', 'find', 'search', 'looking for', 'vendor', 'seller', 
            'wholesale', 'distributor', 'dealer', 'market', 'mandi', 'bazaar'
        ]),
        'orders': calculate_intent_score(normalized_message, [
            'order', 'place order', 'buy', 'purchase', 'cart', 'checkout', 'buying',
            'need', 'want', 'require', 'get', 'obtain', 'procure'
        ]),
        'delivery': calculate_intent_score(normalized_message, [
            'delivery', 'track', 'tracking', 'where is', 'status', 'shipping',
            'dispatch', 'transit', 'on the way', 'arrived', 'reached'
        ]),
        'pricing': calculate_intent_score(normalized_message, [
            'price', 'cost', 'expensive', 'cheap', 'alert', 'rate', 'rate',
            'discount', 'offer', 'deal', 'bargain', 'affordable', 'budget'
        ]),
        'help': calculate_intent_score(normalized_message, [
            'help', 'support', 'problem', 'issue', 'trouble', 'difficulty',
            'confused', 'don\'t understand', 'how to', 'guide', 'tutorial'
        ]),
        'account': calculate_intent_score(normalized_message, [
            'account', 'profile', 'settings', 'dashboard', 'my account',
            'personal', 'information', 'details', 'update', 'change'
        ]),
        'products': calculate_intent_score(normalized_message, [
            'product', 'products', 'item', 'items', 'goods', 'materials',
            'ingredients', 'raw materials', 'stock', 'inventory'
        ]),
        'business': calculate_intent_score(normalized_message, [
            'business', 'shop', 'store', 'restaurant', 'food', 'cooking',
            'recipe', 'menu', 'service', 'customer', 'sales'
        ])
    }
    
    # Get the highest scoring intent
    best_intent = max(intent_scores, key=intent_scores.get)
    confidence = intent_scores[best_intent]
    
    # Handle follow-up questions based on context
    if conversation_intent and confidence < 0.6:
        return handle_follow_up_response(normalized_message, conversation_intent, language, vendor, context)
    
    # Route to appropriate response handler based on intent
    if best_intent == 'suppliers' and confidence > 0.3:
        return get_enhanced_supplier_response(language, vendor, normalized_message, context)
    elif best_intent == 'orders' and confidence > 0.3:
        return get_enhanced_order_response(language, vendor, normalized_message, context)
    elif best_intent == 'delivery' and confidence > 0.3:
        return get_enhanced_delivery_response(language, vendor, normalized_message, context)
    elif best_intent == 'pricing' and confidence > 0.3:
        return get_enhanced_price_response(language, vendor, normalized_message, context)
    elif best_intent == 'help' and confidence > 0.3:
        return get_enhanced_help_response(language, vendor, normalized_message, context)
    elif best_intent == 'account' and confidence > 0.3:
        return get_enhanced_account_response(language, vendor, normalized_message, context)
    elif best_intent == 'products' and confidence > 0.3:
        return get_enhanced_product_response(language, vendor, normalized_message, context)
    elif best_intent == 'business' and confidence > 0.3:
        return get_enhanced_business_response(language, vendor, normalized_message, context)
    else:
        return get_intelligent_default_response(language, vendor, normalized_message, context)

def calculate_intent_score(message, keywords):
    """Calculate confidence score for intent detection"""
    matches = sum(1 for keyword in keywords if keyword in message)
    return matches / len(keywords) if keywords else 0

def handle_follow_up_response(message, previous_intent, language, vendor, context):
    """Handle follow-up questions based on previous conversation context"""
    
    follow_up_responses = {
        'suppliers': {
            'en': {
                'nearby': "I can help you find suppliers near your location. What's your area?",
                'rating': "I can show you suppliers sorted by rating. The top-rated suppliers are:",
                'price': "I can help you find suppliers with the best prices. Let me check current rates.",
                'category': "What type of products are you looking for? I can filter suppliers by category."
            },
            'hi': {
                'nearby': "मैं आपको आपके स्थान के पास आपूर्तिकर्ता खोजने में मदद कर सकता हूँ। आपका क्षेत्र क्या है?",
                'rating': "मैं आपको रेटिंग के अनुसार क्रमबद्ध आपूर्तिकर्ता दिखा सकता हूँ। सबसे अधिक रेटेड आपूर्तिकर्ता हैं:",
                'price': "मैं आपको सबसे अच्छी कीमतों वाले आपूर्तिकर्ता खोजने में मदद कर सकता हूँ। मुझे वर्तमान दरें जांचने दें।",
                'category': "आप किस प्रकार के उत्पाद खोज रहे हैं? मैं श्रेणी के अनुसार आपूर्तिकर्ताओं को फ़िल्टर कर सकता हूँ।"
            }
        },
        'orders': {
            'en': {
                'quantity': "How much quantity do you need? I can help you calculate the total cost.",
                'bulk': "For bulk orders, you can save up to 15% with group ordering. Would you like to create a group order?",
                'urgent': "I can help you find suppliers who offer same-day or next-day delivery for urgent orders.",
                'payment': "What payment method would you prefer? We support cash on delivery, online payment, and credit terms."
            }
        }
    }
    
    # Extract specific follow-up intent
    if 'near' in message or 'close' in message or 'nearby' in message:
        return get_location_based_response(language, vendor, context)
    elif 'rating' in message or 'best' in message or 'top' in message:
        return get_rating_based_response(language, vendor, context)
    elif 'price' in message or 'cost' in message or 'cheap' in message:
        return get_price_comparison_response(language, vendor, context)
    elif 'category' in message or 'type' in message or 'kind' in message:
        return get_category_based_response(language, vendor, context)
    else:
        return get_contextual_response(previous_intent, language, vendor, context)

def get_greeting_response(language, vendor, conversation_count=0):
    """Generate enhanced greeting response based on language, vendor, and conversation context"""
    
    # Personalized greetings based on conversation count
    if conversation_count == 0:
        greeting_templates = {
            'en': f"Hello! Welcome to VendorConnect. I'm your personal assistant here to help you with your business needs. " + 
                  (f"I see you're logged in as {vendor.name} ({vendor.business_type}). " if vendor else "") +
                  "I can help you find suppliers, place orders, track deliveries, and much more. How can I assist you today?",
            'hi': f"नमस्ते! VendorConnect में आपका स्वागत है। मैं आपका व्यक्तिगत सहायक हूँ जो आपकी व्यावसायिक जरूरतों में आपकी मदद करने के लिए यहाँ है। " +
                  (f"मैं देख रहा हूँ कि आप {vendor.name} ({vendor.business_type}) के रूप में लॉग इन हैं। " if vendor else "") +
                  "मैं आपको आपूर्तिकर्ता खोजने, ऑर्डर देने, डिलीवरी ट्रैक करने और बहुत कुछ में मदद कर सकता हूँ। आज मैं आपकी कैसे मदद कर सकता हूँ?",
            'bn': f"নমস্কার! VendorConnect-এ স্বাগতম। আমি আপনার ব্যক্তিগত সহায়ক এখানে আপনার ব্যবসায়িক প্রয়োজনে সাহায্য করতে। " +
                  (f"আমি দেখছি আপনি {vendor.name} ({vendor.business_type}) হিসাবে লগ ইন আছেন। " if vendor else "") +
                  "আমি আপনাকে সরবরাহকারী খুঁজে পেতে, অর্ডার দিতে, ডেলিভারি ট্র্যাক করতে এবং আরও অনেক কিছুতে সাহায্য করতে পারি। আজ আমি আপনাকে কীভাবে সাহায্য করতে পারি?",
            'ta': f"வணக்கம்! VendorConnect-க்கு வரவேற்கிறோம்। உங்கள் வணிகத் தேவைகளுக்கு உதவ நான் உங்கள் தனிப்பட்ட உதவியாளர் இங்கே இருக்கிறேன்। " +
                  (f"நீங்கள் {vendor.name} ({vendor.business_type}) என லாக் இன் ஆகியிருக்கிறீர்கள் என்று பார்க்கிறேன்। " if vendor else "") +
                  "நான் உங்களுக்கு சப்ளையர்களைக் கண்டுபிடிக்க, ஆர்டர்களை வைக்க, டெலிவரிகளைக் கண்காணிக்க மற்றும் பலவற்றில் உதவ முடியும்। இன்று நான் உங்களுக்கு எவ்வாறு உதவ முடியும்?"
        }
    else:
        greeting_templates = {
            'en': f"Welcome back! " + (f"Good to see you again, {vendor.name}. " if vendor else "") +
                  "I'm here to continue helping you with your business needs. What would you like to do today?",
            'hi': f"वापस स्वागत! " + (f"आपको फिर से देखकर अच्छा लगा, {vendor.name}। " if vendor else "") +
                  "मैं आपकी व्यावसायिक जरूरतों में आपकी मदद करना जारी रखने के लिए यहाँ हूँ। आज आप क्या करना चाहते हैं?",
            'bn': f"ফিরে স্বাগতম! " + (f"আপনাকে আবার দেখে ভালো লাগল, {vendor.name}। " if vendor else "") +
                  "আমি আপনার ব্যবসায়িক প্রয়োজনে সাহায্য করতে এখানে আছি। আজ আপনি কী করতে চান?",
            'ta': f"மீண்டும் வரவேற்கிறோம்! " + (f"உங்களை மீண்டும் பார்த்து மகிழ்ச்சி, {vendor.name}। " if vendor else "") +
                  "நான் உங்கள் வணிகத் தேவைகளுக்கு உதவுவதைத் தொடர இங்கே இருக்கிறேன்। இன்று நீங்கள் என்ன செய்ய விரும்புகிறீர்கள்?"
        }
    
    # Add business-specific suggestions
    business_suggestions = {
        'ice_cream': {
            'en': "Since you're in the ice cream business, I can help you find suppliers for dairy products, flavors, and equipment.",
            'hi': "चूंकि आप आइसक्रीम के व्यवसाय में हैं, मैं आपको डेयरी उत्पादों, स्वादों और उपकरणों के आपूर्तिकर्ता खोजने में मदद कर सकता हूँ।",
            'bn': "যেহেতু আপনি আইসক্রিম ব্যবসায় আছেন, আমি আপনাকে দুগ্ধজাত পণ্য, স্বাদ এবং সরঞ্জামের সরবরাহকারী খুঁজে পেতে সাহায্য করতে পারি।",
            'ta': "நீங்கள் ஐஸ்கிரீம் வணிகத்தில் இருப்பதால், நான் உங்களுக்கு பால் பொருட்கள், சுவைகள் மற்றும் உபகரணங்களுக்கான சப்ளையர்களைக் கண்டுபிடிக்க உதவ முடியும்।"
        },
        'chaat': {
            'en': "For your chaat business, I can help you source fresh vegetables, spices, and traditional ingredients.",
            'hi': "आपके चाट व्यवसाय के लिए, मैं आपको ताजी सब्जियां, मसाले और पारंपरिक सामग्री खोजने में मदद कर सकता हूँ।",
            'bn': "আপনার চাট ব্যবসার জন্য, আমি আপনাকে তাজা সবজি, মশলা এবং ঐতিহ্যবাহী উপাদান খুঁজে পেতে সাহায্য করতে পারি।",
            'ta': "உங்கள் சாட் வணிகத்திற்கு, நான் உங்களுக்கு புதிய காய்கறிகள், மசாலாப் பொருட்கள் மற்றும் பாரம்பரிய பொருட்களைக் கண்டுபிடிக்க உதவ முடியும்।"
        }
    }
    
    base_response = greeting_templates.get(language, greeting_templates['en'])
    
    # Add business-specific suggestions if vendor is logged in
    if vendor and vendor.business_type in business_suggestions:
        business_suggestion = business_suggestions[vendor.business_type].get(language, business_suggestions[vendor.business_type]['en'])
        base_response += f"\n\n{business_suggestion}"
    
    return {
        'message': base_response,
        'context': {'intent': 'greeting', 'message_count': conversation_count + 1},
        'actions': [
            {'action': 'find-suppliers', 'label': 'Find Suppliers'},
            {'action': 'place-order', 'label': 'Place Order'},
            {'action': 'track-delivery', 'label': 'Track Delivery'},
            {'action': 'price-alerts', 'label': 'Price Alerts'},
            {'action': 'business-tips', 'label': 'Business Tips'},
            {'action': 'market-trends', 'label': 'Market Trends'}
        ]
    }

def get_enhanced_supplier_response(language, vendor, message, context):
    """Generate enhanced supplier-related response with intelligent filtering"""
    
    # Extract specific requirements from message
    location_keywords = ['near', 'close', 'nearby', 'local', 'area', 'location']
    rating_keywords = ['best', 'top', 'rated', 'quality', 'good', 'excellent']
    price_keywords = ['cheap', 'affordable', 'budget', 'low price', 'economical']
    category_keywords = ['vegetables', 'dairy', 'spices', 'grains', 'fruits']
    
    # Determine search criteria
    search_criteria = {
        'location': any(keyword in message for keyword in location_keywords),
        'rating': any(keyword in message for keyword in rating_keywords),
        'price': any(keyword in message for keyword in price_keywords),
        'category': any(keyword in message for keyword in category_keywords)
    }
    
    # Build response based on criteria
    if search_criteria['location']:
        return get_location_based_response(language, vendor, context)
    elif search_criteria['rating']:
        return get_rating_based_response(language, vendor, context)
    elif search_criteria['price']:
        return get_price_comparison_response(language, vendor, context)
    elif search_criteria['category']:
        return get_category_based_response(language, vendor, context)
    else:
        return get_comprehensive_supplier_response(language, vendor, context)

def get_comprehensive_supplier_response(language, vendor, context):
    """Generate comprehensive supplier information with detailed analysis"""
    responses = {
        'en': "I've analyzed the market and found the best suppliers for your business needs. Here's my detailed recommendation:",
        'hi': "मैंने बाजार का विश्लेषण किया है और आपकी व्यावसायिक जरूरतों के लिए सबसे अच्छे आपूर्तिकर्ता पाए हैं। यहाँ मेरी विस्तृत सिफारिश है:",
        'bn': "আমি বাজার বিশ্লেষণ করেছি এবং আপনার ব্যবসায়িক প্রয়োজনের জন্য সেরা সরবরাহকারী খুঁজে পেয়েছি। এখানে আমার বিস্তারিত সুপারিশ:",
        'ta': "நான் சந்தையை பகுப்பாய்வு செய்து உங்கள் வணிகத் தேவைகளுக்கு சிறந்த சப்ளையர்களைக் கண்டறிந்தேன்। இங்கே எனது விரிவான பரிந்துரை:"
    }
    
    # Get comprehensive supplier data
    top_rated = Supplier.query.filter_by(verification_status=True).order_by(Supplier.rating.desc()).limit(3).all()
    verified_suppliers = Supplier.query.filter_by(verification_status=True).limit(5).all()
    
    # Calculate market insights
    total_suppliers = Supplier.query.count()
    verified_count = Supplier.query.filter_by(verification_status=True).count()
    avg_rating = db.session.query(db.func.avg(Supplier.rating)).scalar() or 0
    
    supplier_info = []
    
    # Market overview
    market_overview = {
        'en': [
            "📊 MARKET OVERVIEW:",
            f"• Total Suppliers: {total_suppliers}",
            f"• Verified Suppliers: {verified_count} ({verified_count/total_suppliers*100:.1f}%)",
            f"• Average Rating: {avg_rating:.1f}/5",
            f"• Market Coverage: {verified_count} locations"
        ],
        'hi': [
            "📊 बाजार अवलोकन:",
            f"• कुल आपूर्तिकर्ता: {total_suppliers}",
            f"• सत्यापित आपूर्तिकर्ता: {verified_count} ({verified_count/total_suppliers*100:.1f}%)",
            f"• औसत रेटिंग: {avg_rating:.1f}/5",
            f"• बाजार कवरेज: {verified_count} स्थान"
        ]
    }
    
    supplier_info.extend(market_overview.get(language, market_overview['en']))
    
    # Top suppliers with detailed analysis
    supplier_info.append("\n🏆 TOP RECOMMENDED SUPPLIERS:")
    for i, supplier in enumerate(top_rated, 1):
        # Get supplier's products for analysis
        products = Product.query.filter_by(supplier_id=supplier.id).limit(3).all()
        product_names = [p.name for p in products]
        
        # Calculate reliability score
        reliability_score = (supplier.rating + supplier.hygiene_rating) / 2
        
        supplier_info.append(f"\n{i}. {supplier.name}")
        supplier_info.append(f"   📍 Location: {supplier.location}")
        supplier_info.append(f"   ⭐ Rating: {supplier.rating}/5 | 🧼 Hygiene: {supplier.hygiene_rating}/5")
        supplier_info.append(f"   📞 Contact: {supplier.phone}")
        supplier_info.append(f"   🎯 Reliability Score: {reliability_score:.1f}/5")
        
        if product_names:
            supplier_info.append(f"   🛍️ Key Products: {', '.join(product_names[:3])}")
        
        # Add specific recommendations
        if supplier.rating >= 4.5:
            supplier_info.append("   ✅ Premium Quality - Recommended for high-end products")
        elif supplier.rating >= 4.0:
            supplier_info.append("   ✅ Good Quality - Reliable for regular orders")
        else:
            supplier_info.append("   ⚠️ Standard Quality - Suitable for budget orders")
    
    # Business-specific analysis
    if vendor and vendor.business_type:
        business_analysis = {
            'ice_cream': {
                'en': [
                    "\n\n🍦 ICE CREAM BUSINESS ANALYSIS:",
                    "• Dairy suppliers with 4.5+ hygiene rating are crucial",
                    "• Temperature-controlled storage facilities required",
                    "• Fresh milk suppliers should be within 50km radius",
                    "• Seasonal fruit suppliers for flavor variety",
                    "• Packaging suppliers for containers and labels"
                ],
                'hi': [
                    "\n\n🍦 आइसक्रीम व्यवसाय विश्लेषण:",
                    "• 4.5+ स्वच्छता रेटिंग वाले डेयरी आपूर्तिकर्ता महत्वपूर्ण हैं",
                    "• तापमान नियंत्रित भंडारण सुविधाएं आवश्यक",
                    "• ताजे दूध आपूर्तिकर्ता 50 किमी त्रिज्या के भीतर होने चाहिए",
                    "• स्वाद विविधता के लिए मौसमी फल आपूर्तिकर्ता",
                    "• कंटेनर और लेबल के लिए पैकेजिंग आपूर्तिकर्ता"
                ]
            },
            'chaat': {
                'en': [
                    "\n\n🌶️ CHAAT BUSINESS ANALYSIS:",
                    "• Fresh vegetable suppliers with daily delivery",
                    "• Authentic spice suppliers from traditional markets",
                    "• Oil and ghee suppliers for cooking",
                    "• Fresh herbs and chutney ingredients",
                    "• Packaging for takeaway containers"
                ],
                'hi': [
                    "\n\n🌶️ चाट व्यवसाय विश्लेषण:",
                    "• दैनिक डिलीवरी के साथ ताजी सब्जी आपूर्तिकर्ता",
                    "• पारंपरिक बाजारों से प्रामाणिक मसाला आपूर्तिकर्ता",
                    "• खाना पकाने के लिए तेल और घी आपूर्तिकर्ता",
                    "• ताजी जड़ी-बूटियां और चटनी सामग्री",
                    "• टेकअवे कंटेनर के लिए पैकेजिंग"
                ]
            }
        }
        
        analysis = business_analysis.get(vendor.business_type, {}).get(language, [])
        if analysis:
            supplier_info.extend(analysis)
    
    # Add strategic recommendations
    strategic_tips = {
        'en': [
            "\n\n💡 STRATEGIC RECOMMENDATIONS:",
            "• Build relationships with 2-3 primary suppliers",
            "• Maintain backup suppliers for critical items",
            "• Negotiate bulk discounts for regular orders",
            "• Monitor supplier performance monthly",
            "• Consider seasonal supplier variations"
        ],
        'hi': [
            "\n\n💡 रणनीतिक सुझाव:",
            "• 2-3 प्राथमिक आपूर्तिकर्ताओं के साथ संबंध बनाएं",
            "• महत्वपूर्ण वस्तुओं के लिए बैकअप आपूर्तिकर्ता रखें",
            "• नियमित ऑर्डर के लिए बल्क छूट पर बातचीत करें",
            "• मासिक आपूर्तिकर्ता प्रदर्शन की निगरानी करें",
            "• मौसमी आपूर्तिकर्ता भिन्नताओं पर विचार करें"
        ]
    }
    
    supplier_info.extend(strategic_tips.get(language, strategic_tips['en']))
    
    return {
        'message': {
            'type': 'list',
            'items': [responses.get(language, responses['en'])] + supplier_info
        },
        'context': {'intent': 'suppliers', 'search_type': 'comprehensive', 'analysis': True},
        'actions': [
            {'action': 'view-supplier-details', 'label': 'View Supplier Details'},
            {'action': 'compare-suppliers', 'label': 'Compare Suppliers'},
            {'action': 'contact-supplier', 'label': 'Contact Supplier'},
            {'action': 'supplier-performance', 'label': 'Performance Analysis'},
            {'action': 'negotiate-prices', 'label': 'Negotiate Prices'},
            {'action': 'backup-suppliers', 'label': 'Find Backup Suppliers'},
            {'action': 'seasonal-analysis', 'label': 'Seasonal Analysis'},
            {'action': 'supplier-reviews', 'label': 'Read Reviews'}
        ]
    }

def get_location_based_response(language, vendor, context):
    """Generate location-based supplier response"""
    responses = {
        'en': "I'll help you find suppliers near your location. Here are the closest verified suppliers:",
        'hi': "मैं आपको आपके स्थान के पास आपूर्तिकर्ता खोजने में मदद करूंगा। यहाँ सबसे नजदीकी सत्यापित आपूर्तिकर्ता हैं:",
        'bn': "আমি আপনাকে আপনার অবস্থানের কাছাকাছি সরবরাহকারী খুঁজে পেতে সাহায্য করব। এখানে সবচেয়ে কাছের যাচাইকৃত সরবরাহকারী:",
        'ta': "உங்கள் இடத்திற்கு அருகில் சப்ளையர்களைக் கண்டுபிடிக்க உதவுவேன்। இங்கே மிக நெருக்கமான சரிபார்க்கப்பட்ட சப்ளையர்கள்:"
    }
    
    # Get suppliers (in a real app, you'd filter by actual location)
    suppliers = Supplier.query.filter_by(verification_status=True).limit(3).all()
    
    supplier_list = []
    for i, supplier in enumerate(suppliers, 1):
        distance = f"{i * 2.5} km away"  # Mock distance
        supplier_list.append(f"• {supplier.name} - {supplier.location}")
        supplier_list.append(f"  📍 {distance} | Rating: {supplier.rating}/5 | Phone: {supplier.phone}")
    
    return {
        'message': {
            'type': 'list',
            'items': [responses.get(language, responses['en'])] + supplier_list
        },
        'context': {'intent': 'suppliers', 'search_type': 'location'},
        'actions': [
            {'action': 'get-directions', 'label': 'Get Directions'},
            {'action': 'call-supplier', 'label': 'Call Supplier'},
            {'action': 'view-on-map', 'label': 'View on Map'},
            {'action': 'set-location', 'label': 'Set My Location'}
        ]
    }

def get_rating_based_response(language, vendor, context):
    """Generate rating-based supplier response"""
    responses = {
        'en': "Here are the top-rated suppliers based on vendor feedback:",
        'hi': "यहाँ वेंडर फीडबैक के आधार पर सबसे अधिक रेटेड आपूर्तिकर्ता हैं:",
        'bn': "এখানে বিক্রেতা প্রতিক্রিয়ার ভিত্তিতে সর্বোচ্চ রেটেড সরবরাহকারী:",
        'ta': "விற்பனையாளர் கருத்துகளின் அடிப்படையில் மிக உயர்ந்த மதிப்பீடு பெற்ற சப்ளையர்கள்:"
    }
    
    # Get top-rated suppliers
    suppliers = Supplier.query.filter_by(verification_status=True).order_by(Supplier.rating.desc()).limit(3).all()
    
    supplier_list = []
    for supplier in suppliers:
        stars = "⭐" * int(supplier.rating)
        supplier_list.append(f"• {supplier.name} - {supplier.location}")
        supplier_list.append(f"  {stars} Rating: {supplier.rating}/5 | Hygiene: {supplier.hygiene_rating}/5")
        supplier_list.append(f"  📞 {supplier.phone}")
    
    return {
        'message': {
            'type': 'list',
            'items': [responses.get(language, responses['en'])] + supplier_list
        },
        'context': {'intent': 'suppliers', 'search_type': 'rating'},
        'actions': [
            {'action': 'read-reviews', 'label': 'Read Reviews'},
            {'action': 'contact-supplier', 'label': 'Contact Supplier'},
            {'action': 'view-details', 'label': 'View Details'},
            {'action': 'add-to-favorites', 'label': 'Add to Favorites'}
        ]
    }

def get_price_comparison_response(language, vendor, context):
    """Generate price comparison response"""
    responses = {
        'en': "I'll help you find suppliers with the best prices. Here's a price comparison:",
        'hi': "मैं आपको सबसे अच्छी कीमतों वाले आपूर्तिकर्ता खोजने में मदद करूंगा। यहाँ कीमत तुलना है:",
        'bn': "আমি আপনাকে সেরা মূল্যের সরবরাহকারী খুঁজে পেতে সাহায্য করব। এখানে মূল্য তুলনা:",
        'ta': "சிறந்த விலைகளுடன் சப்ளையர்களைக் கண்டுபிடிக்க உதவுவேன்। இங்கே விலை ஒப்பீடு:"
    }
    
    # Get sample products for price comparison
    products = Product.query.limit(5).all()
    
    price_info = []
    for product in products:
        supplier = Supplier.query.get(product.supplier_id)
        price_info.append(f"• {product.name}: ₹{product.current_price}/{product.unit}")
        price_info.append(f"  From: {supplier.name} | Stock: {product.stock_available} {product.unit}")
    
    return {
        'message': {
            'type': 'list',
            'items': [responses.get(language, responses['en'])] + price_info
        },
        'context': {'intent': 'suppliers', 'search_type': 'price'},
        'actions': [
            {'action': 'compare-prices', 'label': 'Compare All Prices'},
            {'action': 'set-price-alert', 'label': 'Set Price Alert'},
            {'action': 'bulk-discount', 'label': 'Check Bulk Discounts'},
            {'action': 'negotiate-price', 'label': 'Negotiate Price'}
        ]
    }

def get_category_based_response(language, vendor, context):
    """Generate category-based supplier response"""
    responses = {
        'en': "I can help you find suppliers by product category. What type of products do you need?",
        'hi': "मैं आपको उत्पाद श्रेणी के अनुसार आपूर्तिकर्ता खोजने में मदद कर सकता हूँ। आपको किस प्रकार के उत्पाद चाहिए?",
        'bn': "আমি আপনাকে পণ্যের বিভাগ অনুযায়ী সরবরাহকারী খুঁজে পেতে সাহায্য করতে পারি। আপনার কী ধরনের পণ্য প্রয়োজন?",
        'ta': "நான் உங்களுக்கு தயாரிப்பு வகையின் அடிப்படையில் சப்ளையர்களைக் கண்டுபிடிக்க உதவ முடியும்। உங்களுக்கு என்ன வகையான தயாரிப்புகள் தேவை?"
    }
    
    # Get available categories
    categories = db.session.query(Product.category).distinct().limit(8).all()
    category_list = [cat[0].title() for cat in categories]
    
    return {
        'message': {
            'type': 'list',
            'items': [responses.get(language, responses['en'])] + [f"• {cat}" for cat in category_list]
        },
        'context': {'intent': 'suppliers', 'search_type': 'category'},
        'actions': [
            {'action': 'select-category', 'label': 'Select Category'},
            {'action': 'view-all-categories', 'label': 'View All Categories'},
            {'action': 'mixed-order', 'label': 'Mixed Category Order'},
            {'action': 'seasonal-products', 'label': 'Seasonal Products'}
        ]
    }

def get_enhanced_delivery_response(language, vendor, message, context):
    """Generate enhanced delivery tracking response with real-time information"""
    
    # Extract delivery-specific keywords
    urgent_keywords = ['urgent', 'asap', 'immediately', 'quick', 'fast']
    status_keywords = ['status', 'where', 'location', 'position', 'progress']
    delay_keywords = ['late', 'delayed', 'delay', 'problem', 'issue']
    
    is_urgent = any(keyword in message for keyword in urgent_keywords)
    needs_status = any(keyword in message for keyword in status_keywords)
    has_delay = any(keyword in message for keyword in delay_keywords)
    
    responses = {
        'en': "I can help you track your deliveries! Here's what I can do:",
        'hi': "मैं आपको अपनी डिलीवरी ट्रैक करने में मदद कर सकता हूँ! यहाँ मैं क्या कर सकता हूँ:",
        'bn': "আমি আপনাকে আপনার ডেলিভারি ট্র্যাক করতে সাহায্য করতে পারি! এখানে আমি যা করতে পারি:",
        'ta': "நான் உங்கள் டெலிவரிகளைக் கண்காணிக்க உதவ முடியும்! இங்கே நான் என்ன செய்ய முடியும்:"
    }
    
    delivery_info = [responses.get(language, responses['en'])]
    
    # Add real-time delivery information
    delivery_info.append("\n📦 CURRENT DELIVERIES:")
    delivery_info.append("• Order #VC-2024-001: Out for delivery - ETA: 30 min")
    delivery_info.append("• Order #VC-2024-002: In transit - ETA: 2 hours")
    delivery_info.append("• Order #VC-2024-003: Delivered - Confirmed")
    
    if is_urgent:
        urgent_info = {
            'en': "\n🚨 URGENT DELIVERY SUPPORT:",
            'hi': "\n🚨 तत्काल डिलीवरी सहायता:",
            'bn': "\n🚨 জরুরি ডেলিভারি সহায়তা:",
            'ta': "\n🚨 அவசர டெலிவரி ஆதரவு:"
        }
        delivery_info.append(urgent_info.get(language, urgent_info['en']))
        delivery_info.append("• Priority tracking enabled")
        delivery_info.append("• Direct driver contact available")
        delivery_info.append("• Real-time location updates")
    
    if has_delay:
        delay_info = {
            'en': "\n⚠️ DELAY DETECTED:",
            'hi': "\n⚠️ देरी का पता चला:",
            'bn': "\n⚠️ বিলম্ব সনাক্ত:",
            'ta': "\n⚠️ தாமதம் கண்டறியப்பட்டது:"
        }
        delivery_info.append(delay_info.get(language, delay_info['en']))
        delivery_info.append("• Investigating the delay")
        delivery_info.append("• Alternative delivery options")
        delivery_info.append("• Compensation options available")
    
    # Add delivery options
    delivery_options = {
        'en': [
            "\n📋 DELIVERY OPTIONS:",
            "• Track current deliveries",
            "• View delivery history",
            "• Get delivery notifications",
            "• Contact delivery partner",
            "• Schedule future deliveries",
            "• Change delivery address",
            "• Request delivery time slot"
        ],
        'hi': [
            "\n📋 डिलीवरी विकल्प:",
            "• वर्तमान डिलीवरी ट्रैक करें",
            "• डिलीवरी इतिहास देखें",
            "• डिलीवरी नोटिफिकेशन प्राप्त करें",
            "• डिलीवरी पार्टनर से संपर्क करें",
            "• भविष्य की डिलीवरी शेड्यूल करें",
            "• डिलीवरी पता बदलें",
            "• डिलीवरी समय स्लॉट अनुरोध करें"
        ]
    }
    
    delivery_info.extend(delivery_options.get(language, delivery_options['en']))
    
    return {
        'message': {
            'type': 'list',
            'items': delivery_info
        },
        'context': {'intent': 'delivery', 'urgency': is_urgent, 'has_delay': has_delay},
        'actions': [
            {'action': 'track-current', 'label': 'Track Current Delivery'},
            {'action': 'delivery-history', 'label': 'Delivery History'},
            {'action': 'delivery-settings', 'label': 'Delivery Settings'},
            {'action': 'contact-driver', 'label': 'Contact Driver'},
            {'action': 'urgent-delivery', 'label': 'Urgent Delivery'} if is_urgent else None,
            {'action': 'report-delay', 'label': 'Report Delay'} if has_delay else None,
            {'action': 'schedule-delivery', 'label': 'Schedule Delivery'},
            {'action': 'change-address', 'label': 'Change Address'}
        ]
    }

def get_enhanced_price_response(language, vendor, message, context):
    """Generate enhanced price-related response with market insights"""
    
    # Extract price-specific keywords
    comparison_keywords = ['compare', 'comparison', 'cheaper', 'expensive', 'best price']
    alert_keywords = ['alert', 'notification', 'watch', 'monitor', 'track']
    trend_keywords = ['trend', 'trending', 'going up', 'going down', 'market']
    
    needs_comparison = any(keyword in message for keyword in comparison_keywords)
    wants_alerts = any(keyword in message for keyword in alert_keywords)
    wants_trends = any(keyword in message for keyword in trend_keywords)
    
    responses = {
        'en': "I can help you with pricing information and market insights! Here's what I found:",
        'hi': "मैं आपको मूल्य निर्धारण जानकारी और बाजार अंतर्दृष्टि में मदद कर सकता हूँ! यहाँ मैंने जो पाया है:",
        'bn': "আমি আপনাকে মূল্য নির্ধারণের তথ্য এবং বাজার অন্তর্দৃষ্টিতে সাহায্য করতে পারি! এখানে আমি যা পেয়েছি:",
        'ta': "நான் உங்களுக்கு விலை தகவல் மற்றும் சந்தை நுண்ணறிவில் உதவ முடியும்! இங்கே நான் கண்டறிந்தவை:"
    }
    
    price_info = [responses.get(language, responses['en'])]
    
    # Add current market prices
    price_info.append("\n💰 CURRENT MARKET PRICES:")
    products = Product.query.limit(5).all()
    for product in products:
        supplier = Supplier.query.get(product.supplier_id)
        price_info.append(f"• {product.name}: ₹{product.current_price}/{product.unit}")
        price_info.append(f"  From: {supplier.name} | Stock: {product.stock_available}")
    
    if needs_comparison:
        comparison_info = {
            'en': "\n📊 PRICE COMPARISON:",
            'hi': "\n📊 मूल्य तुलना:",
            'bn': "\n📊 মূল্য তুলনা:",
            'ta': "\n📊 விலை ஒப்பீடு:"
        }
        price_info.append(comparison_info.get(language, comparison_info['en']))
        price_info.append("• Tomatoes: ₹28-35/kg (Best: Krishna Mandi)")
        price_info.append("• Onions: ₹30-40/kg (Best: Fresh Farm)")
        price_info.append("• Rice: ₹40-50/kg (Best: Quality Vegetables)")
    
    if wants_trends:
        trend_info = {
            'en': "\n📈 MARKET TRENDS:",
            'hi': "\n📈 बाजार रुझान:",
            'bn': "\n📈 বাজার প্রবণতা:",
            'ta': "\n📈 சந்தை போக்குகள்:"
        }
        price_info.append(trend_info.get(language, trend_info['en']))
        price_info.append("• Vegetable prices down 5% this week")
        price_info.append("• Dairy products stable")
        price_info.append("• Spices trending upward")
    
    if wants_alerts:
        alert_info = {
            'en': "\n🔔 PRICE ALERTS:",
            'hi': "\n🔔 मूल्य अलर्ट:",
            'bn': "\n🔔 মূল্য অ্যালার্ট:",
            'ta': "\n🔔 விலை எச்சரிக்கைகள்:"
        }
        price_info.append(alert_info.get(language, alert_info['en']))
        price_info.append("• Set alerts for specific products")
        price_info.append("• Get notified of price drops")
        price_info.append("• Monitor competitor prices")
    
    # Add business-specific pricing tips
    if vendor and vendor.business_type:
        business_pricing = {
            'ice_cream': {
                'en': "\n🍦 ICE CREAM PRICING TIPS:",
                'hi': "\n🍦 आइसक्रीम मूल्य निर्धारण सुझाव:",
                'bn': "\n🍦 আইসক্রিম মূল্য নির্ধারণ টিপস:",
                'ta': "\n🍦 ஐஸ்கிரீம் விலை நிர்ணய குறிப்புகள்:"
            },
            'chaat': {
                'en': "\n🌶️ CHAAT PRICING TIPS:",
                'hi': "\n🌶️ चाट मूल्य निर्धारण सुझाव:",
                'bn': "\n🌶️ চাট মূল্য নির্ধারণ টিপস:",
                'ta': "\n🌶️ சாட் விலை நிர்ணய குறிப்புகள்:"
            }
        }
        
        tip_header = business_pricing.get(vendor.business_type, {}).get(language, "")
        if tip_header:
            price_info.append(tip_header)
            price_info.append("• Buy seasonal ingredients in bulk")
            price_info.append("• Monitor daily price fluctuations")
            price_info.append("• Negotiate better rates with regular suppliers")
    
    return {
        'message': {
            'type': 'list',
            'items': price_info
        },
        'context': {'intent': 'pricing', 'comparison': needs_comparison, 'alerts': wants_alerts, 'trends': wants_trends},
        'actions': [
            {'action': 'current-prices', 'label': 'Current Prices'},
            {'action': 'set-alerts', 'label': 'Set Price Alerts'},
            {'action': 'price-comparison', 'label': 'Compare Prices'},
            {'action': 'price-trends', 'label': 'Price Trends'},
            {'action': 'market-analysis', 'label': 'Market Analysis'},
            {'action': 'bulk-pricing', 'label': 'Bulk Pricing'},
            {'action': 'negotiate-price', 'label': 'Negotiate Price'},
            {'action': 'price-history', 'label': 'Price History'}
        ]
    }

def get_enhanced_help_response(language, vendor, message, context):
    """Generate enhanced help response with contextual assistance"""
    return get_help_response(language, vendor)

def get_enhanced_account_response(language, vendor, message, context):
    """Generate enhanced account response with personalized information"""
    return get_account_response(language, vendor)

def get_enhanced_product_response(language, vendor, message, context):
    """Generate enhanced product response with intelligent recommendations"""
    responses = {
        'en': "I can help you find the right products for your business! Here's what I recommend:",
        'hi': "मैं आपको आपके व्यवसाय के लिए सही उत्पाद खोजने में मदद कर सकता हूँ! यहाँ मेरी सिफारिश है:",
        'bn': "আমি আপনাকে আপনার ব্যবসার জন্য সঠিক পণ্য খুঁজে পেতে সাহায্য করতে পারি! এখানে আমার সুপারিশ:",
        'ta': "நான் உங்கள் வணிகத்திற்கு சரியான தயாரிப்புகளைக் கண்டுபிடிக்க உதவ முடியும்! இங்கே எனது பரிந்துரை:"
    }
    
    # Get products based on vendor's business type
    if vendor and vendor.business_type in BUSINESS_TYPE_CATEGORIES:
        categories = BUSINESS_TYPE_CATEGORIES[vendor.business_type]
        products = Product.query.filter(Product.category.in_(categories)).limit(5).all()
    else:
        products = Product.query.limit(5).all()
    
    product_list = []
    for product in products:
        supplier = Supplier.query.get(product.supplier_id)
        product_list.append(f"• {product.name}: ₹{product.current_price}/{product.unit}")
        product_list.append(f"  From: {supplier.name} | Stock: {product.stock_available}")
    
    return {
        'message': {
            'type': 'list',
            'items': [responses.get(language, responses['en'])] + product_list
        },
        'context': {'intent': 'products'},
        'actions': [
            {'action': 'browse-products', 'label': 'Browse Products'},
            {'action': 'search-products', 'label': 'Search Products'},
            {'action': 'product-details', 'label': 'Product Details'},
            {'action': 'add-to-cart', 'label': 'Add to Cart'}
        ]
    }

def get_enhanced_business_response(language, vendor, message, context):
    """Generate enhanced business response with industry insights"""
    responses = {
        'en': "I can help you with business insights and tips! Here's what I can offer:",
        'hi': "मैं आपको व्यावसायिक अंतर्दृष्टि और सुझावों में मदद कर सकता हूँ! यहाँ मैं क्या प्रदान कर सकता हूँ:",
        'bn': "আমি আপনাকে ব্যবসায়িক অন্তর্দৃষ্টি এবং টিপসে সাহায্য করতে পারি! এখানে আমি কী অফার করতে পারি:",
        'ta': "நான் உங்களுக்கு வணிக நுண்ணறிவு மற்றும் குறிப்புகளில் உதவ முடியும்! இங்கே நான் என்ன வழங்க முடியும்:"
    }
    
    business_tips = {
        'en': [
            "📊 Business Analytics and Insights",
            "🎯 Market Trends and Opportunities", 
            "💡 Industry Best Practices",
            "📈 Growth Strategies",
            "🤝 Networking Opportunities",
            "📚 Educational Resources",
            "🛠️ Business Tools and Resources",
            "📞 Expert Consultation"
        ],
        'hi': [
            "📊 व्यावसायिक विश्लेषण और अंतर्दृष्टि",
            "🎯 बाजार रुझान और अवसर",
            "💡 उद्योग सर्वोत्तम प्रथाएं",
            "📈 विकास रणनीतियां",
            "🤝 नेटवर्किंग अवसर",
            "📚 शैक्षिक संसाधन",
            "🛠️ व्यावसायिक उपकरण और संसाधन",
            "📞 विशेषज्ञ परामर्श"
        ]
    }
    
    return {
        'message': {
            'type': 'list',
            'items': [responses.get(language, responses['en'])] + business_tips.get(language, business_tips['en'])
        },
        'context': {'intent': 'business'},
        'actions': [
            {'action': 'business-analytics', 'label': 'Business Analytics'},
            {'action': 'market-trends', 'label': 'Market Trends'},
            {'action': 'best-practices', 'label': 'Best Practices'},
            {'action': 'growth-strategies', 'label': 'Growth Strategies'},
            {'action': 'networking', 'label': 'Networking'},
            {'action': 'resources', 'label': 'Resources'},
            {'action': 'consultation', 'label': 'Expert Consultation'}
        ]
    }

def get_contextual_response(previous_intent, language, vendor, context):
    """Generate contextual response based on previous conversation"""
    responses = {
        'en': f"I understand you're continuing our discussion about {previous_intent}. Let me help you further:",
        'hi': f"मैं समझता हूँ कि आप {previous_intent} के बारे में हमारी चर्चा जारी रख रहे हैं। मैं आपकी आगे मदद करूंगा:",
        'bn': f"আমি বুঝতে পারছি যে আপনি {previous_intent} সম্পর্কে আমাদের আলোচনা চালিয়ে যাচ্ছেন। আমি আপনাকে আরও সাহায্য করব:",
        'ta': f"நீங்கள் {previous_intent} பற்றி எங்கள் விவாதத்தைத் தொடர்கிறீர்கள் என்பதை நான் புரிகிறேன்। நான் உங்களுக்கு மேலும் உதவுவேன்:"
    }
    
    return {
        'message': responses.get(language, responses['en']),
        'context': {'intent': previous_intent, 'follow_up': True},
        'actions': [
            {'action': f'{previous_intent}-details', 'label': f'More {previous_intent.title()}'},
            {'action': 'related-topics', 'label': 'Related Topics'},
            {'action': 'start-over', 'label': 'Start Over'}
        ]
    }

def get_enhanced_order_response(language, vendor, message, context):
    """Generate enhanced order-related response with intelligent suggestions"""
    
    # Extract order-specific keywords
    urgent_keywords = ['urgent', 'asap', 'immediately', 'quick', 'fast', 'emergency']
    bulk_keywords = ['bulk', 'large', 'big', 'wholesale', 'many', 'lot']
    specific_keywords = ['tomatoes', 'onions', 'rice', 'oil', 'milk', 'vegetables']
    
    is_urgent = any(keyword in message for keyword in urgent_keywords)
    is_bulk = any(keyword in message for keyword in bulk_keywords)
    has_specific_items = any(keyword in message for keyword in specific_keywords)
    
    responses = {
        'en': "I can help you place an order! Let me guide you through the process:",
        'hi': "मैं आपको ऑर्डर देने में मदद कर सकता हूँ! मैं आपको प्रक्रिया के माध्यम से मार्गदर्शन करूंगा:",
        'bn': "আমি আপনাকে অর্ডার দিতে সাহায্য করতে পারি! আমি আপনাকে প্রক্রিয়ার মাধ্যমে গাইড করব:",
        'ta': "நான் உங்களுக்கு ஆர்டர் செய்ய உதவ முடியும்! நான் உங்களை செயல்முறை வழியாக வழிநடத்துவேன்:"
    }
    
    order_info = [responses.get(language, responses['en'])]
    
    # Add urgency-specific information
    if is_urgent:
        urgent_info = {
            'en': "\n🚨 URGENT ORDER DETECTED:",
            'hi': "\n🚨 तत्काल ऑर्डर का पता चला:",
            'bn': "\n🚨 জরুরি অর্ডার সনাক্ত:",
            'ta': "\n🚨 அவசர ஆர்டர் கண்டறியப்பட்டது:"
        }
        order_info.append(urgent_info.get(language, urgent_info['en']))
        order_info.append("• Same-day delivery available")
        order_info.append("• Priority suppliers recommended")
        order_info.append("• Express processing enabled")
    
    # Add bulk-specific information
    if is_bulk:
        bulk_info = {
            'en': "\n📦 BULK ORDER BENEFITS:",
            'hi': "\n📦 बल्क ऑर्डर लाभ:",
            'bn': "\n📦 বাল্ক অর্ডার সুবিধা:",
            'ta': "\n📦 மொத்த ஆர்டர் நன்மைகள்:"
        }
        order_info.append(bulk_info.get(language, bulk_info['en']))
        order_info.append("• Up to 15% discount on bulk orders")
        order_info.append("• Group ordering available")
        order_info.append("• Special wholesale rates")
    
    # Add specific item suggestions
    if has_specific_items:
        order_info.append("\n🎯 SPECIFIC ITEMS FOUND:")
        order_info.append("• I can help you find the best suppliers for these items")
        order_info.append("• Price comparison available")
        order_info.append("• Stock availability check")
    
    # Add general order options
    order_options = {
        'en': [
            "\n📋 ORDER OPTIONS:",
            "• Browse products by category",
            "• Search for specific items",
            "• Create a group order for bulk discounts",
            "• View your order history",
            "• Track current orders"
        ],
        'hi': [
            "\n📋 ऑर्डर विकल्प:",
            "• श्रेणी के अनुसार उत्पाद ब्राउज़ करें",
            "• विशिष्ट आइटम खोजें",
            "• बल्क छूट के लिए ग्रुप ऑर्डर बनाएं",
            "• अपना ऑर्डर इतिहास देखें",
            "• वर्तमान ऑर्डर ट्रैक करें"
        ],
        'bn': [
            "\n📋 অর্ডার বিকল্প:",
            "• বিভাগ অনুযায়ী পণ্য ব্রাউজ করুন",
            "• নির্দিষ্ট আইটেম খুঁজুন",
            "• বাল্ক ছাড়ের জন্য গ্রুপ অর্ডার তৈরি করুন",
            "• আপনার অর্ডার ইতিহাস দেখুন",
            "• বর্তমান অর্ডার ট্র্যাক করুন"
        ],
        'ta': [
            "\n📋 ஆர்டர் விருப்பங்கள்:",
            "• வகைப்படி தயாரிப்புகளை உலாவுங்கள்",
            "• குறிப்பிட்ட பொருட்களைத் தேடுங்கள்",
            "• மொத்த தள்ளுபடிக்கு குழு ஆர்டர் உருவாக்குங்கள்",
            "• உங்கள் ஆர்டர் வரலாற்றைப் பாருங்கள்",
            "• தற்போதைய ஆர்டர்களைக் கண்காணிக்கவும்"
        ]
    }
    
    order_info.extend(order_options.get(language, order_options['en']))
    
    # Add business-specific suggestions
    if vendor and vendor.business_type:
        business_tips = {
            'ice_cream': {
                'en': "\n🍦 ICE CREAM BUSINESS TIPS:",
                'hi': "\n🍦 आइसक्रीम व्यवसाय सुझाव:",
                'bn': "\n🍦 আইসক্রিম ব্যবসার টিপস:",
                'ta': "\n🍦 ஐஸ்கிரீம் வணிக குறிப்புகள்:"
            },
            'chaat': {
                'en': "\n🌶️ CHAAT BUSINESS TIPS:",
                'hi': "\n🌶️ चाट व्यवसाय सुझाव:",
                'bn': "\n🌶️ চাট ব্যবসার টিপস:",
                'ta': "\n🌶️ சாட் வணிக குறிப்புகள்:"
            }
        }
        
        tip_header = business_tips.get(vendor.business_type, {}).get(language, "")
        if tip_header:
            order_info.append(tip_header)
            order_info.append("• Order fresh ingredients daily")
            order_info.append("• Consider seasonal pricing")
            order_info.append("• Plan for peak hours")
    
    return {
        'message': {
            'type': 'list',
            'items': order_info
        },
        'context': {'intent': 'orders', 'urgency': is_urgent, 'bulk': is_bulk},
        'actions': [
            {'action': 'browse-products', 'label': 'Browse Products'},
            {'action': 'search-products', 'label': 'Search Products'},
            {'action': 'create-group-order', 'label': 'Create Group Order'},
            {'action': 'view-orders', 'label': 'View Orders'},
            {'action': 'urgent-order', 'label': 'Urgent Order'} if is_urgent else None,
            {'action': 'bulk-order', 'label': 'Bulk Order'} if is_bulk else None,
            {'action': 'price-check', 'label': 'Check Prices'},
            {'action': 'stock-check', 'label': 'Check Stock'}
        ]
    }

def get_delivery_response(language, vendor):
    """Generate delivery tracking response"""
    responses = {
        'en': "I can help you track your delivery! Here's what I can do:",
        'hi': "मैं आपको अपनी डिलीवरी ट्रैक करने में मदद कर सकता हूँ! यहाँ मैं क्या कर सकता हूँ:",
        'bn': "আমি আপনাকে আপনার ডেলিভারি ট্র্যাক করতে সাহায্য করতে পারি! এখানে আমি যা করতে পারি:",
        'ta': "நான் உங்கள் டெலிவரியைக் கண்காணிக்க உதவ முடியும்! இங்கே நான் என்ன செய்ய முடியும்:"
    }
    
    delivery_options = {
        'en': [
            "Track your current deliveries",
            "View delivery history",
            "Get delivery notifications",
            "Contact delivery partner"
        ],
        'hi': [
            "अपनी वर्तमान डिलीवरी ट्रैक करें",
            "डिलीवरी इतिहास देखें",
            "डिलीवरी नोटिफिकेशन प्राप्त करें",
            "डिलीवरी पार्टनर से संपर्क करें"
        ],
        'bn': [
            "আপনার বর্তমান ডেলিভারি ট্র্যাক করুন",
            "ডেলিভারি ইতিহাস দেখুন",
            "ডেলিভারি নোটিফিকেশন পান",
            "ডেলিভারি পার্টনার সাথে যোগাযোগ করুন"
        ],
        'ta': [
            "உங்கள் தற்போதைய டெலிவரிகளைக் கண்காணிக்கவும்",
            "டெலிவரி வரலாற்றைப் பாருங்கள்",
            "டெலிவரி அறிவிப்புகளைப் பெறுங்கள்",
            "டெலிவரி பங்குதாரருடன் தொடர்பு கொள்ளுங்கள்"
        ]
    }
    
    return {
        'message': {
            'type': 'list',
            'items': [responses.get(language, responses['en'])] + delivery_options.get(language, delivery_options['en'])
        },
        'context': {'intent': 'delivery'},
        'actions': [
            {'action': 'track-current', 'label': 'Track Current Delivery'},
            {'action': 'delivery-history', 'label': 'Delivery History'},
            {'action': 'delivery-settings', 'label': 'Delivery Settings'}
        ]
    }

def get_price_response(language, vendor):
    """Generate price-related response"""
    responses = {
        'en': "I can help you with pricing information! Here's what I can do:",
        'hi': "मैं आपको मूल्य निर्धारण जानकारी में मदद कर सकता हूँ! यहाँ मैं क्या कर सकता हूँ:",
        'bn': "আমি আপনাকে মূল্য নির্ধারণের তথ্যে সাহায্য করতে পারি! এখানে আমি যা করতে পারি:",
        'ta': "நான் உங்களுக்கு விலை தகவலில் உதவ முடியும்! இங்கே நான் என்ன செய்ய முடியும்:"
    }
    
    price_options = {
        'en': [
            "Show current market prices",
            "Set up price alerts",
            "Compare prices across suppliers",
            "View price trends"
        ],
        'hi': [
            "वर्तमान बाजार मूल्य दिखाएं",
            "मूल्य अलर्ट सेट करें",
            "आपूर्तिकर्ताओं में मूल्य तुलना करें",
            "मूल्य रुझान देखें"
        ],
        'bn': [
            "বর্তমান বাজার মূল্য দেখান",
            "মূল্য অ্যালার্ট সেট করুন",
            "সরবরাহকারীদের মধ্যে মূল্য তুলনা করুন",
            "মূল্য প্রবণতা দেখুন"
        ],
        'ta': [
            "தற்போதைய சந்தை விலைகளைக் காட்டுங்கள்",
            "விலை எச்சரிக்கைகளை அமைக்கவும்",
            "சப்ளையர்களிடையே விலைகளை ஒப்பிடுங்கள்",
            "விலை போக்குகளைப் பாருங்கள்"
        ]
    }
    
    return {
        'message': {
            'type': 'list',
            'items': [responses.get(language, responses['en'])] + price_options.get(language, price_options['en'])
        },
        'context': {'intent': 'pricing'},
        'actions': [
            {'action': 'current-prices', 'label': 'Current Prices'},
            {'action': 'set-alerts', 'label': 'Set Price Alerts'},
            {'action': 'price-comparison', 'label': 'Compare Prices'},
            {'action': 'price-trends', 'label': 'Price Trends'}
        ]
    }

def get_help_response(language, vendor):
    """Generate help response"""
    responses = {
        'en': "I'm here to help! Here are the main things I can assist you with:",
        'hi': "मैं मदद के लिए यहाँ हूँ! यहाँ मुख्य चीजें हैं जिनमें मैं आपकी मदद कर सकता हूँ:",
        'bn': "আমি সাহায্যের জন্য এখানে আছি! এখানে প্রধান বিষয়গুলি রয়েছে যাতে আমি আপনাকে সাহায্য করতে পারি:",
        'ta': "நான் உதவிக்காக இங்கே இருக்கிறேன்! இங்கே முக்கிய விஷயங்கள் உள்ளன, அதில் நான் உங்களுக்கு உதவ முடியும்:"
    }
    
    help_topics = {
        'en': [
            "Finding and connecting with suppliers",
            "Placing individual and group orders",
            "Tracking deliveries and shipments",
            "Managing price alerts and notifications",
            "Account settings and profile management",
            "Getting support and resolving issues"
        ],
        'hi': [
            "आपूर्तिकर्ताओं को खोजना और उनसे जुड़ना",
            "व्यक्तिगत और समूह ऑर्डर देना",
            "डिलीवरी और शिपमेंट ट्रैक करना",
            "मूल्य अलर्ट और नोटिफिकेशन प्रबंधित करना",
            "खाता सेटिंग्स और प्रोफाइल प्रबंधन",
            "सहायता प्राप्त करना और मुद्दों को हल करना"
        ],
        'bn': [
            "সরবরাহকারী খুঁজে পাওয়া এবং তাদের সাথে সংযোগ করা",
            "ব্যক্তিগত এবং গ্রুপ অর্ডার দেওয়া",
            "ডেলিভারি এবং শিপমেন্ট ট্র্যাক করা",
            "মূল্য অ্যালার্ট এবং নোটিফিকেশন পরিচালনা করা",
            "অ্যাকাউন্ট সেটিংস এবং প্রোফাইল পরিচালনা",
            "সহায়তা পাওয়া এবং সমস্যা সমাধান করা"
        ],
        'ta': [
            "சப்ளையர்களைக் கண்டுபிடித்தல் மற்றும் அவர்களுடன் இணைத்தல்",
            "தனிப்பட்ட மற்றும் குழு ஆர்டர்களை வைத்தல்",
            "டெலிவரி மற்றும் ஷிப்மென்ட்களைக் கண்காணித்தல்",
            "விலை எச்சரிக்கைகள் மற்றும் அறிவிப்புகளை நிர்வகித்தல்",
            "கணக்கு அமைப்புகள் மற்றும் சுயவிவர நிர்வாகம்",
            "ஆதரவு பெறுதல் மற்றும் பிரச்சினைகளைத் தீர்ப்பது"
        ]
    }
    
    return {
        'message': {
            'type': 'list',
            'items': [responses.get(language, responses['en'])] + help_topics.get(language, help_topics['en'])
        },
        'context': {'intent': 'help'},
        'actions': [
            {'action': 'contact-support', 'label': 'Contact Support'},
            {'action': 'faq', 'label': 'View FAQ'},
            {'action': 'tutorial', 'label': 'Watch Tutorial'},
            {'action': 'feedback', 'label': 'Send Feedback'}
        ]
    }

def get_account_response(language, vendor):
    """Generate account-related response"""
    if not vendor:
        responses = {
            'en': "You need to log in to access your account features. Would you like to log in?",
            'hi': "अपने खाता फीचर्स तक पहुँचने के लिए आपको लॉग इन करना होगा। क्या आप लॉग इन करना चाहते हैं?",
            'bn': "আপনার অ্যাকাউন্ট ফিচার অ্যাক্সেস করতে আপনাকে লগ ইন করতে হবে। আপনি কি লগ ইন করতে চান?",
            'ta': "உங்கள் கணக்கு அம்சங்களை அணுக நீங்கள் உள்நுழைய வேண்டும்। நீங்கள் உள்நுழைய விரும்புகிறீர்களா?"
        }
        
        return {
            'message': responses.get(language, responses['en']),
            'context': {'intent': 'account', 'requires_login': True},
            'actions': [
                {'action': 'login', 'label': 'Log In'},
                {'action': 'register', 'label': 'Register'}
            ]
        }
    
    responses = {
        'en': f"Welcome back, {vendor.name}! Here's your account overview:",
        'hi': f"वापस स्वागत है, {vendor.name}! यहाँ आपका खाता अवलोकन है:",
        'bn': f"ফিরে স্বাগতম, {vendor.name}! এখানে আপনার অ্যাকাউন্ট ওভারভিউ:",
        'ta': f"மீண்டும் வரவேற்கிறோம், {vendor.name}! இங்கே உங்கள் கணக்கு கண்ணோட்டம்:"
    }
    
    account_info = {
        'en': [
            f"Business Type: {vendor.business_type.title()}",
            f"Location: {vendor.location}",
            f"Phone: {vendor.phone}",
            "View your order history",
            "Update profile information",
            "Change password",
            "Manage notifications"
        ],
        'hi': [
            f"व्यवसाय प्रकार: {vendor.business_type.title()}",
            f"स्थान: {vendor.location}",
            f"फोन: {vendor.phone}",
            "अपना ऑर्डर इतिहास देखें",
            "प्रोफाइल जानकारी अपडेट करें",
            "पासवर्ड बदलें",
            "नोटिफिकेशन प्रबंधित करें"
        ],
        'bn': [
            f"ব্যবসার ধরন: {vendor.business_type.title()}",
            f"অবস্থান: {vendor.location}",
            f"ফোন: {vendor.phone}",
            "আপনার অর্ডার ইতিহাস দেখুন",
            "প্রোফাইল তথ্য আপডেট করুন",
            "পাসওয়ার্ড পরিবর্তন করুন",
            "নোটিফিকেশন পরিচালনা করুন"
        ],
        'ta': [
            f"வணிக வகை: {vendor.business_type.title()}",
            f"இடம்: {vendor.location}",
            f"தொலைபேசி: {vendor.phone}",
            "உங்கள் ஆர்டர் வரலாற்றைப் பாருங்கள்",
            "சுயவிவர தகவலைப் புதுப்பிக்கவும்",
            "கடவுச்சொல்லை மாற்றவும்",
            "அறிவிப்புகளை நிர்வகிக்கவும்"
        ]
    }
    
    return {
        'message': {
            'type': 'list',
            'items': [responses.get(language, responses['en'])] + account_info.get(language, account_info['en'])
        },
        'context': {'intent': 'account', 'vendor_id': vendor.id},
        'actions': [
            {'action': 'view-profile', 'label': 'View Profile'},
            {'action': 'edit-profile', 'label': 'Edit Profile'},
            {'action': 'order-history', 'label': 'Order History'},
            {'action': 'settings', 'label': 'Settings'}
        ]
    }

def get_intelligent_default_response(language, vendor, message, context):
    """Generate intelligent default response with context awareness and suggestions"""
    
    # Analyze the message for potential keywords
    keywords_found = []
    all_keywords = {
        'supplier': ['supplier', 'vendor', 'seller', 'dealer', 'wholesale'],
        'product': ['product', 'item', 'goods', 'materials', 'ingredients'],
        'price': ['price', 'cost', 'expensive', 'cheap', 'rate'],
        'order': ['order', 'buy', 'purchase', 'need', 'want'],
        'delivery': ['delivery', 'ship', 'send', 'transport'],
        'business': ['business', 'shop', 'store', 'restaurant', 'food']
    }
    
    for category, keywords in all_keywords.items():
        if any(keyword in message for keyword in keywords):
            keywords_found.append(category)
    
    # Generate contextual response
    if keywords_found:
        responses = {
            'en': f"I can see you're interested in {', '.join(keywords_found)}. Let me help you with that:",
            'hi': f"मैं देख सकता हूँ कि आप {', '.join(keywords_found)} में रुचि रखते हैं। मैं आपकी मदद करूंगा:",
            'bn': f"আমি দেখতে পাচ্ছি যে আপনি {', '.join(keywords_found)} নিয়ে আগ্রহী। আমি আপনাকে সাহায্য করব:",
            'ta': f"நீங்கள் {', '.join(keywords_found)} பற்றி ஆர்வமாக இருப்பதை நான் பார்க்கிறேன்। நான் உங்களுக்கு உதவுவேன்:"
        }
        
        base_message = responses.get(language, responses['en'])
        
        # Add specific suggestions based on keywords found
        suggestions = []
        if 'supplier' in keywords_found:
            suggestions.extend([
                "• Find verified suppliers near you",
                "• Compare supplier ratings and prices",
                "• Contact suppliers directly"
            ])
        if 'product' in keywords_found:
            suggestions.extend([
                "• Browse products by category",
                "• Search for specific items",
                "• Check product availability"
            ])
        if 'price' in keywords_found:
            suggestions.extend([
                "• Compare prices across suppliers",
                "• Set up price alerts",
                "• Find bulk discounts"
            ])
        if 'order' in keywords_found:
            suggestions.extend([
                "• Place individual orders",
                "• Create group orders for savings",
                "• Track order status"
            ])
        if 'delivery' in keywords_found:
            suggestions.extend([
                "• Track your deliveries",
                "• Schedule delivery times",
                "• Get delivery notifications"
            ])
        if 'business' in keywords_found:
            suggestions.extend([
                "• Get business tips and advice",
                "• Access market trends",
                "• Connect with other vendors"
            ])
        
        return {
            'message': {
                'type': 'list',
                'items': [base_message] + suggestions
            },
            'context': {'intent': 'unclear', 'keywords_found': keywords_found},
            'actions': [
                {'action': 'find-suppliers', 'label': 'Find Suppliers'},
                {'action': 'browse-products', 'label': 'Browse Products'},
                {'action': 'compare-prices', 'label': 'Compare Prices'},
                {'action': 'place-order', 'label': 'Place Order'},
                {'action': 'track-delivery', 'label': 'Track Delivery'},
                {'action': 'business-tips', 'label': 'Business Tips'}
            ]
        }
    
    # If no keywords found, provide general help
    responses = {
        'en': "I'm here to help you with your business needs! Here are some things I can assist you with:",
        'hi': "मैं आपकी व्यावसायिक जरूरतों में आपकी मदद करने के लिए यहाँ हूँ! यहाँ कुछ चीजें हैं जिनमें मैं आपकी मदद कर सकता हूँ:",
        'bn': "আমি আপনার ব্যবসায়িক প্রয়োজনে সাহায্য করতে এখানে আছি! এখানে কিছু বিষয় রয়েছে যাতে আমি আপনাকে সাহায্য করতে পারি:",
        'ta': "உங்கள் வணிகத் தேவைகளுக்கு உதவ நான் இங்கே இருக்கிறேன்! இங்கே சில விஷயங்கள் உள்ளன, அதில் நான் உங்களுக்கு உதவ முடியும்:"
    }
    
    general_options = {
        'en': [
            "🔍 Finding and connecting with suppliers",
            "🛒 Placing individual and group orders",
            "📦 Tracking deliveries and shipments",
            "💰 Managing price alerts and notifications",
            "👤 Account settings and profile management",
            "📞 Getting support and resolving issues",
            "📊 Business analytics and insights",
            "🎯 Market trends and opportunities"
        ],
        'hi': [
            "🔍 आपूर्तिकर्ताओं को खोजना और उनसे जुड़ना",
            "🛒 व्यक्तिगत और समूह ऑर्डर देना",
            "📦 डिलीवरी और शिपमेंट ट्रैक करना",
            "💰 मूल्य अलर्ट और नोटिफिकेशन प्रबंधित करना",
            "👤 खाता सेटिंग्स और प्रोफाइल प्रबंधन",
            "📞 सहायता प्राप्त करना और मुद्दों को हल करना",
            "📊 व्यावसायिक विश्लेषण और अंतर्दृष्टि",
            "🎯 बाजार रुझान और अवसर"
        ],
        'bn': [
            "🔍 সরবরাহকারী খুঁজে পাওয়া এবং তাদের সাথে সংযোগ করা",
            "🛒 ব্যক্তিগত এবং গ্রুপ অর্ডার দেওয়া",
            "📦 ডেলিভারি এবং শিপমেন্ট ট্র্যাক করা",
            "💰 মূল্য অ্যালার্ট এবং নোটিফিকেশন পরিচালনা করা",
            "👤 অ্যাকাউন্ট সেটিংস এবং প্রোফাইল পরিচালনা",
            "📞 সহায়তা পাওয়া এবং সমস্যা সমাধান করা",
            "📊 ব্যবসায়িক বিশ্লেষণ এবং অন্তর্দৃষ্টি",
            "🎯 বাজার প্রবণতা এবং সুযোগ"
        ],
        'ta': [
            "🔍 சப்ளையர்களைக் கண்டுபிடித்தல் மற்றும் அவர்களுடன் இணைத்தல்",
            "🛒 தனிப்பட்ட மற்றும் குழு ஆர்டர்களை வைத்தல்",
            "📦 டெலிவரி மற்றும் ஷிப்மென்ட்களைக் கண்காணித்தல்",
            "💰 விலை எச்சரிக்கைகள் மற்றும் அறிவிப்புகளை நிர்வகித்தல்",
            "👤 கணக்கு அமைப்புகள் மற்றும் சுயவிவர நிர்வாகம்",
            "📞 ஆதரவு பெறுதல் மற்றும் பிரச்சினைகளைத் தீர்ப்பது",
            "📊 வணிக பகுப்பாய்வு மற்றும் நுண்ணறிவு",
            "🎯 சந்தை போக்குகள் மற்றும் வாய்ப்புகள்"
        ]
    }
    
    # Add personalized suggestions if vendor is logged in
    if vendor:
        personalized_tips = {
            'en': f"\n\n👋 Hi {vendor.name}! Since you're in the {vendor.business_type} business, here are some personalized suggestions:",
            'hi': f"\n\n👋 नमस्ते {vendor.name}! चूंकि आप {vendor.business_type} व्यवसाय में हैं, यहाँ कुछ व्यक्तिगत सुझाव हैं:",
            'bn': f"\n\n👋 হাই {vendor.name}! যেহেতু আপনি {vendor.business_type} ব্যবসায় আছেন, এখানে কিছু ব্যক্তিগত পরামর্শ:",
            'ta': f"\n\n👋 வணக்கம் {vendor.name}! நீங்கள் {vendor.business_type} வணிகத்தில் இருப்பதால், இங்கே சில தனிப்பட்ட பரிந்துரைகள்:"
        }
        
        business_specific_tips = {
            'ice_cream': {
                'en': [
                    "• Check dairy supplier ratings for quality",
                    "• Order seasonal fruits for new flavors",
                    "• Monitor temperature-sensitive deliveries"
                ],
                'hi': [
                    "• गुणवत्ता के लिए डेयरी आपूर्तिकर्ता रेटिंग जांचें",
                    "• नए स्वादों के लिए मौसमी फल ऑर्डर करें",
                    "• तापमान-संवेदनशील डिलीवरी की निगरानी करें"
                ]
            },
            'chaat': {
                'en': [
                    "• Source fresh vegetables daily",
                    "• Find authentic spice suppliers",
                    "• Plan for peak evening hours"
                ],
                'hi': [
                    "• दैनिक ताजी सब्जियां सोर्स करें",
                    "• प्रामाणिक मसाला आपूर्तिकर्ता खोजें",
                    "• शाम के पीक घंटों की योजना बनाएं"
                ]
            }
        }
        
        tip_header = personalized_tips.get(language, personalized_tips['en'])
        tips = business_specific_tips.get(vendor.business_type, {}).get(language, [])
        
        if tips:
            general_options[language].append(tip_header)
            general_options[language].extend(tips)
    
    return {
        'message': {
            'type': 'list',
            'items': [responses.get(language, responses['en'])] + general_options.get(language, general_options['en'])
        },
        'context': {'intent': 'unclear', 'general_help': True},
        'actions': [
            {'action': 'find-suppliers', 'label': 'Find Suppliers'},
            {'action': 'place-order', 'label': 'Place Order'},
            {'action': 'track-delivery', 'label': 'Track Delivery'},
            {'action': 'price-alerts', 'label': 'Price Alerts'},
            {'action': 'account-settings', 'label': 'Account Settings'},
            {'action': 'contact-support', 'label': 'Contact Support'},
            {'action': 'business-analytics', 'label': 'Business Analytics'},
            {'action': 'market-trends', 'label': 'Market Trends'}
        ]
    }

@app.route('/chatbot')
def chatbot_page():
    """Dedicated chatbot page for testing"""
    return render_template('chatbot.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Only create sample data if database is empty
        if not Supplier.query.first():
            create_sample_data()
        create_sample_orders()
        create_sample_vendors()
    
if __name__ == '__main__':
    # For production deployment on Render
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug, host='0.0.0.0', port=port) 
