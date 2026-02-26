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
        // Boot receiver disabled for stability
        Log.i(TAG, "Boot event received but service auto-start is disabled");
    }
}
