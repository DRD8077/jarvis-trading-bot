package com.jarvis.trading.plugins;

import android.Manifest;
import android.app.Activity;
import android.content.ContentResolver;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.media.AudioManager;
import android.net.Uri;
import android.os.Build;
import android.provider.CallLog;
import android.provider.ContactsContract;
import android.provider.Settings;
import android.provider.Telephony;
import android.telecom.TelecomManager;
import android.util.Log;

import com.getcapacitor.JSArray;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.getcapacitor.annotation.Permission;

import org.json.JSONException;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

/**
 * 📱 JARVIS Personal Assistant Plugin — Android Native
 * ═══════════════════════════════════════════════════════
 *
 * Native Capacitor plugin for personal assistant features:
 * - Contact access and search
 * - Call management (make, answer, reject calls)
 * - SMS read and send
 * - WhatsApp integration (open chat, send message)
 * - Call log access
 * - Notification listener (read incoming notifications)
 * - Video call proxy via Intent
 *
 * Permissions are requested at runtime. Graceful fallback
 * when permissions are denied.
 */
@CapacitorPlugin(
    name = "PersonalAssistant",
    permissions = {
        @Permission(strings = {Manifest.permission.READ_CONTACTS}, alias = "contacts"),
        @Permission(strings = {Manifest.permission.READ_CALL_LOG}, alias = "callLog"),
        @Permission(strings = {Manifest.permission.CALL_PHONE}, alias = "phone"),
        @Permission(strings = {Manifest.permission.READ_SMS}, alias = "sms"),
        @Permission(strings = {Manifest.permission.SEND_SMS}, alias = "sendSms"),
        @Permission(strings = {Manifest.permission.READ_PHONE_STATE}, alias = "phoneState"),
        @Permission(strings = {Manifest.permission.RECORD_AUDIO}, alias = "microphone"),
        @Permission(strings = {Manifest.permission.CAMERA}, alias = "camera")
    }
)
public class PersonalAssistantPlugin extends Plugin {
    private static final String TAG = "JarvisPA";

    // ═══════════════════════════════
    // CONTACTS
    // ═══════════════════════════════

    /**
     * Get all contacts from phone
     */
    @PluginMethod
    public void getContacts(PluginCall call) {
        try {
            if (!hasRequiredPermission(Manifest.permission.READ_CONTACTS)) {
                requestPermissionForAlias("contacts", call, "handleContactsPermission");
                return;
            }

            JSArray contacts = new JSArray();
            ContentResolver cr = getContext().getContentResolver();
            Cursor cursor = cr.query(
                ContactsContract.CommonDataKinds.Phone.CONTENT_URI,
                new String[]{
                    ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME,
                    ContactsContract.CommonDataKinds.Phone.NUMBER,
                    ContactsContract.CommonDataKinds.Phone.CONTACT_ID
                },
                null, null,
                ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME + " ASC"
            );

            if (cursor != null) {
                int limit = call.getInt("limit", 500);
                int count = 0;
                while (cursor.moveToNext() && count < limit) {
                    JSObject contact = new JSObject();
                    contact.put("name", cursor.getString(0));
                    contact.put("phone", cursor.getString(1));
                    contact.put("id", cursor.getString(2));
                    contacts.put(contact);
                    count++;
                }
                cursor.close();
            }

            JSObject result = new JSObject();
            result.put("contacts", contacts);
            result.put("count", contacts.length());
            call.resolve(result);
        } catch (Exception e) {
            Log.e(TAG, "getContacts error: " + e.getMessage());
            call.reject("Failed to get contacts: " + e.getMessage());
        }
    }

    @PluginMethod
    public void handleContactsPermission(PluginCall call) {
        if (hasRequiredPermission(Manifest.permission.READ_CONTACTS)) {
            getContacts(call);
        } else {
            call.reject("Contacts permission denied");
        }
    }

    /**
     * Search contacts by name or number
     */
    @PluginMethod
    public void searchContacts(PluginCall call) {
        String query = call.getString("query", "");
        if (query.isEmpty()) {
            call.reject("Query is required");
            return;
        }

        try {
            if (!hasRequiredPermission(Manifest.permission.READ_CONTACTS)) {
                requestPermissionForAlias("contacts", call, "handleContactsPermission");
                return;
            }

            JSArray results = new JSArray();
            ContentResolver cr = getContext().getContentResolver();
            Cursor cursor = cr.query(
                ContactsContract.CommonDataKinds.Phone.CONTENT_URI,
                new String[]{
                    ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME,
                    ContactsContract.CommonDataKinds.Phone.NUMBER,
                    ContactsContract.CommonDataKinds.Phone.CONTACT_ID
                },
                ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME + " LIKE ?",
                new String[]{"%" + query + "%"},
                ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME + " ASC"
            );

            if (cursor != null) {
                while (cursor.moveToNext()) {
                    JSObject contact = new JSObject();
                    contact.put("name", cursor.getString(0));
                    contact.put("phone", cursor.getString(1));
                    contact.put("id", cursor.getString(2));
                    results.put(contact);
                }
                cursor.close();
            }

            JSObject result = new JSObject();
            result.put("contacts", results);
            result.put("count", results.length());
            call.resolve(result);
        } catch (Exception e) {
            call.reject("Search failed: " + e.getMessage());
        }
    }

    // ═══════════════════════════════
    // CALL MANAGEMENT
    // ═══════════════════════════════

    /**
     * Make a phone call
     */
    @PluginMethod
    public void makeCall(PluginCall call) {
        String phone = call.getString("phone", "");
        if (phone.isEmpty()) {
            call.reject("Phone number is required");
            return;
        }

        try {
            if (!hasRequiredPermission(Manifest.permission.CALL_PHONE)) {
                requestPermissionForAlias("phone", call, "handlePhonePermission");
                return;
            }

            Intent intent = new Intent(Intent.ACTION_CALL);
            intent.setData(Uri.parse("tel:" + phone));
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            getContext().startActivity(intent);

            JSObject result = new JSObject();
            result.put("success", true);
            result.put("message", "Calling " + phone);
            call.resolve(result);
        } catch (Exception e) {
            call.reject("Call failed: " + e.getMessage());
        }
    }

    @PluginMethod
    public void handlePhonePermission(PluginCall call) {
        if (hasRequiredPermission(Manifest.permission.CALL_PHONE)) {
            makeCall(call);
        } else {
            call.reject("Phone permission denied");
        }
    }

    /**
     * Answer incoming call (Android 8+)
     */
    @PluginMethod
    public void answerCall(PluginCall call) {
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                TelecomManager tm = (TelecomManager) getContext().getSystemService(Context.TELECOM_SERVICE);
                if (tm != null && hasRequiredPermission(Manifest.permission.ANSWER_PHONE_CALLS)) {
                    tm.acceptRingingCall();
                    JSObject result = new JSObject();
                    result.put("success", true);
                    result.put("message", "Call answered");
                    call.resolve(result);
                    return;
                }
            }
            call.reject("Cannot answer call — requires Android 8+ and permissions");
        } catch (Exception e) {
            call.reject("Answer failed: " + e.getMessage());
        }
    }

    /**
     * Reject/end incoming call
     */
    @PluginMethod
    public void rejectCall(PluginCall call) {
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                TelecomManager tm = (TelecomManager) getContext().getSystemService(Context.TELECOM_SERVICE);
                if (tm != null) {
                    tm.endCall();
                    JSObject result = new JSObject();
                    result.put("success", true);
                    result.put("message", "Call rejected");
                    call.resolve(result);
                    return;
                }
            }
            call.reject("Cannot reject call — requires Android 9+");
        } catch (Exception e) {
            call.reject("Reject failed: " + e.getMessage());
        }
    }

    /**
     * Enable/disable speakerphone
     */
    @PluginMethod
    public void setSpeaker(PluginCall call) {
        boolean enabled = call.getBoolean("enabled", true);
        try {
            AudioManager am = (AudioManager) getContext().getSystemService(Context.AUDIO_SERVICE);
            if (am != null) {
                am.setSpeakerphoneOn(enabled);
                JSObject result = new JSObject();
                result.put("success", true);
                result.put("speaker", enabled);
                call.resolve(result);
            } else {
                call.reject("AudioManager unavailable");
            }
        } catch (Exception e) {
            call.reject("Speaker toggle failed: " + e.getMessage());
        }
    }

    // ═══════════════════════════════
    // CALL LOG
    // ═══════════════════════════════

    /**
     * Get recent call history
     */
    @PluginMethod
    public void getCallLog(PluginCall call) {
        try {
            if (!hasRequiredPermission(Manifest.permission.READ_CALL_LOG)) {
                requestPermissionForAlias("callLog", call, "handleCallLogPermission");
                return;
            }

            int limit = call.getInt("limit", 50);
            JSArray logs = new JSArray();
            ContentResolver cr = getContext().getContentResolver();
            Cursor cursor = cr.query(
                CallLog.Calls.CONTENT_URI,
                new String[]{
                    CallLog.Calls.NUMBER,
                    CallLog.Calls.CACHED_NAME,
                    CallLog.Calls.TYPE,
                    CallLog.Calls.DATE,
                    CallLog.Calls.DURATION
                },
                null, null,
                CallLog.Calls.DATE + " DESC"
            );

            if (cursor != null) {
                int count = 0;
                SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault());
                while (cursor.moveToNext() && count < limit) {
                    JSObject entry = new JSObject();
                    entry.put("number", cursor.getString(0));
                    entry.put("name", cursor.getString(1) != null ? cursor.getString(1) : "Unknown");
                    int type = cursor.getInt(2);
                    String typeStr = type == CallLog.Calls.INCOMING_TYPE ? "incoming" :
                                     type == CallLog.Calls.OUTGOING_TYPE ? "outgoing" :
                                     type == CallLog.Calls.MISSED_TYPE ? "missed" : "other";
                    entry.put("type", typeStr);
                    entry.put("date", sdf.format(new Date(cursor.getLong(3))));
                    entry.put("duration", cursor.getInt(4));
                    logs.put(entry);
                    count++;
                }
                cursor.close();
            }

            JSObject result = new JSObject();
            result.put("calls", logs);
            result.put("count", logs.length());
            call.resolve(result);
        } catch (Exception e) {
            call.reject("Call log failed: " + e.getMessage());
        }
    }

    @PluginMethod
    public void handleCallLogPermission(PluginCall call) {
        if (hasRequiredPermission(Manifest.permission.READ_CALL_LOG)) {
            getCallLog(call);
        } else {
            call.reject("Call log permission denied");
        }
    }

    // ═══════════════════════════════
    // SMS
    // ═══════════════════════════════

    /**
     * Read recent SMS messages
     */
    @PluginMethod
    public void getMessages(PluginCall call) {
        try {
            if (!hasRequiredPermission(Manifest.permission.READ_SMS)) {
                requestPermissionForAlias("sms", call, "handleSmsPermission");
                return;
            }

            int limit = call.getInt("limit", 50);
            String filter = call.getString("filter", "all"); // all, inbox, sent

            Uri uri = filter.equals("sent") ? Telephony.Sms.Sent.CONTENT_URI :
                       filter.equals("inbox") ? Telephony.Sms.Inbox.CONTENT_URI :
                       Telephony.Sms.CONTENT_URI;

            JSArray messages = new JSArray();
            ContentResolver cr = getContext().getContentResolver();
            Cursor cursor = cr.query(
                uri,
                new String[]{
                    Telephony.Sms.ADDRESS,
                    Telephony.Sms.BODY,
                    Telephony.Sms.DATE,
                    Telephony.Sms.TYPE
                },
                null, null,
                Telephony.Sms.DATE + " DESC"
            );

            if (cursor != null) {
                int count = 0;
                SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault());
                while (cursor.moveToNext() && count < limit) {
                    JSObject msg = new JSObject();
                    msg.put("address", cursor.getString(0));
                    msg.put("body", cursor.getString(1));
                    msg.put("date", sdf.format(new Date(cursor.getLong(2))));
                    int type = cursor.getInt(3);
                    msg.put("type", type == Telephony.Sms.MESSAGE_TYPE_INBOX ? "received" : "sent");
                    messages.put(msg);
                    count++;
                }
                cursor.close();
            }

            JSObject result = new JSObject();
            result.put("messages", messages);
            result.put("count", messages.length());
            call.resolve(result);
        } catch (Exception e) {
            call.reject("SMS read failed: " + e.getMessage());
        }
    }

    @PluginMethod
    public void handleSmsPermission(PluginCall call) {
        if (hasRequiredPermission(Manifest.permission.READ_SMS)) {
            getMessages(call);
        } else {
            call.reject("SMS permission denied");
        }
    }

    /**
     * Send an SMS message
     */
    @PluginMethod
    public void sendSms(PluginCall call) {
        String phone = call.getString("phone", "");
        String message = call.getString("message", "");

        if (phone.isEmpty() || message.isEmpty()) {
            call.reject("Phone and message are required");
            return;
        }

        try {
            // Use Intent to open SMS app (doesn't require SEND_SMS permission)
            Intent intent = new Intent(Intent.ACTION_SENDTO);
            intent.setData(Uri.parse("smsto:" + phone));
            intent.putExtra("sms_body", message);
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            getContext().startActivity(intent);

            JSObject result = new JSObject();
            result.put("success", true);
            result.put("message", "Opening SMS to " + phone);
            call.resolve(result);
        } catch (Exception e) {
            call.reject("Send SMS failed: " + e.getMessage());
        }
    }

    // ═══════════════════════════════
    // WHATSAPP INTEGRATION
    // ═══════════════════════════════

    /**
     * Open WhatsApp chat with a number
     */
    @PluginMethod
    public void openWhatsApp(PluginCall call) {
        String phone = call.getString("phone", "");
        String message = call.getString("message", "");

        try {
            String url;
            if (!phone.isEmpty()) {
                // Remove + and spaces from phone number
                String cleanPhone = phone.replaceAll("[^0-9]", "");
                url = "https://api.whatsapp.com/send?phone=" + cleanPhone;
                if (!message.isEmpty()) {
                    url += "&text=" + Uri.encode(message);
                }
            } else {
                url = "whatsapp://";
            }

            Intent intent = new Intent(Intent.ACTION_VIEW);
            intent.setData(Uri.parse(url));
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            getContext().startActivity(intent);

            JSObject result = new JSObject();
            result.put("success", true);
            result.put("message", phone.isEmpty() ? "Opening WhatsApp" : "Opening chat with " + phone);
            call.resolve(result);
        } catch (Exception e) {
            call.reject("WhatsApp open failed: " + e.getMessage());
        }
    }

    /**
     * Make a WhatsApp voice/video call
     */
    @PluginMethod
    public void whatsAppCall(PluginCall call) {
        String phone = call.getString("phone", "");
        boolean video = call.getBoolean("video", false);

        if (phone.isEmpty()) {
            call.reject("Phone number is required");
            return;
        }

        try {
            String cleanPhone = phone.replaceAll("[^0-9]", "");
            // WhatsApp uses contacts URI for calls
            Intent intent = new Intent(Intent.ACTION_VIEW);
            String url = "https://api.whatsapp.com/send?phone=" + cleanPhone;
            intent.setData(Uri.parse(url));
            intent.setPackage("com.whatsapp");
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            getContext().startActivity(intent);

            JSObject result = new JSObject();
            result.put("success", true);
            result.put("message", (video ? "Video" : "Voice") + " call to " + phone);
            call.resolve(result);
        } catch (Exception e) {
            call.reject("WhatsApp call failed: " + e.getMessage());
        }
    }

    // ═══════════════════════════════
    // VIDEO CALL PROXY
    // ═══════════════════════════════

    /**
     * Start a video call via default video app
     */
    @PluginMethod
    public void startVideoCall(PluginCall call) {
        String phone = call.getString("phone", "");
        String app = call.getString("app", "default"); // default, whatsapp, google-meet

        try {
            Intent intent;
            switch (app.toLowerCase()) {
                case "whatsapp":
                    intent = new Intent(Intent.ACTION_VIEW);
                    String cleanPhone = phone.replaceAll("[^0-9]", "");
                    intent.setData(Uri.parse("https://api.whatsapp.com/send?phone=" + cleanPhone));
                    intent.setPackage("com.whatsapp");
                    break;
                case "google-meet":
                case "meet":
                    intent = new Intent(Intent.ACTION_VIEW);
                    intent.setData(Uri.parse("https://meet.google.com/new"));
                    break;
                default:
                    // Default video call via phone dialer
                    intent = new Intent(Intent.ACTION_CALL);
                    intent.setData(Uri.parse("tel:" + phone));
                    intent.putExtra("android.telecom.extra.START_CALL_WITH_VIDEO_STATE", 3); // Video TX+RX
                    break;
            }

            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            getContext().startActivity(intent);

            JSObject result = new JSObject();
            result.put("success", true);
            result.put("message", "Starting video call via " + app);
            call.resolve(result);
        } catch (Exception e) {
            call.reject("Video call failed: " + e.getMessage());
        }
    }

    // ═══════════════════════════════
    // NOTIFICATION ACCESS
    // ═══════════════════════════════

    /**
     * Check if notification listener permission is granted
     */
    @PluginMethod
    public void hasNotificationAccess(PluginCall call) {
        try {
            String packageName = getContext().getPackageName();
            String listeners = Settings.Secure.getString(
                getContext().getContentResolver(),
                "enabled_notification_listeners"
            );

            boolean hasAccess = listeners != null && listeners.contains(packageName);

            JSObject result = new JSObject();
            result.put("granted", hasAccess);
            call.resolve(result);
        } catch (Exception e) {
            JSObject result = new JSObject();
            result.put("granted", false);
            call.resolve(result);
        }
    }

    /**
     * Request notification listener permission
     */
    @PluginMethod
    public void requestNotificationAccess(PluginCall call) {
        try {
            Intent intent = new Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS);
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            getContext().startActivity(intent);

            JSObject result = new JSObject();
            result.put("success", true);
            result.put("message", "Settings opened — please enable JARVIS notification access");
            call.resolve(result);
        } catch (Exception e) {
            call.reject("Could not open notification settings: " + e.getMessage());
        }
    }

    // ═══════════════════════════════
    // PA CAPABILITIES CHECK
    // ═══════════════════════════════

    /**
     * Get all PA capabilities and permission states
     */
    @PluginMethod
    public void getCapabilities(PluginCall call) {
        JSObject caps = new JSObject();
        caps.put("contacts", hasRequiredPermission(Manifest.permission.READ_CONTACTS));
        caps.put("phone", hasRequiredPermission(Manifest.permission.CALL_PHONE));
        caps.put("callLog", hasRequiredPermission(Manifest.permission.READ_CALL_LOG));
        caps.put("sms", hasRequiredPermission(Manifest.permission.READ_SMS));
        caps.put("camera", hasRequiredPermission(Manifest.permission.CAMERA));
        caps.put("microphone", hasRequiredPermission(Manifest.permission.RECORD_AUDIO));

        // Check WhatsApp availability
        boolean hasWhatsApp = false;
        try {
            getContext().getPackageManager().getPackageInfo("com.whatsapp", 0);
            hasWhatsApp = true;
        } catch (PackageManager.NameNotFoundException e) {
            // WhatsApp not installed
        }
        caps.put("whatsapp", hasWhatsApp);
        caps.put("videoCall", true); // Always available via Intent
        caps.put("platform", "android");
        caps.put("sdkVersion", Build.VERSION.SDK_INT);

        JSObject result = new JSObject();
        result.put("capabilities", caps);
        call.resolve(result);
    }

    // ═══════════════════════════════
    // PERMISSION HELPER
    // ═══════════════════════════════

    private boolean hasRequiredPermission(String permission) {
        return getContext().checkSelfPermission(permission) == PackageManager.PERMISSION_GRANTED;
    }

    /**
     * Request a specific permission by name
     */
    @PluginMethod
    public void requestPermission(PluginCall call) {
        String permission = call.getString("permission", "");
        switch (permission.toUpperCase()) {
            case "CONTACTS":
                requestPermissionForAlias("contacts", call, "permissionResult");
                break;
            case "PHONE":
            case "CALL_PHONE":
                requestPermissionForAlias("phone", call, "permissionResult");
                break;
            case "CALL_LOG":
            case "READ_CALL_LOG":
                requestPermissionForAlias("callLog", call, "permissionResult");
                break;
            case "SMS":
            case "READ_SMS":
                requestPermissionForAlias("sms", call, "permissionResult");
                break;
            case "SEND_SMS":
                requestPermissionForAlias("sendSms", call, "permissionResult");
                break;
            case "CAMERA":
                requestPermissionForAlias("camera", call, "permissionResult");
                break;
            case "MICROPHONE":
            case "RECORD_AUDIO":
                requestPermissionForAlias("microphone", call, "permissionResult");
                break;
            case "NOTIFICATION_LISTENER":
                requestNotificationAccess(call);
                break;
            default:
                call.reject("Unknown permission: " + permission);
        }
    }

    @PluginMethod
    public void permissionResult(PluginCall call) {
        JSObject result = new JSObject();
        result.put("success", true);
        result.put("message", "Permission dialog shown");
        call.resolve(result);
    }
}
