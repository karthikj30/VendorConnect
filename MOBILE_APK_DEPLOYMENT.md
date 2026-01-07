# VendorConnect Android APK - Deployment & Installation Guide

## Overview
This guide covers how to download and install the VendorConnect APK on Android devices and emulators.

---

## 1. Download the APK

### From GitHub Actions (Automated Builds)
1. Go to your GitHub repository: `https://github.com/karthikj30/VendorConnect`
2. Click **Actions** tab
3. Select the latest **"Build Android APK"** workflow run
4. Scroll down to **Artifacts** section
5. Download **app-debug.apk**

### From GitHub Releases (Tagged Versions)
1. Go to **Releases** section in your repository
2. Find your version tag (e.g., `v1.0.0`)
3. Download the APK from the release assets

---

## 2. Install on Physical Android Device

### Prerequisites
- Android phone/tablet with **Android 5.0+** (API 21+)
- USB cable
- Android Debug Bridge (ADB) installed on your computer

### Method A: Using ADB (Recommended for Development)

**Step 1: Enable Developer Mode on Device**
1. Open **Settings** → **About Phone**
2. Tap **Build Number** 7 times until "Developer Mode Enabled" message appears
3. Go back to Settings → **Developer Options** → Enable **USB Debugging**

**Step 2: Connect Device via USB**
```bash
# Connect phone via USB cable
# Allow USB debugging when prompted on phone

# Verify device is connected
adb devices
# Output should show your device: "XXXXX    device"
```

**Step 3: Install APK**
```bash
adb install -r app-debug.apk
# -r flag reinstalls if already installed
```

**Step 4: Launch App**
```bash
adb shell am start -n com.vendorconnect/.MainActivity
```

### Method B: Direct Download on Device
1. Download APK file on your phone (via email, Google Drive, etc.)
2. Open file manager → Navigate to **Downloads**
3. Tap the **app-debug.apk** file
4. Tap **Install**
5. Allow permissions if prompted
6. Tap **Open** when installation completes

### Method C: Email/Cloud Transfer
1. Download APK from GitHub Actions
2. Email or upload to Google Drive
3. Open link on Android device
4. Download and install

---

## 3. Install on Android Emulator

### Prerequisites
- Android Studio installed
- Android Emulator configured and running

### Step 1: Start Emulator
```bash
# List available emulators
emulator -list-avds

# Start emulator (replace "Pixel_4_API_30" with your emulator name)
emulator -avd Pixel_4_API_30
```

### Step 2: Install APK
```bash
# Wait for emulator to fully boot (check "adb devices")
adb install -r app-debug.apk
```

### Step 3: Launch App
```bash
adb shell am start -n com.vendorconnect/.MainActivity
```

---

## 4. Configure Base URL Before Installation

The APK connects to your VendorConnect backend server. Configure it before installing:

### Option A: Edit in Source Code (Before Building)
Edit `android/VendorConnectApp/app/src/main/res/values/strings.xml`:
```xml
<string name="app_base_url">http://your-server-domain:5000/customer/dashboard</string>
```

For **production**, use HTTPS:
```xml
<string name="app_base_url">https://your-domain.com/customer/dashboard</string>
```

### Option B: Override URL via ADB (After Installing)
```bash
adb shell am start -n com.vendorconnect/.MainActivity \
  --es BASE_URL "https://your-server.com/customer/dashboard"
```

### Option C: For Local Development
- **Android Emulator**: `http://10.0.2.2:5000/customer/dashboard`
- **Physical Device (same network)**: `http://192.168.x.x:5000/customer/dashboard`

---

## 5. Uninstall APK

### From Device Settings
1. **Settings** → **Apps** → **VendorConnect**
2. Tap **Uninstall**

### Via ADB
```bash
adb uninstall com.vendorconnect
```

---

## 6. Troubleshooting

### APK Installation Fails
```bash
# Clear cache and reinstall
adb uninstall com.vendorconnect
adb install -r app-debug.apk
```

### App Shows Blank Page
- Verify base URL is correct and server is running
- Check network connectivity on device
- Use Chrome DevTools: Right-click in app → **Inspect** (if WebView debugging enabled)

### Geolocation/Google Maps Not Working
1. Enable location services on device
2. Grant location permission to VendorConnect app:
   - **Settings** → **Apps** → **VendorConnect** → **Permissions** → **Location** → **Allow**
3. Verify Google Maps API key is configured in web app

### ADB Device Not Found
```bash
# Reconnect USB cable
# Restart ADB daemon
adb kill-server
adb start-server
adb devices
```

### "Unknown sources" Error
1. Go to **Settings** → **Security**
2. Enable **Unknown Sources** or **Install Unknown Apps**
3. Retry installation

---

## 7. Testing Checklist

After installation, verify:
- [ ] App launches without errors
- [ ] Dashboard loads with data
- [ ] Google Maps displays (if using delivery tracking)
- [ ] Chatbot functionality works
- [ ] Location permission prompt appears
- [ ] Network requests reach your server

---

## 8. Distribution Options

### For Beta Testing
- Use internal testing via **Google Play Console**
- Share APK directly via links (GitHub Releases)
- Use Firebase App Distribution

### For Production Release
1. **Sign APK** with your release keystore
2. Upload to **Google Play Store**
3. Set version code and release notes
4. Roll out gradually (5% → 25% → 100%)

---

## 9. CI/CD Pipeline Status

Your GitHub Actions workflow automatically builds APKs on:
- Every push to `main` or `develop` branches
- Every pull request modifying `android/` folder
- Manual trigger via **Run workflow** button

Check build status: **Actions** → **Build Android APK** → Latest run
