from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import json
import random
from datetime import datetime, timedelta
import requests
from werkzeug.security import generate_password_hash, check_password_hash
import os  # ✅ add this

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vendorconnect_secret_key_2024'

# ✅ fix DB path
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, '../instance/vendorconnect.db')
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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Only create sample data if database is empty
        if not Supplier.query.first():
            create_sample_data()
        create_sample_orders()
        create_sample_vendors()
    
    app.run(debug=True, host='0.0.0.0', port=5000) 
