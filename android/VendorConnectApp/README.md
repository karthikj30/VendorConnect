adb devices# VendorConnect Android APK (WebView)

This Android app wraps the VendorConnect web app in a secure WebView, enabling mobile users to access the customer dashboard and delivery tracking (including Google Maps).

## Features
- WebView loads the VendorConnect dashboard
- JavaScript, cookies, and DOM storage enabled
- Geolocation permissions integrated for Google Maps
- Network security config allows local development hosts

## Project Structure
- `app/src/main/java/com/vendorconnect/MainActivity.kt`: WebView host with geolocation handling
- `app/src/main/res/layout/activity_main.xml`: Layout with full-screen WebView
- `app/src/main/AndroidManifest.xml`: Permissions and cleartext traffic for dev
- `app/src/main/res/xml/network_security_config.xml`: Allows localhost/10.0.2.2/10.0.1.82
- `app/src/main/res/values/strings.xml`: Default base URL

## Set the Base URL
By default, the app loads:
- `http://10.0.2.2:5000/customer/dashboard` (Android emulator → host machine)

Override via Intent extra (ADB):
```bash
adb shell am start -n com.vendorconnect/.MainActivity --es BASE_URL "http://10.0.1.82:5000/customer/dashboard"
```

For production, update `app_base_url` in `res/values/strings.xml` to your HTTPS domain.

## Build the APK
Import the project in Android Studio (Giraffe or newer), then:
- Build → Build Bundle(s) / APK(s) → Build APK(s)

Or with Gradle (requires Android SDK + Gradle Wrapper):
```bash
./gradlew assembleDebug
```

The output APK will be at:
- `app/build/outputs/apk/debug/app-debug.apk`

## Permissions
- `INTERNET`, `ACCESS_NETWORK_STATE`: to load web content
- `ACCESS_FINE_LOCATION`, `ACCESS_COARSE_LOCATION`: geolocation for maps

## Notes
- For HTTPS production sites, set `android:usesCleartextTraffic="false"` and remove the dev domains in `network_security_config.xml`.
- Ensure your web app’s Google Maps key allows the mobile app’s domain/origin. WebView uses your app’s WebView user agent; referrer restrictions generally don’t apply, but API restrictions must include “Maps JavaScript API”.

## Troubleshooting
- Blank page: verify base URL is reachable from device/emulator
- Map auth overlay: confirm your Google Maps key is valid and billing enabled
- Geolocation prompts do not appear: ensure runtime permissions are granted

## Debugging with ADB
For debugging, use Android Debug Bridge (ADB) commands:
```bash
adb pair <pairing_host:pairing_port>   # enter code
adb connect <device_host:device_port>
adb devices
adb logcat -c
adb logcat | grep -i AndroidRuntime
```

