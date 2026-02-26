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
        
        Log.i(TAG, "JARVIS AI v17.0 started");
        
        // Enable WebView debugging
        try {
            WebView.setWebContentsDebuggingEnabled(true);
        } catch (Exception e) {
            Log.w(TAG, "WebView debug init failed: " + e.getMessage());
        }
        
        // WebView Performance Optimizations - null-safe
        try {
            if (getBridge() != null && getBridge().getWebView() != null) {
                WebView webView = getBridge().getWebView();
                WebSettings ws = webView.getSettings();
                
                webView.setLayerType(View.LAYER_TYPE_HARDWARE, null);
                ws.setDomStorageEnabled(true);
                ws.setDatabaseEnabled(true);
                ws.setCacheMode(WebSettings.LOAD_DEFAULT);
                ws.setAllowFileAccess(true);
                ws.setJavaScriptEnabled(true);
                ws.setJavaScriptCanOpenWindowsAutomatically(true);
                ws.setLoadWithOverviewMode(true);
                ws.setUseWideViewPort(true);
                ws.setBlockNetworkImage(false);
                ws.setLoadsImagesAutomatically(true);
                ws.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
                
                Log.i(TAG, "WebView optimizations applied");
            }
        } catch (Exception e) {
            Log.w(TAG, "WebView optimization failed: " + e.getMessage());
        }
        
        // Register native plugins safely - catches both Exception AND Error
        safeRegisterPlugin(com.jarvis.trading.plugins.DeviceCommandsPlugin.class, "DeviceCommands");
        safeRegisterPlugin(com.jarvis.trading.plugins.LocalTTSPlugin.class, "LocalTTS");
        safeRegisterPlugin(com.jarvis.trading.plugins.LocalLLMPlugin.class, "LocalLLM");
        safeRegisterPlugin(com.jarvis.trading.plugins.VoskSTTPlugin.class, "VoskSTT");
        safeRegisterPlugin(com.jarvis.trading.plugins.PersonalAssistantPlugin.class, "PersonalAssistant");
        
        // Start service AFTER delay to let app fully initialize
        try {
            if (getBridge() != null && getBridge().getWebView() != null) {
                getBridge().getWebView().postDelayed(this::startJarvisService, 3000);
            }
        } catch (Exception e) {
            Log.w(TAG, "Delayed service start setup failed: " + e.getMessage());
        }
    }
    
    @SuppressWarnings("unchecked")
    private void safeRegisterPlugin(Class<?> pluginClass, String name) {
        try {
            registerPlugin((Class<? extends com.getcapacitor.Plugin>) pluginClass);
            Log.i(TAG, name + " plugin registered");
        } catch (Exception e) {
            Log.w(TAG, name + " plugin skipped: " + e.getMessage());
        } catch (Error e) {
            Log.w(TAG, name + " plugin error: " + e.getMessage());
        }
    }
    
    private void startJarvisService() {
        try {
            Intent serviceIntent = new Intent(this, JarvisService.class);
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                startForegroundService(serviceIntent);
            } else {
                startService(serviceIntent);
            }
            Log.i(TAG, "JARVIS Service started");
        } catch (Exception e) {
            Log.w(TAG, "JARVIS Service start failed: " + e.getMessage());
        }
    }
}
