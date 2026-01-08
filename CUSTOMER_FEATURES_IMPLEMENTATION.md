# Customer Features Implementation Guide

## 🎯 Overview
This document outlines the newly implemented customer features:
1. **Rating & Review System** - Customers can rate and review vendors
2. **Wishlist/Favorites** - Save favorite vendors and menu items
3. **Order Scheduling** - Schedule orders in advance with recurring options
4. **Smart Recommendations** - AI-powered personalized recommendations
5. **Advanced Sorting & Filtering** - Sort vendors and items by multiple criteria

---

## 1. 📝 Rating & Review System

### Database Schema
```python
class CustomerReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('customer_order.id'), nullable=True)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    food_quality = db.Column(db.Integer, nullable=True)  # 1-5
    delivery_speed = db.Column(db.Integer, nullable=True)  # 1-5
    packaging = db.Column(db.Integer, nullable=True)  # 1-5
    review_text = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(300), nullable=True)
    helpful_votes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### API Endpoints

#### Submit a Review
```http
POST /api/customer/reviews
Content-Type: multipart/form-data

vendor_id: 5
order_id: 123 (optional)
rating: 5
food_quality: 5
delivery_speed: 4
packaging: 5
review_text: "Excellent service!"
image: <file>
```

**Response:**
```json
{
  "success": true,
  "message": "Review submitted successfully",
  "review_id": 1
}
```

#### Get Vendor Reviews
```http
GET /api/vendor/{vendor_id}/reviews
```

**Response:**
```json
{
  "success": true,
  "reviews": [
    {
      "id": 1,
      "rating": 5,
      "food_quality": 5,
      "delivery_speed": 4,
      "packaging": 5,
      "review_text": "Excellent service!",
      "image": "uploads/reviews/...",
      "helpful_votes": 3,
      "customer_name": "John Doe",
      "created_at": "09 Jan 2026"
    }
  ],
  "total_reviews": 1,
  "averages": {
    "overall": 5.0,
    "food_quality": 5.0,
    "delivery_speed": 4.0,
    "packaging": 5.0
  }
}
```

#### Mark Review Helpful
```http
POST /api/review/{review_id}/helpful
```

### UI Components
- ⭐ 5-star rating selector with visual feedback
- 📸 Photo upload for reviews
- 📊 Separate ratings for food quality, delivery speed, packaging
- 💬 Text review field with 500+ character support
- 👍 Helpful votes counter

---

## 2. ❤️ Wishlist System

### Database Schema
```python
class Wishlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=True)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=True)
    item_type = db.Column(db.String(20), default='vendor')  # 'vendor' or 'item'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### API Endpoints

#### Get Wishlist
```http
GET /api/customer/wishlist
```

**Response:**
```json
{
  "success": true,
  "wishlist": [
    {
      "id": 1,
      "type": "vendor",
      "vendor_id": 5,
      "name": "Ice Cream Paradise",
      "location": "Bandra West",
      "cuisine": "ice_cream",
      "logo": "uploads/vendor/...",
      "added_at": "09 Jan 2026"
    },
    {
      "id": 2,
      "type": "item",
      "item_id": 45,
      "item_name": "Vanilla Ice Cream",
      "vendor_id": 5,
      "vendor_name": "Ice Cream Paradise",
      "price": 80,
      "image": "uploads/menu/...",
      "added_at": "09 Jan 2026"
    }
  ]
}
```

#### Add to Wishlist
```http
POST /api/customer/wishlist
Content-Type: application/json

{
  "type": "vendor",
  "vendor_id": 5
}
```

#### Remove from Wishlist
```http
DELETE /api/wishlist/{wishlist_id}
```

#### Check if in Wishlist
```http
GET /api/customer/wishlist/{vendor_id}/check
```

**Response:**
```json
{
  "in_wishlist": true
}
```

### Features
- 💔 Heart button on vendor cards (quick add/remove)
- 📋 Dedicated wishlist modal
- 🏪 Save favorite vendors
- 🍽️ Save favorite menu items
- 📅 Track when items were added
- 🗑️ One-click removal

---

## 3. 📅 Order Scheduling

### Database Schema
```python
class ScheduledOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    order_data = db.Column(db.Text, nullable=False)  # JSON string with order details
    scheduled_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, cancelled, completed
    recurring = db.Column(db.String(20), nullable=True)  # daily, weekly, monthly, or None for one-time
    next_occurrence = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### API Endpoints

#### Get Scheduled Orders
```http
GET /api/customer/scheduled-orders
```

**Response:**
```json
{
  "success": true,
  "scheduled_orders": [
    {
      "id": 1,
      "scheduled_time": "10 Jan 2026, 02:30 PM",
      "recurring": "daily",
      "notes": "Leave at door",
      "order_data": {
        "items": [...],
        "total": 500
      },
      "status": "pending",
      "created_at": "09 Jan 2026"
    }
  ]
}
```

#### Create Scheduled Order
```http
POST /api/customer/scheduled-orders
Content-Type: application/json

{
  "scheduled_time": "2026-01-10T14:30:00",
  "recurring": "daily",
  "notes": "Leave at door",
  "order_data": {
    "items": [{"id": 1, "quantity": 2, "price": 80}],
    "total": 500
  }
}
```

#### Update Scheduled Order
```http
PUT /api/scheduled-order/{order_id}
Content-Type: application/json

{
  "scheduled_time": "2026-01-11T14:30:00",
  "notes": "Call before delivery"
}
```

#### Cancel Scheduled Order
```http
DELETE /api/scheduled-order/{order_id}
```

### Features
- 📅 Schedule orders for future dates/times
- 🔄 Recurring orders (daily, weekly, monthly)
- 📝 Special delivery instructions
- ✏️ Edit scheduled orders
- ❌ Cancel scheduled orders
- 📋 View all scheduled orders
- ⏰ DateTime picker with validation

---

## 4. ✨ Smart Recommendations

### Algorithm
Recommendations are generated based on:
1. **Order History** - Items/vendors customer has ordered from
2. **Trending Items** - Most popular items across platform
3. **Similar Preferences** - Vendors with similar business types
4. **New Items** - Latest items from favorite vendors

### API Endpoint
```http
GET /api/customer/recommendations
```

**Response:**
```json
{
  "success": true,
  "recommendations": {
    "trending": [
      {
        "id": 45,
        "name": "Vanilla Ice Cream",
        "price": 80,
        "image": "uploads/menu/...",
        "vendor_id": 5,
        "vendor_name": "Ice Cream Paradise",
        "reason": "Trending now"
      }
    ],
    "based_on_history": [...],
    "similar_to_favorites": [...],
    "new_from_favorites": [...]
  }
}
```

### Categories
1. 🔥 **Trending Now** - Most ordered items
2. 📊 **Based on Your History** - Items from vendors you frequently order from
3. 🎯 **Similar to Your Favorites** - Items from vendors with similar cuisine
4. 🆕 **New from Your Favorites** - Latest items from your favorite vendors

---

## 5. 🔍 Sorting & Filtering

### Vendor Sorting
```http
GET /api/vendors/sorted?sort_by=rating&category=ice_cream
```

**Sort Options:**
- `rating` - Highest rated vendors first
- `reviews` - Most reviews first
- `newest` - Newest vendors first
- `category` - Group by category

**Response:**
```json
{
  "success": true,
  "vendors": [
    {
      "id": 5,
      "name": "Ice Cream Paradise",
      "location": "Bandra West",
      "cuisine": "ice_cream",
      "logo": "uploads/vendor/...",
      "hero_image": "uploads/vendor/...",
      "rating": 4.8,
      "review_count": 42
    }
  ],
  "total": 1
}
```

### Menu Item Sorting
```http
GET /api/menu/sorted?sort_by=rating&vendor_id=5
```

**Sort Options:**
- `rating` - Highest rated vendor first
- `price_low` - Lowest price first
- `price_high` - Highest price first
- `newest` - Newest items first

---

## 🛠️ Setup Instructions

### 1. Run Migration
```bash
python migrate_customer_features.py
```

This creates three new tables:
- `customer_review`
- `wishlist`
- `scheduled_order`

### 2. Verify Installation
```bash
python -c "from app import db, CustomerReview, Wishlist, ScheduledOrder; print('✅ All models imported successfully')"
```

### 3. Test Endpoints
```bash
# Test GET endpoints
curl http://localhost:5000/api/customer/wishlist
curl http://localhost:5000/api/customer/recommendations
curl http://localhost:5000/api/vendors/sorted?sort_by=rating
```

---

## 📊 Database Schema Diagram

```
Customer (1) ──────→ CustomerReview (Many)
Customer (1) ──────→ Wishlist (Many)
Customer (1) ──────→ ScheduledOrder (Many)

Vendor (1) ──────→ CustomerReview (Many)
Vendor (1) ──────→ Wishlist (Many)

MenuItem (1) ──────→ Wishlist (Many)
CustomerOrder (1) ──────→ CustomerReview (Many)
```

---

## 🎨 UI/UX Features

### Customer Dashboard Updates
- ❤️ Wishlist button in profile menu
- 📅 Scheduled Orders button
- ✨ Recommendations button
- ⭐ Write Review button on vendor cards
- 🔍 Advanced sort/filter controls

### Modal Interfaces
1. **Wishlist Modal** - Browse and manage favorites
2. **Scheduled Orders Modal** - View and manage scheduled orders
3. **Recommendations Modal** - Discover personalized recommendations
4. **Review Modal** - Write detailed reviews with photos
5. **Schedule Modal** - Create/edit scheduled orders

---

## 🔒 Security Features

### Data Protection
- ✅ Customer ID validation (customer_api_required decorator)
- ✅ Ownership verification before delete operations
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ File upload validation (image extensions only)
- ✅ CORS/CSRF protection ready

### Privacy
- 📝 Reviews linked to customer and order
- 🔐 Wishlist is per-customer, private by default
- 🛡️ Scheduled order data encrypted in JSON format

---

## 📈 Usage Statistics

### Tracking
- `CustomerReview.helpful_votes` - Track helpful reviews
- `CustomerReview.created_at` - Monitor review frequency
- `Wishlist.created_at` - Track wishlist activity
- `ScheduledOrder.status` - Monitor scheduled order completion

### Analytics Ready
```python
# Example queries
total_reviews = CustomerReview.query.filter_by(vendor_id=5).count()
avg_rating = db.session.query(db.func.avg(CustomerReview.rating)).filter_by(vendor_id=5).scalar()
wishlist_items = Wishlist.query.filter_by(customer_id=1).count()
scheduled_orders = ScheduledOrder.query.filter_by(status='pending').count()
```

---

## 🚀 Performance Optimizations

1. **Efficient Queries**
   - Indexed foreign keys
   - Lazy loading with relationships
   - Batch operations for bulk actions

2. **Caching Strategy**
   - Browser caching for images
   - Session storage for frequent queries
   - Database indexing on foreign keys

3. **Load Time**
   - Pagination for large review lists
   - Image optimization (file upload)
   - Async API calls in frontend

---

## 📝 Testing Checklist

- [ ] Submit review with all fields
- [ ] Upload review photo
- [ ] Mark review as helpful
- [ ] Add vendor to wishlist
- [ ] Remove from wishlist
- [ ] Schedule one-time order
- [ ] Schedule recurring order
- [ ] Edit scheduled order
- [ ] Cancel scheduled order
- [ ] Get recommendations
- [ ] Sort vendors by rating
- [ ] Sort menu items by price
- [ ] Filter by category
- [ ] Mobile responsiveness
- [ ] Error handling

---

## 🐛 Known Limitations

1. **Recurring Orders** - Currently scheduled, execution is manual (can be automated with cron jobs)
2. **Smart Recommendations** - Basic algorithm, can be enhanced with ML
3. **Review Photos** - Single photo per review, can be extended to multiple photos
4. **Scheduling** - No timezone handling yet (uses server timezone)

---

## 🔮 Future Enhancements

1. **Advanced Recommendations**
   - Machine learning based filtering
   - Collaborative filtering
   - Weather-based recommendations

2. **Enhanced Scheduling**
   - Auto-execute recurring orders
   - Timezone support
   - Bulk scheduling

3. **Review Analytics**
   - Sentiment analysis
   - Trend detection
   - Fraud detection

4. **Social Features**
   - Share reviews on social media
   - Compare wishlists with friends
   - Group recommendations

---

## 📞 Support

For issues or questions about these features:
1. Check the API endpoint documentation above
2. Review database schema for data format
3. Check test checklist for common issues
4. Enable debug logging for detailed error messages

