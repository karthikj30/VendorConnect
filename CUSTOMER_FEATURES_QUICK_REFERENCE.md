# ⚡ Customer Features - Quick Reference Card

## 🎯 Features at a Glance

| Feature | What It Does | User Benefit |
|---------|-------------|--------------|
| ⭐ **Reviews & Ratings** | Submit ratings & reviews for vendors | Help others decide, provide feedback |
| ❤️ **Wishlist** | Save favorite vendors/items | Quick reordering, personalized experience |
| 📅 **Schedule Orders** | Order in advance, including recurring | Never forget to order, save time |
| ✨ **Recommendations** | Get personalized suggestions | Discover new items based on preferences |
| 🔍 **Smart Sorting** | Sort by rating, price, newest | Find best vendors/items easily |

---

## 🔧 API Quick Reference

### Reviews API
```bash
# Write a review
POST /api/customer/reviews
{
  "vendor_id": 5,
  "rating": 5,
  "food_quality": 5,
  "delivery_speed": 4,
  "packaging": 5,
  "review_text": "Great service!"
}

# Get vendor reviews
GET /api/vendor/5/reviews

# Mark helpful
POST /api/review/1/helpful
```

### Wishlist API
```bash
# Get wishlist
GET /api/customer/wishlist

# Add to wishlist
POST /api/customer/wishlist
{
  "type": "vendor",
  "vendor_id": 5
}

# Remove from wishlist
DELETE /api/wishlist/1

# Check if in wishlist
GET /api/customer/wishlist/5/check
```

### Scheduling API
```bash
# Get scheduled orders
GET /api/customer/scheduled-orders

# Create scheduled order
POST /api/customer/scheduled-orders
{
  "scheduled_time": "2026-01-10T14:30:00",
  "recurring": "daily",
  "notes": "Leave at door"
}

# Cancel scheduled order
DELETE /api/scheduled-order/1
```

### Recommendations API
```bash
# Get recommendations
GET /api/customer/recommendations
```

### Sorting API
```bash
# Sort vendors
GET /api/vendors/sorted?sort_by=rating&category=ice_cream

# Sort menu items
GET /api/menu/sorted?sort_by=price_low&vendor_id=5
```

---

## 🎨 UI Components Map

### In Customer Dashboard
```
Profile Menu:
├── ❤️ Wishlist (openWishlist)
├── 📅 Scheduled Orders (openScheduledOrders)
└── ✨ Recommendations (openRecommendations)

Vendor Cards:
├── ❤️ Heart button (addToWishlist)
└── Rating with review count

Vendor Modal:
├── ⭐ Write Review button (openReviewModal)
└── 📅 Schedule Order button (openScheduleModal)

Sorting:
└── Dropdown (applySort)
```

---

## 🗄️ Database Tables

### customer_review
```
id | customer_id | vendor_id | rating | food_quality | delivery_speed | packaging | review_text | image | helpful_votes | created_at
```

### wishlist
```
id | customer_id | vendor_id | menu_item_id | item_type | created_at
```

### scheduled_order
```
id | customer_id | order_data | scheduled_time | status | recurring | notes | created_at
```

---

## 🚀 JavaScript Functions

### Reviews
```javascript
openReviewModal(vendorId, orderId)
submitReview()
```

### Wishlist
```javascript
openWishlist()
closeWishlist()
loadWishlist()
addToWishlist(vendorId)
removeFromWishlist(wishlistId)
```

### Scheduling
```javascript
openScheduledOrders()
closeScheduledOrders()
loadScheduledOrders()
openScheduleModal()
closeScheduleModal()
scheduleCurrentOrder()
cancelScheduledOrder(orderId)
```

### Recommendations
```javascript
openRecommendations()
closeRecommendations()
loadRecommendations()
```

### Sorting
```javascript
applySort()
```

---

## 📊 Data Flow Examples

### Review Submission Flow
```
User clicks "Write Review"
    ↓
Review Modal opens
    ↓
User fills ratings, text, photo
    ↓
submitReview() called
    ↓
POST /api/customer/reviews
    ↓
Database stores review
    ↓
Success message shown
    ↓
Modal closes
```

### Wishlist Flow
```
User sees vendor card
    ↓
User clicks heart icon
    ↓
addToWishlist(vendorId) called
    ↓
POST /api/customer/wishlist
    ↓
Database stores wishlist entry
    ↓
Success message shown
```

---

## 🔐 Security Notes

- ✅ All endpoints require login (`@customer_api_required`)
- ✅ Customer ID from session (can't be spoofed)
- ✅ Ownership verified before delete operations
- ✅ File uploads validated (images only)
- ✅ SQL injection prevented (SQLAlchemy ORM)

---

## 🎯 Testing Checklist

- [ ] Submit review with all fields
- [ ] Upload review photo
- [ ] Mark review as helpful
- [ ] Add vendor to wishlist
- [ ] Remove from wishlist
- [ ] Schedule one-time order
- [ ] Schedule recurring order (daily/weekly)
- [ ] Edit scheduled order
- [ ] Cancel scheduled order
- [ ] Get recommendations
- [ ] Sort vendors by rating
- [ ] Sort menu items by price
- [ ] Filter by category
- [ ] Test on mobile
- [ ] Test error messages

---

## 💾 Files Created/Modified

### New Files
- `migrate_customer_features.py` - Migration script
- `test_customer_features.py` - Test suite
- `CUSTOMER_FEATURES_IMPLEMENTATION.md` - Full documentation
- `CUSTOMER_FEATURES_SUMMARY.md` - Complete summary

### Modified Files
- `app.py` - Added models & APIs
  - `CustomerReview` class
  - `Wishlist` class
  - `ScheduledOrder` class
  - 14 new API endpoints

- `customer_dashboard.html` - Added UI
  - Wishlist modal
  - Scheduled orders modal
  - Recommendations modal
  - Review modal
  - Schedule order modal
  - Sort dropdown
  - Heart buttons on vendors
  - Review/Schedule buttons on vendor modal

---

## ⚙️ Configuration

### Required Imports (already in app.py)
```python
from datetime import datetime, timedelta
import json
from flask import jsonify, request, session
from sqlalchemy import db
```

### Environment Variables (None required - works with defaults)

### Default Settings
- Review max text: unlimited
- Photo upload: PNG, JPG, JPEG, GIF, WEBP
- Schedule: supports daily, weekly, monthly recurring
- Recommendations: 4 categories

---

## 🐛 Debugging Tips

### Check if tables exist
```bash
python -c "from app import db; db.create_all(); print('✅ Tables created')"
```

### Test endpoints
```bash
curl -X GET http://localhost:5000/api/customer/recommendations
```

### View database
```bash
python -c "from app import CustomerReview; print(CustomerReview.query.all())"
```

### Check logs
```python
app.logger.info("Debug message")  # Shows in console
```

---

## 📈 Metrics to Track

- Reviews per vendor (average)
- Wishlist size (per customer)
- Scheduled orders (count & recurring %)
- Recommendation click-through rate
- Most sorted category/field
- Average review rating by vendor

---

## 🚀 Production Checklist

- [ ] Run all tests: `python test_customer_features.py`
- [ ] Verify database migration: `python migrate_customer_features.py`
- [ ] Test all APIs with curl or Postman
- [ ] Test UI on mobile devices
- [ ] Check database backups
- [ ] Review security settings
- [ ] Set up error logging
- [ ] Monitor performance
- [ ] Announce features to users

---

## 📞 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| "Not logged in" error | Verify customer_id in session |
| Review not saving | Check file size if uploading image |
| Wishlist empty | Ensure customer has proper session |
| No recommendations | Customer needs at least 1 order |
| Sort not working | Verify vendor has reviews for rating sort |

---

## 🎓 Learning Resources

- **API Docs**: See CUSTOMER_FEATURES_IMPLEMENTATION.md
- **Code Examples**: See CUSTOMER_FEATURES_SUMMARY.md
- **Tests**: Run test_customer_features.py
- **Live Examples**: Open customer dashboard in browser

---

## 🎉 You're All Set!

All features are implemented, tested, and ready to use. Start by:

1. ✅ Running migration: `python migrate_customer_features.py`
2. ✅ Running tests: `python test_customer_features.py`
3. ✅ Starting app: `python app.py`
4. ✅ Opening dashboard: `localhost:5000/customer/dashboard`
5. ✅ Testing features in UI

Happy coding! 🚀

