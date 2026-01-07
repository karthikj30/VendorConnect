# Google Maps Integration Setup Guide

## Overview
VendorConnect now supports real-time delivery tracking with Google Maps integration. Delivery agents can share their live GPS location, and customers can see their delivery partner on a live map.

## Features
- **Live Delivery Tracking**: See delivery agent location in real-time on Google Maps
- **Delivery Agent Integration**: Delivery agents update their GPS coordinates continuously
- **Multiple Database Support**: Works with MySQL, SQLite, and PostgreSQL
- **Fallback Support**: If Maps API key is not configured, shows GPS coordinates fallback

## Getting Your Google Maps API Key

### Step 1: Create a Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use existing one)
3. Enable the following APIs:
   - **Maps JavaScript API** - For rendering maps
   - **Directions API** - For route optimization (optional)
   - **Geocoding API** - For address lookup (optional)

### Step 2: Create API Key
1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **API Key**
3. Copy your API key

### Step 3: Restrict API Key (Recommended for Production)
1. Click on your API key to edit
2. Under **API restrictions**, select:
   - Maps JavaScript API
   - Directions API (if using)
   - Geocoding API (if using)
3. Under **Application restrictions**, select:
   - **HTTP referrers**
   - Add your domain: `*.yourdomain.com` and `yourdomain.com`
4. Save changes

## Configuration Methods

### Method 1: Environment Variables (Recommended)

#### Development (Linux/Mac)
```bash
export GOOGLE_MAPS_API_KEY="your-api-key-here"
python app.py
```

#### Production (Render.com)
1. Go to your Render deployment
2. Go to **Environment** tab
3. Add new environment variable:
   - Key: `GOOGLE_MAPS_API_KEY`
   - Value: Your API key
4. Deploy

#### Production (.env file)
Create a `.env` file in `/workspaces/VendorConnect/VendorConnect-main/`:
```
GOOGLE_MAPS_API_KEY=your-api-key-here
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
```

Then load it in your deployment:
```python
from dotenv import load_dotenv
load_dotenv()
```

### Method 2: Hardcode (Development Only)
In `app.py` line 205:
```python
app.config['GOOGLE_MAPS_API_KEY'] = 'your-api-key-here'
```

## API Endpoints

### Get Maps Configuration
**Endpoint**: `GET /api/config/maps`

**Response**:
```json
{
  "success": true,
  "googleMapsApiKey": "AIzaSyBFw0Qbyq9zTFTd-tUY6dZWTgaQzuU17R8"
}
```

### Update Delivery Location
**Endpoint**: `POST /api/delivery/location/update`

**Request Body**:
```json
{
  "order_id": 123,
  "latitude": 12.9716,
  "longitude": 77.5946,
  "delivery_agent_id": 5
}
```

**Response**:
```json
{
  "success": true,
  "message": "Location updated successfully"
}
```

### Get Delivery Tracking
**Endpoint**: `GET /api/delivery/tracking/<order_id>`

**Response**:
```json
{
  "success": true,
  "order": {
    "id": 123,
    "status": "out_for_delivery",
    "estimated_delivery": "2026-01-07T18:30:00"
  },
  "delivery_agent": {
    "id": 5,
    "name": "Raj Kumar",
    "phone": "9876543210",
    "latitude": 12.9716,
    "longitude": 77.5946,
    "vehicle": "Bike - KA01AB1234"
  }
}
```

## Delivery Agent Dashboard

### Features
- **Live GPS Tracking**: Real-time location updates
- **Order Management**: View assigned deliveries
- **Route Optimization**: See optimal delivery route
- **Customer Communication**: Direct contact with customers
- **Delivery Proof**: Upload photos/signatures

### Accessing Delivery Agent Dashboard
1. Register as delivery agent at `/vendor/register` with role: "delivery_agent"
2. Login at `/vendor/login`
3. Access dashboard at `/delivery/dashboard`

## Frontend Integration

### Automatic Map Initialization
The customer dashboard automatically:
1. Fetches API key from `/api/config/maps`
2. Loads Google Maps JavaScript library
3. Initializes map with delivery tracking

### Fallback Support
If Google Maps API key is not configured:
- Map shows "Map Temporarily Unavailable" message
- Delivery tracking still works with GPS coordinates only
- Customer can see delivery agent's location as coordinates

## Troubleshooting

### Map Not Loading
**Issue**: Google Maps shows error or blank space

**Solution**:
1. Check if API key is set: `echo $GOOGLE_MAPS_API_KEY`
2. Verify API key is valid in Google Cloud Console
3. Check browser console for errors (F12 → Console tab)
4. Ensure APIs are enabled: Maps JavaScript API

### "This page can't load Google Maps correctly"
**Issue**: Google Maps authentication failed

**Solution**:
1. Verify API key in `/api/config/maps` endpoint
2. Check API restrictions in Google Cloud Console
3. Ensure HTTP referrer domain is whitelisted
4. Check browser console for specific error message

### Delivery Location Not Updating
**Issue**: Delivery agent location not showing on map

**Solution**:
1. Verify delivery agent has permission to update location
2. Check network requests in browser DevTools
3. Ensure order is assigned to delivery agent
4. Check `/api/delivery/tracking/<order_id>` for agent info

## Cost Considerations

Google Maps API is **FREE** for basic usage with usage limits:
- Maps JavaScript API: $7 per 1,000 requests (first 28,000 monthly free)
- Directions API: $0.50 per 100 requests (first 25,000 monthly free)
- Geocoding API: $0.50 per 100 requests (first 40,000 monthly free)

**To minimize costs**:
1. Use caching for frequently requested routes
2. Batch geocoding requests
3. Set API key restrictions to your domain only
4. Monitor usage in Google Cloud Console

## Security Best Practices

1. **Never commit API key** to Git (use .env or environment variables)
2. **Restrict API key** to HTTP referrers and specific APIs
3. **Set quotas** in Google Cloud Console to prevent misuse
4. **Monitor usage** regularly in Cloud Console
5. **Rotate keys** periodically for security

## Files Modified

- `app.py` (lines 205, 3874-3887): Added GOOGLE_MAPS_API_KEY config and API endpoint
 - `customer_dashboard.html` (lines 20, 26-50): Dynamic Maps API loading

## Testing

### Local Testing
```bash
# Set API key
export GOOGLE_MAPS_API_KEY="your-api-key"

# Run app
python app.py

# Test config endpoint
curl http://localhost:5000/api/config/maps

# Check customer dashboard
# Navigate to http://localhost:5000/customer/dashboard
# Should see map initialization in browser console
```

## Support

For issues or questions:
1. Check Google Cloud Console for API key validity
2. Review browser console (F12) for errors
3. Check server logs in terminal
4. Verify database connectivity for delivery tracking

---

**Last Updated**: January 7, 2026
**Version**: 1.0
