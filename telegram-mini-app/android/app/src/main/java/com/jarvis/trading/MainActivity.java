package com.jarvis.trading;

import android.content.Intent;
import android.os.Build;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.webkit.WebSettings;
import android.webkit.WebView;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    private static final String TAG = "JARVIS";
    
    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        Log.i(TAG, "🚀 JARVIS AI v16.0 — Iron Man OS Edition started");
        
        // Start JARVIS Always-On Service
        startJarvisService();
        
        // Enable WebView debugging for troubleshooting
        WebView.setWebContentsDebuggingEnabled(true);
        
        // ═══════════════════════════════════════════
        //  WebView Performance Optimizations
        // ═══════════════════════════════════════════
        try {
            WebView webView = getBridge().getWebView();
            WebSettings ws = webView.getSettings();
            
            // Hardware acceleration
            webView.setLayerType(View.LAYER_TYPE_HARDWARE, null);
            
            // Enable DOM storage & caching for faster loads
            ws.setDomStorageEnabled(true);
            ws.setDatabaseEnabled(true);
            ws.setCacheMode(WebSettings.LOAD_DEFAULT);
            ws.setAllowFileAccess(true);
            
            // JavaScript performance
            ws.setJavaScriptEnabled(true);
            ws.setJavaScriptCanOpenWindowsAutomatically(true);
            
            // Rendering performance
            ws.setRenderPriority(WebSettings.RenderPriority.HIGH);
            ws.setEnableSmoothTransition(true);
            ws.setLoadWithOverviewMode(true);
            ws.setUseWideViewPort(true);
            
            // Disable slow features
            ws.setBlockNetworkImage(false);
            ws.setLoadsImagesAutomatically(true);
            ws.setGeolocationEnabled(false);
            
            // Mixed content for API calls
            ws.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
            
            Log.i(TAG, "✅ WebView performance optimizations applied");
        } catch (Exception e) {
            Log.w(TAG, "⚠️ WebView optimization failed: " + e.getMessage());
        }
        
        // Try to register native plugins safely (won't crash if they fail)
        try {
            registerPlugin(com.jarvis.trading.plugins.DeviceCommandsPlugin.class);
            Log.i(TAG, "✅ DeviceCommands plugin registered");
        } catch (Exception e) {
            Log.w(TAG, "⚠️ DeviceCommands plugin skipped: " + e.getMessage());
        }
        
        try {
            registerPlugin(com.jarvis.trading.plugins.LocalTTSPlugin.class);
            Log.i(TAG, "✅ LocalTTS plugin registered");
        } catch (Exception e) {
            Log.w(TAG, "⚠️ LocalTTS plugin skipped: " + e.getMessage());
        }
        
        // These plugins need external libs — safe-register
        try {
            registerPlugin(com.jarvis.trading.plugins.LocalLLMPlugin.class);
            Log.i(TAG, "✅ LocalLLM plugin registered");
        } catch (Exception e) {
            Log.w(TAG, "⚠️ LocalLLM plugin skipped: " + e.getMessage());
        }
        
        try {
            registerPlugin(com.jarvis.trading.plugins.VoskSTTPlugin.class);
            Log.i(TAG, "✅ VoskSTT plugin registered");
        } catch (Exception e) {
            Log.w(TAG, "⚠️ VoskSTT plugin skipped: " + e.getMessage());
        }
        
        try {
            registerPlugin(com.jarvis.trading.plugins.PersonalAssistantPlugin.class);
            Log.i(TAG, "✅ PersonalAssistant plugin registered");
        } catch (Exception e) {
            Log.w(TAG, "⚠️ PersonalAssistant plugin skipped: " + e.getMessage());
        }
        
        // Start JARVIS always-on background service
        startJarvisService();
    }
    
    /**
     * Start the JARVIS always-on foreground service
     */
    private void startJarvisService() {
        try {
            Intent serviceIntent = new Intent(this, JarvisService.class);
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                startForegroundService(serviceIntent);
            } else {
                startService(serviceIntent);
            }
            Log.i(TAG, "✅ JARVIS Service started — always-on mode ACTIVE");
        } catch (Exception e) {
            Log.w(TAG, "⚠️ JARVIS Service start failed: " + e.getMessage());
        }
    }
}
