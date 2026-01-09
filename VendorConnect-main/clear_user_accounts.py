#!/usr/bin/env python3
"""
One-time script to clear all user accounts from the database
"""

import sys
import os

# Prevent Flask from running automatically
os.environ['SKIP_FLASK_RUN'] = '1'

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vendorconnect.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app)
db = SQLAlchemy(app)

# Import models
class Customer(db.Model):
    __tablename__ = 'customer'
    id = db.Column(db.Integer, primary_key=True)

class Vendor(db.Model):
    __tablename__ = 'vendor'
    id = db.Column(db.Integer, primary_key=True)

class Supplier(db.Model):
    __tablename__ = 'supplier'
    id = db.Column(db.Integer, primary_key=True)

class DeliveryAgent(db.Model):
    __tablename__ = 'delivery_agent'
    id = db.Column(db.Integer, primary_key=True)

class Admin(db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)

def clear_all_accounts():
    """Delete all user accounts from the database"""
    with app.app_context():
        print("🗑️  Clearing all user accounts from database...\n")
        
        # Count before deletion
        customer_count = Customer.query.count()
        vendor_count = Vendor.query.count()
        supplier_count = Supplier.query.count()
        delivery_agent_count = DeliveryAgent.query.count()
        admin_count = Admin.query.count()
        
        print(f"📊 Accounts found:")
        print(f"   - Customers: {customer_count}")
        print(f"   - Vendors: {vendor_count}")
        print(f"   - Suppliers: {supplier_count}")
        print(f"   - Delivery Agents: {delivery_agent_count}")
        print(f"   - Admins: {admin_count}")
        print(f"\nTotal: {customer_count + vendor_count + supplier_count + delivery_agent_count + admin_count} accounts\n")
        
        # Delete all accounts
        try:
            Customer.query.delete()
            print("✅ Deleted all customers")
            
            Vendor.query.delete()
            print("✅ Deleted all vendors")
            
            Supplier.query.delete()
            print("✅ Deleted all suppliers")
            
            DeliveryAgent.query.delete()
            print("✅ Deleted all delivery agents")
            
            Admin.query.delete()
            print("✅ Deleted all admins")
            
            db.session.commit()
            print("\n✅ All user accounts have been cleared successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error clearing accounts: {str(e)}")
            return False
            
    return True

if __name__ == '__main__':
    clear_all_accounts()
