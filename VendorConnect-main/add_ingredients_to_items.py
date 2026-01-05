"""
Script to add sample ingredients to existing menu items
"""
import sys
sys.path.insert(0, '/workspaces/VendorConnect/VendorConnect-main')

from app import app, db
from app import MenuItem

# Sample ingredients for different items
ingredients_map = {
    'Ice Cream': 'Milk, Cream, Sugar, Vanilla Extract',
    'Dosa': 'Rice, Urid Dal, Salt, Oil',
    'Samosa': 'Potato, Onion, Peas, Spices, Pastry Flour',
    'Chai': 'Tea Leaves, Milk, Sugar, Ginger, Cardamom',
    'Juice': 'Fresh Fruits, Water, Sugar',
    'Vada': 'Urid Dal, Salt, Cumin, Onion, Oil',
    'Pav': 'Maida, Salt, Sugar, Yeast, Butter',
    'Chaat': 'Potato, Chickpeas, Tamarind, Mint, Spices',
    'Tea': 'Tea Leaves, Milk, Sugar, Ginger, Cardamom',
}

with app.app_context():
    # Get all menu items
    items = MenuItem.query.all()
    
    print(f"📝 Found {len(items)} menu items")
    
    updated_count = 0
    for item in items:
        # Check if ingredients already exist
        if not item.ingredients or item.ingredients.strip() == '':
            # Try to match by name
            for key, value in ingredients_map.items():
                if key.lower() in item.name.lower():
                    item.ingredients = value
                    updated_count += 1
                    print(f"✅ {item.name}: {value}")
                    break
            else:
                # Default ingredients if no match
                if updated_count == 0:
                    item.ingredients = 'Premium Quality Ingredients'
                    print(f"✅ {item.name}: (generic ingredients)")
                    updated_count += 1
    
    if updated_count > 0:
        db.session.commit()
        print(f"\n✅ Successfully added ingredients to {updated_count} items!")
    else:
        print("\n✅ All items already have ingredients!")

print("\n✅ Ingredients setup completed!")
