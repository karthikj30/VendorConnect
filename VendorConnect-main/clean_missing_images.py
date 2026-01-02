"""
Clean up menu items with missing image files
"""
from app import app, db, MenuItem
import os

def clean_missing_images():
    with app.app_context():
        items = MenuItem.query.all()
        cleaned = 0
        
        for item in items:
            if item.image:
                image_path = os.path.join(app.root_path, 'static', item.image)
                if not os.path.exists(image_path):
                    print(f"Removing missing image reference: {item.image} for item: {item.name}")
                    item.image = None
                    cleaned += 1
        
        if cleaned > 0:
            db.session.commit()
            print(f"✓ Cleaned {cleaned} menu item(s) with missing images")
        else:
            print("✓ No missing images found")

if __name__ == '__main__':
    clean_missing_images()
