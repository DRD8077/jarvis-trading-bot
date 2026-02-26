package com.jarvis.trading;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.os.Build;
import android.os.IBinder;
import android.util.Log;

import androidx.core.app.NotificationCompat;

/**
 * 🤖 JARVIS Always-On Service
 * 
 * Foreground service that keeps JARVIS running in background.
 * Shows persistent notification so Android doesn't kill the app.
 * Enables:
 * - Always-on voice listening (wake word detection)
 * - Real-time market alerts
 * - Background price monitoring
 * - Notification-based quick actions
 */
public class JarvisService extends Service {
    private static final String TAG = "JarvisService";
    private static final String CHANNEL_ID = "jarvis_always_on";
    private static final int NOTIFICATION_ID = 7777;

    @Override
    public void onCreate() {
        super.onCreate();
        Log.i(TAG, "🤖 JARVIS Service created — Always-on mode ACTIVE");
        createNotificationChannel();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        Log.i(TAG, "🚀 JARVIS Service started — entering foreground");

        // Create notification for foreground service
        Notification notification = buildNotification();
        startForeground(NOTIFICATION_ID, notification);

        // Return START_STICKY so Android restarts us if killed
        return START_STICKY;
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null; // Not a bound service
    }

    @Override
    public void onDestroy() {
        Log.i(TAG, "⚠️ JARVIS Service destroyed — will restart via START_STICKY");
        super.onDestroy();
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                CHANNEL_ID,
                "JARVIS Always-On",
                NotificationManager.IMPORTANCE_LOW
            );
            channel.setDescription("Keeps JARVIS AI running for voice commands and market alerts");
            channel.setShowBadge(false);
            channel.enableLights(false);
            channel.enableVibration(false);

            NotificationManager manager = getSystemService(NotificationManager.class);
            if (manager != null) {
                manager.createNotificationChannel(channel);
            }
        }
    }

    private Notification buildNotification() {
        Intent notificationIntent = new Intent(this, MainActivity.class);
        notificationIntent.setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        
        PendingIntent pendingIntent = PendingIntent.getActivity(
            this, 0, notificationIntent,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );

        return new NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("JARVIS AI — Online")
            .setContentText("Listening for commands • Market monitoring active")
            .setSmallIcon(android.R.drawable.ic_menu_compass)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setCategory(NotificationCompat.CATEGORY_SERVICE)
            .build();
    }
}
