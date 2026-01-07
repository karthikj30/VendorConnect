"""
Migration script to change Promotion from per-click to per-view model.
Handles MySQL, SQLite, and PostgreSQL with proper dialect-specific DDL.

Note: For production use, consider converting to Alembic migration for more robust cross-DB handling.
"""
from app import app, db
from sqlalchemy import text, inspect

def migrate_promotion_to_views():
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            dialect = db.engine.dialect.name
            print(f"\nDetected database dialect: {dialect}")
            
            # Start transaction
            with db.session.begin_nested():
                # Check Promotion table columns
                promo_columns = inspector.get_columns('promotion')
                promo_col_names = {col['name'] for col in promo_columns}
                
                # Rename price_per_click to price_per_view if it exists
                if 'price_per_click' in promo_col_names and 'price_per_view' not in promo_col_names:
                    print("Renaming price_per_click to price_per_view...")
                    if dialect == 'mysql':
                        # Get column definition for MySQL
                        col_type = next((str(c['type']) for c in promo_columns if c['name'] == 'price_per_click'), 'FLOAT')
                        db.session.execute(text(f"ALTER TABLE promotion CHANGE price_per_click price_per_view {col_type}"))
                    elif dialect == 'sqlite':
                        # SQLite: Check version for RENAME COLUMN support (3.25.0+)
                        result = db.session.execute(text("SELECT sqlite_version()")).scalar()
                        version_parts = list(map(int, result.split('.')))
                        if version_parts >= [3, 25, 0]:
                            db.session.execute(text("ALTER TABLE promotion RENAME COLUMN price_per_click TO price_per_view"))
                        else:
                            print(f"SQLite version {result} < 3.25.0, skipping column rename (requires table recreation)")
                            raise Exception("SQLite version too old for RENAME COLUMN. Please upgrade to 3.25.0+")
                    else:  # PostgreSQL and others
                        db.session.execute(text("ALTER TABLE promotion RENAME COLUMN price_per_click TO price_per_view"))
                    print("✓ Renamed price_per_click to price_per_view in Promotion table")
                elif 'price_per_view' in promo_col_names:
                    print("✓ price_per_view column already exists in Promotion table")
                
                # Rename total_clicks to total_views if it exists
                if 'total_clicks' in promo_col_names and 'total_views' not in promo_col_names:
                    print("Renaming total_clicks to total_views...")
                    if dialect == 'mysql':
                        col_type = next((str(c['type']) for c in promo_columns if c['name'] == 'total_clicks'), 'INTEGER')
                        db.session.execute(text(f"ALTER TABLE promotion CHANGE total_clicks total_views {col_type}"))
                    elif dialect == 'sqlite':
                        result = db.session.execute(text("SELECT sqlite_version()")).scalar()
                        version_parts = list(map(int, result.split('.')))
                        if version_parts >= [3, 25, 0]:
                            db.session.execute(text("ALTER TABLE promotion RENAME COLUMN total_clicks TO total_views"))
                        else:
                            raise Exception("SQLite version too old for RENAME COLUMN. Please upgrade to 3.25.0+")
                    else:  # PostgreSQL and others
                        db.session.execute(text("ALTER TABLE promotion RENAME COLUMN total_clicks TO total_views"))
                    print("✓ Renamed total_clicks to total_views in Promotion table")
                elif 'total_views' in promo_col_names:
                    print("✓ total_views column already exists in Promotion table")
                
                # Check if PromotionClick table exists and rename to PromotionView
                tables = inspector.get_table_names()
                if 'promotion_click' in tables and 'promotion_view' not in tables:
                    print("Renaming promotion_click table to promotion_view...")
                    
                    # Get foreign keys before rename
                    fks = inspector.get_foreign_keys('promotion_click')
                    print(f"Found {len(fks)} foreign key constraints on promotion_click table")
                    
                    # Drop foreign keys if they exist (to avoid FK errors during rename)
                    dropped_fks = []
                    for fk in fks:
                        fk_name = fk.get('name')
                        if fk_name:
                            try:
                                if dialect == 'mysql':
                                    db.session.execute(text(f"ALTER TABLE promotion_click DROP FOREIGN KEY {fk_name}"))
                                elif dialect == 'postgresql':
                                    db.session.execute(text(f"ALTER TABLE promotion_click DROP CONSTRAINT {fk_name}"))
                                elif dialect == 'sqlite':
                                    # SQLite doesn't support dropping FK constraints directly
                                    print(f"SQLite: Cannot drop FK {fk_name} (will be preserved during rename)")
                                    continue
                                dropped_fks.append(fk)
                                print(f"  Dropped FK constraint: {fk_name}")
                            except Exception as e:
                                print(f"  Warning: Could not drop FK {fk_name}: {e}")
                    
                    # Rename table
                    if dialect == 'mysql':
                        db.session.execute(text("RENAME TABLE promotion_click TO promotion_view"))
                    else:  # PostgreSQL, SQLite
                        db.session.execute(text("ALTER TABLE promotion_click RENAME TO promotion_view"))
                    print("✓ Renamed promotion_click table to promotion_view")
                    
                    # Recreate foreign keys
                    for fk in dropped_fks:
                        fk_name = fk.get('name')
                        referred_table = fk.get('referred_table')
                        constrained_cols = ','.join(fk.get('constrained_columns', []))
                        referred_cols = ','.join(fk.get('referred_columns', []))
                        try:
                            if dialect == 'mysql':
                                db.session.execute(text(
                                    f"ALTER TABLE promotion_view ADD CONSTRAINT {fk_name} "
                                    f"FOREIGN KEY ({constrained_cols}) REFERENCES {referred_table}({referred_cols})"
                                ))
                            elif dialect == 'postgresql':
                                db.session.execute(text(
                                    f"ALTER TABLE promotion_view ADD CONSTRAINT {fk_name} "
                                    f"FOREIGN KEY ({constrained_cols}) REFERENCES {referred_table}({referred_cols})"
                                ))
                            print(f"  Recreated FK constraint: {fk_name}")
                        except Exception as e:
                            print(f"  Warning: Could not recreate FK {fk_name}: {e}")
                    
                elif 'promotion_view' in tables:
                    print("✓ promotion_view table already exists")
                
                # Rename clicked_at to viewed_at if promotion_view table exists
                if 'promotion_view' in inspector.get_table_names():
                    view_columns = inspector.get_columns('promotion_view')
                    view_col_names = {col['name'] for col in view_columns}
                    
                    if 'clicked_at' in view_col_names and 'viewed_at' not in view_col_names:
                        print("Renaming clicked_at to viewed_at...")
                        if dialect == 'mysql':
                            col_type = next((str(c['type']) for c in view_columns if c['name'] == 'clicked_at'), 'DATETIME')
                            db.session.execute(text(f"ALTER TABLE promotion_view CHANGE clicked_at viewed_at {col_type}"))
                        elif dialect == 'sqlite':
                            result = db.session.execute(text("SELECT sqlite_version()")).scalar()
                            version_parts = list(map(int, result.split('.')))
                            if version_parts >= [3, 25, 0]:
                                db.session.execute(text("ALTER TABLE promotion_view RENAME COLUMN clicked_at TO viewed_at"))
                            else:
                                raise Exception("SQLite version too old for RENAME COLUMN. Please upgrade to 3.25.0+")
                        else:  # PostgreSQL and others
                            db.session.execute(text("ALTER TABLE promotion_view RENAME COLUMN clicked_at TO viewed_at"))
                        print("✓ Renamed clicked_at to viewed_at in promotion_view table")
                    elif 'viewed_at' in view_col_names:
                        print("✓ viewed_at column already exists in promotion_view table")
            
            # Commit transaction
            db.session.commit()
            print("\n✓ Successfully migrated promotion system from per-click to per-view!")
            print("\nRecommendation: Consider converting this script to an Alembic migration for more robust cross-DB handling.")
            
        except Exception as exc:
            db.session.rollback()
            print(f"\n✗ Error migrating promotion tables: {exc}")
            print("Transaction rolled back. Database remains in consistent state.")
            raise

if __name__ == '__main__':
    migrate_promotion_to_views()
