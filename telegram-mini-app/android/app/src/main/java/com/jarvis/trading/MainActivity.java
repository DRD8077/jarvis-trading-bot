package com.jarvis.trading;

import android.os.Bundle;
import android.util.Log;
import com.getcapacitor.BridgeActivity;

/**
 * JARVIS AI — Minimal stable MainActivity
 * All custom plugins and services are disabled to ensure stable launch.
 * The web app handles all logic via Capacitor's built-in plugins.
 */
public class MainActivity extends BridgeActivity {
    private static final String TAG = "JARVIS";

    @Override
    public void onCreate(Bundle savedInstanceState) {
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
        Log.i(TAG, "JARVIS AI started successfully");
    }
}
