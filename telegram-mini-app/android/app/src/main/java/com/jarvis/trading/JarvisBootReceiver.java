package com.jarvis.trading;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.util.Log;

/**
 * 🔄 JARVIS Boot Receiver
 * 
 * Starts JARVIS service automatically when phone boots up.
 * JARVIS is always ready, just like Iron Man's AI.
 */
public class JarvisBootReceiver extends BroadcastReceiver {
    private static final String TAG = "JarvisBootReceiver";

    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent == null) return;
        String action = intent.getAction();
        if (Intent.ACTION_BOOT_COMPLETED.equals(action) || 
            Intent.ACTION_LOCKED_BOOT_COMPLETED.equals(action) ||
            "android.intent.action.QUICKBOOT_POWERON".equals(action)) {
            Log.i(TAG, "📱 Boot detected - Starting JARVIS service...");
            try {
                Intent serviceIntent = new Intent(context, JarvisService.class);
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    context.startForegroundService(serviceIntent);
                } else {
                    context.startService(serviceIntent);
                }
                Log.i(TAG, "✅ JARVIS service started on boot");
            } catch (Throwable e) {
                Log.e(TAG, "❌ Failed to start JARVIS on boot: " + e.getMessage());
            }
        }
    }
}
