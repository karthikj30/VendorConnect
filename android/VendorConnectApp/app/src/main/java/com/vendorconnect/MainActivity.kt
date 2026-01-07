package com.vendorconnect

import android.Manifest
import android.annotation.SuppressLint
import android.content.pm.PackageManager
import android.os.Bundle
import android.webkit.CookieManager
import android.webkit.GeolocationPermissions
import android.webkit.WebChromeClient
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.activity.OnBackPressedCallback
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private var geoCallback: GeolocationPermissions.Callback? = null
    private var geoOrigin: String? = null

    private val locationPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val granted = (permissions[Manifest.permission.ACCESS_FINE_LOCATION] == true
                || permissions[Manifest.permission.ACCESS_COARSE_LOCATION] == true)
        geoCallback?.invoke(geoOrigin, granted, true)
        geoCallback = null
        geoOrigin = null
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        webView = findViewById(R.id.webView)

        val webSettings: WebSettings = webView.settings
        webSettings.javaScriptEnabled = true
        webSettings.domStorageEnabled = true
        webSettings.databaseEnabled = true
        webSettings.loadsImagesAutomatically = true
        webSettings.javaScriptCanOpenWindowsAutomatically = false
        webSettings.setSupportZoom(false)
        
        // Mobile optimizations
        webSettings.useWideViewPort = true
        webSettings.loadWithOverviewMode = true
        webSettings.builtInZoomControls = false
        webSettings.defaultTextEncodingName = "utf-8"
        webSettings.mixedContentMode = android.webkit.WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
        
        // Performance optimizations
        webSettings.blockNetworkImage = false
        webSettings.blockNetworkLoads = false
        webSettings.cacheMode = android.webkit.WebSettings.LOAD_DEFAULT
        
        // Viewport meta tag support
        webSettings.setSupportZoom(false)
        webSettings.layoutAlgorithm = android.webkit.WebSettings.LayoutAlgorithm.SINGLE_COLUMN

        CookieManager.getInstance().setAcceptCookie(true)
        CookieManager.getInstance().setAcceptThirdPartyCookies(webView, true)

        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView?, url: String?): Boolean {
                return false // Load within the WebView
            }
        }

        webView.webChromeClient = object : WebChromeClient() {
            override fun onGeolocationPermissionsShowPrompt(origin: String?, callback: GeolocationPermissions.Callback?) {
                // Ask for runtime location permissions, then respond
                geoCallback = callback
                geoOrigin = origin
                ensureLocationPermissions()
            }
        }

        // Handle back button using new API
        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (webView.canGoBack()) {
                    webView.goBack()
                } else {
                    isEnabled = false
                    onBackPressedDispatcher.onBackPressed()
                }
            }
        })

        val baseUrl = intent.getStringExtra("BASE_URL") ?: getString(R.string.app_base_url)
        webView.loadUrl(baseUrl)
    }

    private fun ensureLocationPermissions() {
        val fineGranted = ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
        val coarseGranted = ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED
        if (fineGranted || coarseGranted) {
            geoCallback?.invoke(geoOrigin, true, true)
            geoCallback = null
            geoOrigin = null
        } else {
            locationPermissionLauncher.launch(arrayOf(
                Manifest.permission.ACCESS_FINE_LOCATION,
                Manifest.permission.ACCESS_COARSE_LOCATION
            ))
        }
    }
}

// Pairing instructions for adb
// $HOME/android-sdk/platform-tools/adb pair <pairing_host:pairing_port>
// # When prompted, enter the 6-digit pairing code
