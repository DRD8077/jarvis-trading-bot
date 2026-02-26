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
        if (Intent.ACTION_BOOT_COMPLETED.equals(intent.getAction()) ||
            Intent.ACTION_MY_PACKAGE_REPLACED.equals(intent.getAction())) {
            
            Log.i(TAG, "🚀 Phone booted — Starting JARVIS Service");

            Intent serviceIntent = new Intent(context, JarvisService.class);
            
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(serviceIntent);
            } else {
                context.startService(serviceIntent);
            }
        }
    }
}
