This folder contains example Alembic migration scripts.

Steps to apply these migrations in a deployment environment:

1. Install dependencies:
   pip install -r requirements.txt

2. Initialize Flask-Migrate in your project (if not already):
   - from flask_migrate import Migrate
   - migrate = Migrate(app, db)
   - You can add this to `app.py` near the db initialization. (Ensure app and db are imported/visible.)

3. Initialize alembic directory and stamp current DB (if starting fresh):
   flask db init
   flask db migrate -m "Initial migrations"
   flask db upgrade

4. Or apply the example migration file in `migrations/versions/0001_add_supplier_business_warehouse_servicearea.py` by placing it under `migrations/versions/` and running:
   flask db upgrade

Notes:
- The example migration assumes the `supplier` table exists. Review SQL before applying to production backups and test on a staging DB first.
- If you prefer manual SQL migrations, generate the appropriate ALTER TABLE and CREATE TABLE statements using your DB's syntax.
