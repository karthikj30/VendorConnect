"""
Migration script to change Promotion from per-click to per-view model.
"""
from app import app, db
from sqlalchemy import text, inspect

def migrate_promotion_to_views():
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            
            # Check Promotion table columns
            promo_columns = inspector.get_columns('promotion')
            promo_col_names = {col['name'] for col in promo_columns}
            
            # Rename price_per_click to price_per_view if it exists
            if 'price_per_click' in promo_col_names and 'price_per_view' not in promo_col_names:
                db.session.execute(text("ALTER TABLE promotion RENAME COLUMN price_per_click TO price_per_view"))
                print("\u2713 Renamed price_per_click to price_per_view in Promotion table")
            elif 'price_per_view' in promo_col_names:
                print("\u2713 price_per_view column already exists in Promotion table")
            
            # Rename total_clicks to total_views if it exists
            if 'total_clicks' in promo_col_names and 'total_views' not in promo_col_names:
                db.session.execute(text("ALTER TABLE promotion RENAME COLUMN total_clicks TO total_views"))
                print("\u2713 Renamed total_clicks to total_views in Promotion table")
            elif 'total_views' in promo_col_names:
                print("\u2713 total_views column already exists in Promotion table")
            
            # Check if PromotionClick table exists and rename to PromotionView
            tables = inspector.get_table_names()
            if 'promotion_click' in tables and 'promotion_view' not in tables:
                db.session.execute(text("ALTER TABLE promotion_click RENAME TO promotion_view"))
                print("\u2713 Renamed promotion_click table to promotion_view")
            elif 'promotion_view' in tables:
                print("\u2713 promotion_view table already exists")
            
            # Rename clicked_at to viewed_at if promotion_view table exists
            if 'promotion_view' in inspector.get_table_names():
                view_columns = inspector.get_columns('promotion_view')
                view_col_names = {col['name'] for col in view_columns}
                
                if 'clicked_at' in view_col_names and 'viewed_at' not in view_col_names:
                    db.session.execute(text("ALTER TABLE promotion_view RENAME COLUMN clicked_at TO viewed_at"))
                    print("\u2713 Renamed clicked_at to viewed_at in promotion_view table")
                elif 'viewed_at' in view_col_names:
                    print("\u2713 viewed_at column already exists in promotion_view table")
            
            db.session.commit()
            print("\n\u2713 Successfully migrated promotion system from per-click to per-view!")
            
        except Exception as exc:
            db.session.rollback()
            print(f"\u2717 Error migrating promotion tables: {exc}")

if __name__ == '__main__':
    migrate_promotion_to_views()
