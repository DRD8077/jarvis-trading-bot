package com.jarvis.trading.plugins;

import android.Manifest;
import android.content.Context;
import android.os.Handler;
import android.os.HandlerThread;
import android.util.Log;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.getcapacitor.annotation.Permission;

import org.json.JSONObject;
import org.vosk.Model;
import org.vosk.Recognizer;
import org.vosk.android.RecognitionListener;
import org.vosk.android.SpeechService;
import org.vosk.android.StorageService;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

/**
 * 🎤 VoskSTTPlugin — Capacitor Plugin for Offline Speech-to-Text
 * 
 * Uses Vosk (alphacep) for fully offline speech recognition.
 * Supports Hindi (hi), English (en-us), and multilingual models.
 * 
 * Flow:
 * 1. initModel() - Load Vosk model from storage
 * 2. startListening() - Begin speech recognition
 * 3. stopListening() - Stop and get final result
 * 4. Events: partialResult, finalResult, error
 */
@CapacitorPlugin(
    name = "VoskSTT",
    permissions = {
        @Permission(strings = { Manifest.permission.RECORD_AUDIO }, alias = "microphone")
    }
)
public class VoskSTTPlugin extends Plugin implements RecognitionListener {
    private static final String TAG = "VoskSTT";
    
    private Model voskModel;
    private SpeechService speechService;
    private HandlerThread bgThread;
    private Handler bgHandler;
    private boolean isListening = false;
    private boolean modelReady = false;
    private PluginCall activeCall;

    @Override
    public void load() {
        bgThread = new HandlerThread("Vosk-Thread");
        bgThread.start();
        bgHandler = new Handler(bgThread.getLooper());
        Log.i(TAG, "VoskSTT Plugin loaded");
    }

    /**
     * Get available Vosk models
     */
    @PluginMethod
    public void getModels(PluginCall call) {
        JSObject ret = new JSObject();
        try {
            File modelsDir = new File(getContext().getFilesDir(), "vosk-models");
            if (!modelsDir.exists()) modelsDir.mkdirs();
            
            org.json.JSONArray models = new org.json.JSONArray();
            File[] dirs = modelsDir.listFiles();
            if (dirs != null) {
                for (File d : dirs) {
                    if (d.isDirectory()) {
                        // Check if valid Vosk model
                        File conf = new File(d, "conf/model.conf");
                        File mfcc = new File(d, "conf/mfcc.conf");
                        boolean valid = conf.exists() || mfcc.exists() || new File(d, "am/final.mdl").exists();
                        
                        JSObject model = new JSObject();
                        model.put("name", d.getName());
                        model.put("path", d.getAbsolutePath());
                        model.put("valid", valid);
                        
                        // Calculate folder size
                        long size = getFolderSize(d);
                        model.put("sizeMB", size / (1024 * 1024));
                        models.put(model);
                    }
                }
            }
            
            ret.put("models", models);
            ret.put("modelsDir", modelsDir.getAbsolutePath());
            ret.put("modelReady", modelReady);
            ret.put("isListening", isListening);
            call.resolve(ret);
        } catch (Exception e) {
            call.reject("Failed to list models: " + e.getMessage());
        }
    }

    /**
     * Initialize Vosk model for recognition
     */
    @PluginMethod
    public void initModel(PluginCall call) {
        String modelPath = call.getString("modelPath", "");
        String language = call.getString("language", "en-us");
        
        bgHandler.post(() -> {
            try {
                if (modelPath.isEmpty()) {
                    // Try to find model in vosk-models directory
                    File modelsDir = new File(getContext().getFilesDir(), "vosk-models");
                    File[] dirs = modelsDir.listFiles();
                    String foundPath = "";
                    if (dirs != null) {
                        for (File d : dirs) {
                            if (d.isDirectory() && d.getName().contains(language)) {
                                foundPath = d.getAbsolutePath();
                                break;
                            }
                        }
                        // Fallback: use first available model
                        if (foundPath.isEmpty() && dirs.length > 0) {
                            for (File d : dirs) {
                                if (d.isDirectory()) {
                                    foundPath = d.getAbsolutePath();
                                    break;
                                }
                            }
                        }
                    }
                    
                    if (foundPath.isEmpty()) {
                        call.reject("No Vosk model found. Download one first using downloadModel()");
                        return;
                    }
                    
                    voskModel = new Model(foundPath);
                } else {
                    voskModel = new Model(modelPath);
                }
                
                modelReady = true;
                
                JSObject ret = new JSObject();
                ret.put("success", true);
                ret.put("language", language);
                call.resolve(ret);
            } catch (Exception e) {
                Log.e(TAG, "Failed to init Vosk model", e);
                call.reject("Failed to init model: " + e.getMessage());
            }
        });
    }

    /**
     * Start listening for speech
     */
    @PluginMethod
    public void startListening(PluginCall call) {
        if (!modelReady || voskModel == null) {
            call.reject("Model not initialized. Call initModel() first.");
            return;
        }
        
        if (isListening) {
            call.reject("Already listening");
            return;
        }

        float sampleRate = call.getFloat("sampleRate", 16000f);
        
        try {
            Recognizer recognizer = new Recognizer(voskModel, sampleRate);
            recognizer.setMaxAlternatives(3);
            recognizer.setWords(true);
            
            speechService = new SpeechService(recognizer, sampleRate);
            speechService.startListening(this);
            isListening = true;
            activeCall = call;
            
            JSObject ret = new JSObject();
            ret.put("success", true);
            ret.put("listening", true);
            call.resolve(ret);
        } catch (Exception e) {
            Log.e(TAG, "Failed to start listening", e);
            call.reject("Failed to start: " + e.getMessage());
        }
    }

    /**
     * Stop listening and get final result
     */
    @PluginMethod
    public void stopListening(PluginCall call) {
        if (speechService != null) {
            speechService.stop();
            speechService = null;
        }
        isListening = false;
        
        JSObject ret = new JSObject();
        ret.put("success", true);
        ret.put("listening", false);
        call.resolve(ret);
    }

    /**
     * Download a Vosk model
     */
    @PluginMethod
    public void downloadModel(PluginCall call) {
        String language = call.getString("language", "en-us");
        
        // Model URLs (small models for phone)
        String modelUrl;
        String modelName;
        switch (language) {
            case "hi":
                modelUrl = "https://alphacephei.com/vosk/models/vosk-model-small-hi-0.22.zip";
                modelName = "vosk-model-small-hi";
                break;
            case "en-in":
                modelUrl = "https://alphacephei.com/vosk/models/vosk-model-small-en-in-0.4.zip";
                modelName = "vosk-model-small-en-in";
                break;
            case "en-us":
            default:
                modelUrl = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip";
                modelName = "vosk-model-small-en-us";
                break;
        }
        
        // Allow custom URL override
        String customUrl = call.getString("url", "");
        if (!customUrl.isEmpty()) {
            modelUrl = customUrl;
            modelName = call.getString("modelName", "custom-model");
        }
        
        final String finalUrl = modelUrl;
        final String finalName = modelName;
        
        bgHandler.post(() -> {
            try {
                File modelsDir = new File(getContext().getFilesDir(), "vosk-models");
                modelsDir.mkdirs();
                
                File modelDir = new File(modelsDir, finalName);
                if (modelDir.exists() && modelDir.listFiles() != null && modelDir.listFiles().length > 0) {
                    JSObject ret = new JSObject();
                    ret.put("success", true);
                    ret.put("path", modelDir.getAbsolutePath());
                    ret.put("message", "Model already exists");
                    call.resolve(ret);
                    return;
                }
                
                // Download zip
                JSObject progressEvent = new JSObject();
                progressEvent.put("status", "downloading");
                progressEvent.put("model", finalName);
                notifyListeners("sttModelProgress", progressEvent);
                
                URL url = new URL(finalUrl);
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setConnectTimeout(30000);
                
                File zipFile = new File(modelsDir, finalName + ".zip");
                InputStream is = conn.getInputStream();
                FileOutputStream fos = new FileOutputStream(zipFile);
                
                byte[] buffer = new byte[8192];
                long totalSize = conn.getContentLength();
                long downloaded = 0;
                int read;
                
                while ((read = is.read(buffer)) != -1) {
                    fos.write(buffer, 0, read);
                    downloaded += read;
                    if (totalSize > 0 && downloaded % (256 * 1024) == 0) {
                        JSObject p = new JSObject();
                        p.put("progress", (int)(downloaded * 100 / totalSize));
                        p.put("downloadedMB", downloaded / (1024 * 1024));
                        notifyListeners("sttModelProgress", p);
                    }
                }
                fos.close();
                is.close();
                conn.disconnect();
                
                // Extract zip
                progressEvent = new JSObject();
                progressEvent.put("status", "extracting");
                notifyListeners("sttModelProgress", progressEvent);
                
                unzip(zipFile, modelsDir);
                zipFile.delete();
                
                // Find the extracted model directory
                File[] extracted = modelsDir.listFiles();
                String modelPath = "";
                if (extracted != null) {
                    for (File f : extracted) {
                        if (f.isDirectory() && f.getName().contains("vosk-model")) {
                            modelPath = f.getAbsolutePath();
                            break;
                        }
                    }
                }
                
                JSObject ret = new JSObject();
                ret.put("success", true);
                ret.put("path", modelPath);
                ret.put("model", finalName);
                call.resolve(ret);
                
            } catch (Exception e) {
                Log.e(TAG, "Download failed", e);
                call.reject("Download failed: " + e.getMessage());
            }
        });
    }

    /**
     * Get current status
     */
    @PluginMethod
    public void getStatus(PluginCall call) {
        JSObject ret = new JSObject();
        ret.put("modelReady", modelReady);
        ret.put("isListening", isListening);
        call.resolve(ret);
    }

    // ═══ RecognitionListener callbacks ═══

    @Override
    public void onPartialResult(String hypothesis) {
        try {
            JSONObject json = new JSONObject(hypothesis);
            String partial = json.optString("partial", "");
            if (!partial.isEmpty()) {
                JSObject event = new JSObject();
                event.put("partial", partial);
                event.put("isFinal", false);
                notifyListeners("speechResult", event);
            }
        } catch (Exception e) {
            Log.w(TAG, "Parse partial error", e);
        }
    }

    @Override
    public void onResult(String hypothesis) {
        try {
            JSONObject json = new JSONObject(hypothesis);
            String text = json.optString("text", "");
            if (!text.isEmpty()) {
                JSObject event = new JSObject();
                event.put("text", text);
                event.put("isFinal", true);
                notifyListeners("speechResult", event);
            }
        } catch (Exception e) {
            Log.w(TAG, "Parse result error", e);
        }
    }

    @Override
    public void onFinalResult(String hypothesis) {
        try {
            JSONObject json = new JSONObject(hypothesis);
            String text = json.optString("text", "");
            JSObject event = new JSObject();
            event.put("text", text);
            event.put("isFinal", true);
            event.put("isComplete", true);
            notifyListeners("speechResult", event);
        } catch (Exception e) {
            Log.w(TAG, "Parse final error", e);
        }
        isListening = false;
    }

    @Override
    public void onError(Exception exception) {
        JSObject event = new JSObject();
        event.put("error", exception.getMessage());
        notifyListeners("speechError", event);
        isListening = false;
    }

    @Override
    public void onTimeout() {
        JSObject event = new JSObject();
        event.put("text", "");
        event.put("timeout", true);
        notifyListeners("speechResult", event);
        isListening = false;
    }

    // ═══ Helpers ═══

    private void unzip(File zipFile, File destDir) throws IOException {
        ZipInputStream zis = new ZipInputStream(new java.io.FileInputStream(zipFile));
        ZipEntry entry;
        while ((entry = zis.getNextEntry()) != null) {
            File newFile = new File(destDir, entry.getName());
            if (entry.isDirectory()) {
                newFile.mkdirs();
            } else {
                newFile.getParentFile().mkdirs();
                FileOutputStream fos = new FileOutputStream(newFile);
                byte[] buf = new byte[4096];
                int len;
                while ((len = zis.read(buf)) > 0) fos.write(buf, 0, len);
                fos.close();
            }
            zis.closeEntry();
        }
        zis.close();
    }

    private long getFolderSize(File dir) {
        long size = 0;
        File[] files = dir.listFiles();
        if (files != null) {
            for (File f : files) {
                size += f.isDirectory() ? getFolderSize(f) : f.length();
            }
        }
        return size;
    }

    @Override
    protected void handleOnDestroy() {
        if (speechService != null) {
            speechService.stop();
            speechService.shutdown();
        }
        if (voskModel != null) voskModel.close();
        if (bgThread != null) bgThread.quitSafely();
    }
}
