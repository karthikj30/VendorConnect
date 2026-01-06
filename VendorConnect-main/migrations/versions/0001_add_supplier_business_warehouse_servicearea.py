"""add supplier business fields and add Warehouse and ServiceArea tables

Revision ID: 0001_add_supplier_business_warehouse_servicearea
Revises: 
Create Date: 2026-01-06 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_add_supplier_business_warehouse_servicearea'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # add columns to supplier
    op.add_column('supplier', sa.Column('business_name', sa.String(length=200), nullable=True))
    op.add_column('supplier', sa.Column('gstin', sa.String(length=20), nullable=True))

    # create warehouses table
    op.create_table('warehouse',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('supplier_id', sa.Integer, sa.ForeignKey('supplier.id'), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('address', sa.String(length=400), nullable=False),
        sa.Column('phone', sa.String(length=30), nullable=True),
        sa.Column('latitude', sa.Float, nullable=True),
        sa.Column('longitude', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=True)
    )

    # create service_areas table
    op.create_table('service_area',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('supplier_id', sa.Integer, sa.ForeignKey('supplier.id'), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=400), nullable=True),
        sa.Column('postal_codes', sa.Text, nullable=True),
        sa.Column('radius_km', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=True)
    )


def downgrade():
    op.drop_table('service_area')
    op.drop_table('warehouse')
    op.drop_column('supplier', 'gstin')
    op.drop_column('supplier', 'business_name')
