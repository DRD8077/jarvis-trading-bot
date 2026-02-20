package com.jarvis.trading.plugins;

import android.content.Context;
import android.os.Bundle;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;
import android.speech.tts.Voice;
import android.util.Log;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

import java.util.HashMap;
import java.util.Locale;
import java.util.Set;
import java.util.UUID;

/**
 * 🔊 LocalTTSPlugin — Capacitor Plugin for Offline Text-to-Speech
 * 
 * Uses Android's built-in TextToSpeech engine (offline voices available).
 * Supports Hindi (hi-IN), English (en-IN, en-US), and mixed language.
 * 
 * Features:
 * - Offline TTS (no internet needed if offline voice packs downloaded)
 * - Multiple languages (Hindi, English, Hinglish)
 * - Speed & pitch control
 * - Queue management
 * - Speaking events (start, done, error)
 */
@CapacitorPlugin(name = "LocalTTS")
public class LocalTTSPlugin extends Plugin implements TextToSpeech.OnInitListener {
    private static final String TAG = "LocalTTS";
    
    private TextToSpeech tts;
    private boolean ttsReady = false;
    private boolean isSpeaking = false;
    private float speechRate = 1.0f;
    private float pitch = 1.0f;
    private String currentLanguage = "hi-IN";
    private HashMap<String, PluginCall> pendingCalls = new HashMap<>();

    @Override
    public void load() {
        tts = new TextToSpeech(getContext(), this);
        Log.i(TAG, "LocalTTS Plugin loaded");
    }

    @Override
    public void onInit(int status) {
        if (status == TextToSpeech.SUCCESS) {
            // Try Hindi first, fallback to English
            int result = tts.setLanguage(new Locale("hi", "IN"));
            if (result == TextToSpeech.LANG_MISSING_DATA || result == TextToSpeech.LANG_NOT_SUPPORTED) {
                result = tts.setLanguage(new Locale("en", "IN"));
                if (result == TextToSpeech.LANG_MISSING_DATA || result == TextToSpeech.LANG_NOT_SUPPORTED) {
                    tts.setLanguage(Locale.US);
                    currentLanguage = "en-US";
                } else {
                    currentLanguage = "en-IN";
                }
            } else {
                currentLanguage = "hi-IN";
            }
            
            tts.setSpeechRate(speechRate);
            tts.setPitch(pitch);
            
            // Set utterance listener
            tts.setOnUtteranceProgressListener(new UtteranceProgressListener() {
                @Override
                public void onStart(String utteranceId) {
                    isSpeaking = true;
                    JSObject event = new JSObject();
                    event.put("utteranceId", utteranceId);
                    event.put("status", "started");
                    notifyListeners("ttsEvent", event);
                }

                @Override
                public void onDone(String utteranceId) {
                    isSpeaking = false;
                    JSObject event = new JSObject();
                    event.put("utteranceId", utteranceId);
                    event.put("status", "done");
                    notifyListeners("ttsEvent", event);
                    
                    // Resolve pending call if exists
                    PluginCall pendingCall = pendingCalls.remove(utteranceId);
                    if (pendingCall != null) {
                        JSObject ret = new JSObject();
                        ret.put("success", true);
                        ret.put("utteranceId", utteranceId);
                        pendingCall.resolve(ret);
                    }
                }

                @Override
                public void onError(String utteranceId) {
                    isSpeaking = false;
                    JSObject event = new JSObject();
                    event.put("utteranceId", utteranceId);
                    event.put("status", "error");
                    notifyListeners("ttsEvent", event);
                    
                    PluginCall pendingCall = pendingCalls.remove(utteranceId);
                    if (pendingCall != null) {
                        pendingCall.reject("TTS error for utterance: " + utteranceId);
                    }
                }
            });
            
            ttsReady = true;
            Log.i(TAG, "TTS initialized. Language: " + currentLanguage);
        } else {
            Log.e(TAG, "TTS init failed with status: " + status);
        }
    }

    /**
     * Speak text aloud
     */
    @PluginMethod
    public void speak(PluginCall call) {
        if (!ttsReady) {
            call.reject("TTS not initialized yet");
            return;
        }

        String text = call.getString("text", "");
        boolean queue = call.getBoolean("queue", false);
        boolean waitForComplete = call.getBoolean("waitForComplete", false);
        String lang = call.getString("language", "");
        Float rate = call.getFloat("rate", speechRate);
        Float pitchVal = call.getFloat("pitch", pitch);

        if (text.isEmpty()) {
            call.reject("Text cannot be empty");
            return;
        }

        // Set language if specified
        if (!lang.isEmpty()) {
            setTTSLanguage(lang);
        }

        tts.setSpeechRate(rate);
        tts.setPitch(pitchVal);

        String utteranceId = UUID.randomUUID().toString();
        Bundle params = new Bundle();
        params.putString(TextToSpeech.Engine.KEY_PARAM_UTTERANCE_ID, utteranceId);
        
        int queueMode = queue ? TextToSpeech.QUEUE_ADD : TextToSpeech.QUEUE_FLUSH;
        
        if (waitForComplete) {
            pendingCalls.put(utteranceId, call);
            tts.speak(text, queueMode, params, utteranceId);
        } else {
            tts.speak(text, queueMode, params, utteranceId);
            JSObject ret = new JSObject();
            ret.put("success", true);
            ret.put("utteranceId", utteranceId);
            call.resolve(ret);
        }
    }

    /**
     * Stop current speech
     */
    @PluginMethod
    public void stop(PluginCall call) {
        if (tts != null) {
            tts.stop();
        }
        isSpeaking = false;
        pendingCalls.clear();
        
        JSObject ret = new JSObject();
        ret.put("success", true);
        call.resolve(ret);
    }

    /**
     * Set language for TTS
     */
    @PluginMethod
    public void setLanguage(PluginCall call) {
        String lang = call.getString("language", "hi-IN");
        
        if (!ttsReady) {
            call.reject("TTS not ready");
            return;
        }

        setTTSLanguage(lang);
        currentLanguage = lang;
        
        JSObject ret = new JSObject();
        ret.put("success", true);
        ret.put("language", lang);
        call.resolve(ret);
    }

    /**
     * Get available voices and languages
     */
    @PluginMethod
    public void getVoices(PluginCall call) {
        if (!ttsReady) {
            call.reject("TTS not ready");
            return;
        }

        JSObject ret = new JSObject();
        org.json.JSONArray voiceList = new org.json.JSONArray();
        
        try {
            Set<Voice> voices = tts.getVoices();
            if (voices != null) {
                for (Voice voice : voices) {
                    JSObject v = new JSObject();
                    v.put("name", voice.getName());
                    v.put("locale", voice.getLocale().toString());
                    v.put("language", voice.getLocale().getLanguage());
                    v.put("country", voice.getLocale().getCountry());
                    v.put("quality", voice.getQuality());
                    v.put("networkRequired", voice.isNetworkConnectionRequired());
                    v.put("latency", voice.getLatency());
                    voiceList.put(v);
                }
            }
        } catch (Exception e) {
            Log.w(TAG, "Failed to get voices: " + e.getMessage());
        }
        
        ret.put("voices", voiceList);
        ret.put("currentLanguage", currentLanguage);
        ret.put("isSpeaking", isSpeaking);
        call.resolve(ret);
    }

    /**
     * Set speech rate
     */
    @PluginMethod
    public void setRate(PluginCall call) {
        speechRate = call.getFloat("rate", 1.0f);
        if (tts != null) tts.setSpeechRate(speechRate);
        
        JSObject ret = new JSObject();
        ret.put("rate", speechRate);
        call.resolve(ret);
    }

    /**
     * Set pitch
     */
    @PluginMethod
    public void setPitch(PluginCall call) {
        pitch = call.getFloat("pitch", 1.0f);
        if (tts != null) tts.setPitch(pitch);
        
        JSObject ret = new JSObject();
        ret.put("pitch", pitch);
        call.resolve(ret);
    }

    /**
     * Get current status
     */
    @PluginMethod
    public void getStatus(PluginCall call) {
        JSObject ret = new JSObject();
        ret.put("ready", ttsReady);
        ret.put("speaking", isSpeaking);
        ret.put("language", currentLanguage);
        ret.put("rate", speechRate);
        ret.put("pitch", pitch);
        call.resolve(ret);
    }

    // ═══ Helpers ═══

    private void setTTSLanguage(String lang) {
        if (tts == null) return;
        switch (lang) {
            case "hi-IN":
            case "hi":
                tts.setLanguage(new Locale("hi", "IN"));
                break;
            case "en-IN":
                tts.setLanguage(new Locale("en", "IN"));
                break;
            case "en-US":
            case "en":
                tts.setLanguage(Locale.US);
                break;
            default:
                String[] parts = lang.split("-");
                if (parts.length == 2) {
                    tts.setLanguage(new Locale(parts[0], parts[1]));
                } else {
                    tts.setLanguage(new Locale(lang));
                }
                break;
        }
    }

    @Override
    protected void handleOnDestroy() {
        if (tts != null) {
            tts.stop();
            tts.shutdown();
        }
    }
}
