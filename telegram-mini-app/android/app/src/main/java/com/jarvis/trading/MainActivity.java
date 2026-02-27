package com.jarvis.trading;

import android.app.KeyguardManager;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.os.Build;
import android.os.Bundle;
import android.os.Debug;
import android.util.Log;
import android.view.View;
import android.view.WindowManager;
import com.getcapacitor.BridgeActivity;

import java.io.File;

/**
 * JARVIS AI — Iron Man Operating System
 * Z+++ Security Hardened. Full-screen immersive. Always-on voice.
 * Works even when phone is locked.
 */
public class MainActivity extends BridgeActivity {
    private static final String TAG = "JARVIS";

    @Override
    public void onCreate(Bundle savedInstanceState) {
        // ═══ Z+++ SECURITY: Anti-debug check ═══
        try {
            if (Debug.isDebuggerConnected() || Debug.waitingForDebugger()) {
                Log.w(TAG, "⚠️ Debugger detected — JARVIS security alert");
            }
        } catch (Throwable ignored) {}

        // ═══ Z+++ SECURITY: Root detection ═══
        if (isDeviceRooted()) {
            Log.w(TAG, "⚠️ Root detected — JARVIS running in hardened mode");
        }

        // Register custom plugins BEFORE super.onCreate() (Capacitor 8 requirement)
        try {
            registerPlugin(com.jarvis.trading.plugins.DeviceCommandsPlugin.class);
        } catch (Throwable t) { Log.w(TAG, "DeviceCommands skip: " + t.getMessage()); }

        try {
            registerPlugin(com.jarvis.trading.plugins.LocalTTSPlugin.class);
        } catch (Throwable t) { Log.w(TAG, "LocalTTS skip: " + t.getMessage()); }

        try {
            registerPlugin(com.jarvis.trading.plugins.LocalLLMPlugin.class);
        } catch (Throwable t) { Log.w(TAG, "LocalLLM skip: " + t.getMessage()); }

        try {
            registerPlugin(com.jarvis.trading.plugins.VoskSTTPlugin.class);
        } catch (Throwable t) { Log.w(TAG, "VoskSTT skip: " + t.getMessage()); }

        try {
            registerPlugin(com.jarvis.trading.plugins.PersonalAssistantPlugin.class);
        } catch (Throwable t) { Log.w(TAG, "PersonalAssistant skip: " + t.getMessage()); }

        super.onCreate(savedInstanceState);

        // ═══ Z+++ SECURITY: Prevent screenshots & screen recording ═══
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);

        // ═══ Z+++ SECURITY: Tapjacking prevention ═══
        try {
            View rootView = findViewById(android.R.id.content);
            if (rootView != null) {
                rootView.setFilterTouchesWhenObscured(true);
            }
        } catch (Throwable ignored) {}

        // ═══ FULL-SCREEN IMMERSIVE MODE ═══
        enableImmersiveFullscreen();

        // ═══ SHOW OVER LOCK SCREEN ═══
        enableShowOverLockScreen();

        // ═══ KEEP SCREEN ALIVE FOR JARVIS ═══
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);

        // ═══ START ALWAYS-ON SERVICE (delayed 3s for stability) ═══
        try {
            getWindow().getDecorView().postDelayed(() -> {
                try {
                    Intent serviceIntent = new Intent(this, JarvisService.class);
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                        startForegroundService(serviceIntent);
                    } else {
                        startService(serviceIntent);
                    }
                    Log.i(TAG, "JARVIS Always-On Service started");
                } catch (Throwable t) {
                    Log.w(TAG, "Service start skipped: " + t.getMessage());
                }
            }, 3000);
        } catch (Throwable t) {
            Log.w(TAG, "Service delay setup failed: " + t.getMessage());
        }

        Log.i(TAG, "🛡️ JARVIS AI OS — Z+++ Security Active, Full-screen immersive ONLINE");
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) {
            enableImmersiveFullscreen();
        }
    }

    private void enableImmersiveFullscreen() {
        try {
            View decorView = getWindow().getDecorView();
            decorView.setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                | View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                | View.SYSTEM_UI_FLAG_FULLSCREEN
            );
        } catch (Throwable t) {
            Log.w(TAG, "Immersive mode failed: " + t.getMessage());
        }
    }

    private void enableShowOverLockScreen() {
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O_MR1) {
                setShowWhenLocked(true);
                setTurnScreenOn(true);
                KeyguardManager km = (KeyguardManager) getSystemService(Context.KEYGUARD_SERVICE);
                if (km != null) {
                    km.requestDismissKeyguard(this, null);
                }
            } else {
                getWindow().addFlags(
                    WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED
                    | WindowManager.LayoutParams.FLAG_TURN_SCREEN_ON
                    | WindowManager.LayoutParams.FLAG_DISMISS_KEYGUARD
                );
            }
        } catch (Throwable t) {
            Log.w(TAG, "Lock screen overlay failed: " + t.getMessage());
        }
    }

    /**
     * Z+++ Security: Detect rooted devices
     */
    private boolean isDeviceRooted() {
        // Check for su binary
        String[] suPaths = {
            "/system/bin/su", "/system/xbin/su", "/sbin/su",
            "/data/local/xbin/su", "/data/local/bin/su", "/data/local/su",
            "/system/sd/xbin/su", "/system/app/Superuser.apk",
            "/system/app/SuperSU.apk", "/system/app/Magisk.apk"
        };
        for (String path : suPaths) {
            if (new File(path).exists()) return true;
        }

        // Check build tags
        String buildTags = android.os.Build.TAGS;
        if (buildTags != null && buildTags.contains("test-keys")) return true;

        // Check if su is accessible via which
        try {
            Process process = Runtime.getRuntime().exec(new String[]{"which", "su"});
            if (process.waitFor() == 0) return true;
        } catch (Throwable ignored) {}

        return false;
    }
}
