# YouTube Video Support - Implementation Guide

## Overview
VendorConnect now supports **online YouTube videos** in addition to direct video file uploads for promotions.

## Changes Made

### 1. Vendor Dashboard (`templates/vendor_dashboard.html`)
- **Updated placeholder** to show YouTube URL example
- **Updated helper text** to indicate YouTube links are now supported
- **Before:** `https://example.com/video.mp4`
- **After:** `https://example.com/video.mp4 or https://youtu.be/dQw4w9WgXcQ`

### 2. Customer Dashboard (`templates/customer_dashboard.html`)
Added smart video detection and rendering:

#### New Functions:
- `getYouTubeVideoId(url)` - Extracts video ID from various YouTube URL formats
- `getVideoEmbed(videoUrl, promoId)` - Renders appropriate video player

#### Supported YouTube URL Formats:
✅ `https://www.youtube.com/watch?v=dQw4w9WgXcQ`  
✅ `https://youtu.be/dQw4w9WgXcQ`  
✅ `https://youtube.com/embed/dQw4w9WgXcQ`  
✅ `https://youtube.com/watch?v=dQw4w9WgXcQ&t=10s` (with timestamps)

#### Rendering:
- **YouTube URLs** → Embedded iframe player
- **Direct video URLs** → HTML5 video player (MP4, WebM, etc.)

## How It Works

```javascript
// Automatically detects video type
const youtubeId = getYouTubeVideoId(videoUrl);

if (youtubeId) {
    // Render YouTube iframe
    return `<iframe src="https://www.youtube.com/embed/${youtubeId}"></iframe>`;
} else {
    // Render HTML5 video player
    return `<video controls><source src="${videoUrl}"></video>`;
}
```

## Supported Video Sources

| Type | Format | Support |
|------|--------|---------|
| YouTube | https://youtu.be/VIDEO_ID | ✅ Full |
| YouTube | https://youtube.com/watch?v=VIDEO_ID | ✅ Full |
| Direct Upload | MP4 | ✅ Full |
| Direct Upload | WebM | ✅ Full |
| Direct Upload | Any video format | ✅ Full |

## User Guide

### For Vendors:
1. Go to **Promotions** section
2. Enter promotion details (title, description, price)
3. Paste **either**:
   - A YouTube video URL: `https://youtu.be/dQw4w9WgXcQ`
   - OR a direct video file URL: `https://cdn.example.com/video.mp4`
4. Click **"Launch Campaign"**

### For Customers:
- Videos automatically display in the appropriate player
- No difference in user experience
- Full player controls available (play, pause, volume, fullscreen)

## Benefits

✅ **No video hosting needed** - Use YouTube for free hosting  
✅ **Automatic detection** - App detects video type automatically  
✅ **Better performance** - YouTube CDN handles streaming  
✅ **Wider reach** - YouTube embedded players have better compatibility  
✅ **Easy sharing** - Just copy YouTube URL and paste  

## Technical Details

### YouTube Detection Pattern Matching:
The app uses regex patterns to recognize these URL formats:
- `youtube.com/watch?v=ID`
- `youtu.be/ID`
- `youtube.com/embed/ID`

### Fallback Logic:
If a URL doesn't match YouTube patterns, it's treated as a direct video file URL and rendered with HTML5 `<video>` tag.

### iframe Properties:
YouTube embeds include:
- `allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"`
- `allowfullscreen` - Users can watch in fullscreen
- Responsive sizing - Adapts to container width

## Files Modified
1. [templates/vendor_dashboard.html](templates/vendor_dashboard.html) - Line 1613-1614
2. [templates/customer_dashboard.html](templates/customer_dashboard.html) - Lines 50-70, 131-140

## Testing

### Test with YouTube:
```
https://youtu.be/dQw4w9WgXcQ
```

### Test with Direct Video:
```
https://example.com/promo.mp4
```

Both should display correctly in the customer dashboard!

## Future Enhancements
- Support for Vimeo videos
- Support for Instagram/TikTok embeds
- Custom video thumbnail selection
- Video analytics (view duration, engagement)
