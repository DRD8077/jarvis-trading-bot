package com.jarvis.trading.plugins;

import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.media.AudioManager;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import android.net.Uri;
import android.net.wifi.WifiInfo;
import android.net.wifi.WifiManager;
import android.os.BatteryManager;
import android.os.Build;
import android.os.Vibrator;
import android.provider.Settings;
import android.util.Log;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;
import java.util.TimeZone;

/**
 * 📱 DeviceCommandsPlugin — Capacitor Plugin for Phone Tasks
 * 
 * Allows the AI agent to control phone functions:
 * - Battery status
 * - Network info
 * - Make calls
 * - Open apps
 * - Volume control
 * - Vibration
 * - Device info
 * - Flashlight
 * - Time/Date
 */
@CapacitorPlugin(name = "DeviceCommands")
public class DeviceCommandsPlugin extends Plugin {
    private static final String TAG = "DeviceCommands";

    /**
     * Get battery status
     */
    @PluginMethod
    public void getBattery(PluginCall call) {
        IntentFilter filter = new IntentFilter(Intent.ACTION_BATTERY_CHANGED);
        Intent battery = getContext().registerReceiver(null, filter);
        
        JSObject ret = new JSObject();
        if (battery != null) {
            int level = battery.getIntExtra(BatteryManager.EXTRA_LEVEL, -1);
            int scale = battery.getIntExtra(BatteryManager.EXTRA_SCALE, -1);
            int status = battery.getIntExtra(BatteryManager.EXTRA_STATUS, -1);
            int plugged = battery.getIntExtra(BatteryManager.EXTRA_PLUGGED, -1);
            int temp = battery.getIntExtra(BatteryManager.EXTRA_TEMPERATURE, -1);
            int voltage = battery.getIntExtra(BatteryManager.EXTRA_VOLTAGE, -1);
            String tech = battery.getStringExtra(BatteryManager.EXTRA_TECHNOLOGY);
            
            float percentage = level * 100f / scale;
            
            ret.put("level", Math.round(percentage));
            ret.put("isCharging", status == BatteryManager.BATTERY_STATUS_CHARGING || 
                                  status == BatteryManager.BATTERY_STATUS_FULL);
            ret.put("chargingType", plugged == BatteryManager.BATTERY_PLUGGED_USB ? "USB" :
                                   plugged == BatteryManager.BATTERY_PLUGGED_AC ? "AC" :
                                   plugged == BatteryManager.BATTERY_PLUGGED_WIRELESS ? "Wireless" : "None");
            ret.put("temperature", temp / 10.0);
            ret.put("voltage", voltage / 1000.0);
            ret.put("technology", tech);
            ret.put("status", status == BatteryManager.BATTERY_STATUS_FULL ? "Full" :
                              status == BatteryManager.BATTERY_STATUS_CHARGING ? "Charging" :
                              status == BatteryManager.BATTERY_STATUS_DISCHARGING ? "Discharging" :
                              status == BatteryManager.BATTERY_STATUS_NOT_CHARGING ? "Not Charging" : "Unknown");
        }
        call.resolve(ret);
    }

    /**
     * Get network/connectivity info
     */
    @PluginMethod
    public void getNetwork(PluginCall call) {
        JSObject ret = new JSObject();
        
        ConnectivityManager cm = (ConnectivityManager) getContext().getSystemService(Context.CONNECTIVITY_SERVICE);
        if (cm != null) {
            NetworkInfo activeNetwork = cm.getActiveNetworkInfo();
            ret.put("connected", activeNetwork != null && activeNetwork.isConnected());
            ret.put("type", activeNetwork != null ? activeNetwork.getTypeName() : "None");
        }
        
        WifiManager wm = (WifiManager) getContext().getApplicationContext().getSystemService(Context.WIFI_SERVICE);
        if (wm != null) {
            WifiInfo wi = wm.getConnectionInfo();
            ret.put("wifiEnabled", wm.isWifiEnabled());
            ret.put("ssid", wi != null ? wi.getSSID() : "Unknown");
            ret.put("signalStrength", wi != null ? WifiManager.calculateSignalLevel(wi.getRssi(), 5) : 0);
        }
        
        call.resolve(ret);
    }

    /**
     * Get device info
     */
    @PluginMethod
    public void getDeviceInfo(PluginCall call) {
        JSObject ret = new JSObject();
        ret.put("brand", Build.BRAND);
        ret.put("model", Build.MODEL);
        ret.put("device", Build.DEVICE);
        ret.put("manufacturer", Build.MANUFACTURER);
        ret.put("androidVersion", Build.VERSION.RELEASE);
        ret.put("sdkVersion", Build.VERSION.SDK_INT);
        ret.put("product", Build.PRODUCT);
        
        // RAM info
        Runtime rt = Runtime.getRuntime();
        ret.put("totalMemoryMB", rt.totalMemory() / (1024 * 1024));
        ret.put("freeMemoryMB", rt.freeMemory() / (1024 * 1024));
        ret.put("maxMemoryMB", rt.maxMemory() / (1024 * 1024));
        ret.put("processors", rt.availableProcessors());
        
        call.resolve(ret);
    }

    /**
     * Get current time and date
     */
    @PluginMethod
    public void getDateTime(PluginCall call) {
        String timezone = call.getString("timezone", "Asia/Kolkata");
        
        JSObject ret = new JSObject();
        Date now = new Date();
        
        SimpleDateFormat dateFmt = new SimpleDateFormat("dd MMMM yyyy", Locale.getDefault());
        SimpleDateFormat timeFmt = new SimpleDateFormat("hh:mm a", Locale.getDefault());
        SimpleDateFormat dayFmt = new SimpleDateFormat("EEEE", Locale.getDefault());
        SimpleDateFormat fullFmt = new SimpleDateFormat("dd MMM yyyy, hh:mm:ss a", Locale.getDefault());
        
        TimeZone tz = TimeZone.getTimeZone(timezone);
        dateFmt.setTimeZone(tz);
        timeFmt.setTimeZone(tz);
        dayFmt.setTimeZone(tz);
        fullFmt.setTimeZone(tz);
        
        ret.put("date", dateFmt.format(now));
        ret.put("time", timeFmt.format(now));
        ret.put("day", dayFmt.format(now));
        ret.put("full", fullFmt.format(now));
        ret.put("timestamp", now.getTime());
        ret.put("timezone", timezone);
        
        call.resolve(ret);
    }

    /**
     * Make a phone call
     */
    @PluginMethod
    public void makeCall(PluginCall call) {
        String number = call.getString("number", "");
        if (number.isEmpty()) {
            call.reject("Phone number required");
            return;
        }
        
        Intent intent = new Intent(Intent.ACTION_DIAL);
        intent.setData(Uri.parse("tel:" + number));
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        getContext().startActivity(intent);
        
        JSObject ret = new JSObject();
        ret.put("success", true);
        ret.put("number", number);
        call.resolve(ret);
    }

    /**
     * Send SMS
     */
    @PluginMethod
    public void sendSMS(PluginCall call) {
        String number = call.getString("number", "");
        String message = call.getString("message", "");
        
        Intent intent = new Intent(Intent.ACTION_VIEW);
        intent.setData(Uri.parse("sms:" + number));
        intent.putExtra("sms_body", message);
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        getContext().startActivity(intent);
        
        JSObject ret = new JSObject();
        ret.put("success", true);
        call.resolve(ret);
    }

    /**
     * Open a URL in browser
     */
    @PluginMethod
    public void openUrl(PluginCall call) {
        String url = call.getString("url", "");
        if (url.isEmpty()) {
            call.reject("URL required");
            return;
        }
        
        if (!url.startsWith("http")) url = "https://" + url;
        
        Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        getContext().startActivity(intent);
        
        JSObject ret = new JSObject();
        ret.put("success", true);
        call.resolve(ret);
    }

    /**
     * Open an app by package name
     */
    @PluginMethod
    public void openApp(PluginCall call) {
        String packageName = call.getString("package", "");
        
        if (packageName.isEmpty()) {
            call.reject("Package name required");
            return;
        }
        
        Intent intent = getContext().getPackageManager().getLaunchIntentForPackage(packageName);
        if (intent != null) {
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            getContext().startActivity(intent);
            
            JSObject ret = new JSObject();
            ret.put("success", true);
            ret.put("package", packageName);
            call.resolve(ret);
        } else {
            call.reject("App not found: " + packageName);
        }
    }

    /**
     * Set volume level
     */
    @PluginMethod
    public void setVolume(PluginCall call) {
        int level = call.getInt("level", 50);
        String stream = call.getString("stream", "media");
        
        AudioManager am = (AudioManager) getContext().getSystemService(Context.AUDIO_SERVICE);
        if (am == null) {
            call.reject("Audio service not available");
            return;
        }
        
        int streamType;
        switch (stream) {
            case "ring": streamType = AudioManager.STREAM_RING; break;
            case "alarm": streamType = AudioManager.STREAM_ALARM; break;
            case "notification": streamType = AudioManager.STREAM_NOTIFICATION; break;
            default: streamType = AudioManager.STREAM_MUSIC; break;
        }
        
        int maxVol = am.getStreamMaxVolume(streamType);
        int vol = (int) (level * maxVol / 100.0);
        am.setStreamVolume(streamType, vol, 0);
        
        JSObject ret = new JSObject();
        ret.put("success", true);
        ret.put("level", level);
        ret.put("stream", stream);
        call.resolve(ret);
    }

    /**
     * Get current volume levels
     */
    @PluginMethod
    public void getVolume(PluginCall call) {
        AudioManager am = (AudioManager) getContext().getSystemService(Context.AUDIO_SERVICE);
        JSObject ret = new JSObject();
        
        if (am != null) {
            ret.put("media", am.getStreamVolume(AudioManager.STREAM_MUSIC) * 100 / 
                    am.getStreamMaxVolume(AudioManager.STREAM_MUSIC));
            ret.put("ring", am.getStreamVolume(AudioManager.STREAM_RING) * 100 / 
                    am.getStreamMaxVolume(AudioManager.STREAM_RING));
            ret.put("alarm", am.getStreamVolume(AudioManager.STREAM_ALARM) * 100 / 
                    am.getStreamMaxVolume(AudioManager.STREAM_ALARM));
            ret.put("notification", am.getStreamVolume(AudioManager.STREAM_NOTIFICATION) * 100 / 
                    am.getStreamMaxVolume(AudioManager.STREAM_NOTIFICATION));
        }
        
        call.resolve(ret);
    }

    /**
     * Vibrate the phone
     */
    @PluginMethod
    public void vibrate(PluginCall call) {
        int duration = call.getInt("duration", 200);
        String pattern = call.getString("pattern", "");
        
        Vibrator v = (Vibrator) getContext().getSystemService(Context.VIBRATOR_SERVICE);
        if (v != null && v.hasVibrator()) {
            if (!pattern.isEmpty()) {
                // Parse pattern like "100,200,100,400"
                String[] parts = pattern.split(",");
                long[] times = new long[parts.length];
                for (int i = 0; i < parts.length; i++) {
                    times[i] = Long.parseLong(parts[i].trim());
                }
                v.vibrate(times, -1);
            } else {
                v.vibrate(duration);
            }
        }
        
        JSObject ret = new JSObject();
        ret.put("success", true);
        call.resolve(ret);
    }

    /**
     * Open phone settings
     */
    @PluginMethod
    public void openSettings(PluginCall call) {
        String setting = call.getString("setting", "");
        
        Intent intent;
        switch (setting) {
            case "wifi": intent = new Intent(Settings.ACTION_WIFI_SETTINGS); break;
            case "bluetooth": intent = new Intent(Settings.ACTION_BLUETOOTH_SETTINGS); break;
            case "display": intent = new Intent(Settings.ACTION_DISPLAY_SETTINGS); break;
            case "sound": intent = new Intent(Settings.ACTION_SOUND_SETTINGS); break;
            case "location": intent = new Intent(Settings.ACTION_LOCATION_SOURCE_SETTINGS); break;
            case "tts": intent = new Intent("com.android.settings.TTS_SETTINGS"); break;
            default: intent = new Intent(Settings.ACTION_SETTINGS); break;
        }
        
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        getContext().startActivity(intent);
        
        JSObject ret = new JSObject();
        ret.put("success", true);
        call.resolve(ret);
    }

    /**
     * Run a shell command (limited to safe commands)
     */
    @PluginMethod
    public void runCommand(PluginCall call) {
        String command = call.getString("command", "");
        
        // Safety: only allow certain commands
        String[] allowed = {"date", "uptime", "uname", "getprop", "df", "free", "cat /proc/meminfo",
                           "cat /proc/cpuinfo", "ip addr", "ps", "top -n 1"};
        boolean safe = false;
        for (String a : allowed) {
            if (command.startsWith(a)) { safe = true; break; }
        }
        
        if (!safe) {
            call.reject("Command not allowed for safety: " + command);
            return;
        }
        
        try {
            Process p = Runtime.getRuntime().exec(command);
            BufferedReader br = new BufferedReader(new InputStreamReader(p.getInputStream()));
            StringBuilder output = new StringBuilder();
            String line;
            while ((line = br.readLine()) != null) {
                output.append(line).append("\n");
            }
            br.close();
            p.waitFor();
            
            JSObject ret = new JSObject();
            ret.put("output", output.toString().trim());
            ret.put("exitCode", p.exitValue());
            call.resolve(ret);
        } catch (Exception e) {
            call.reject("Command failed: " + e.getMessage());
        }
    }
}
