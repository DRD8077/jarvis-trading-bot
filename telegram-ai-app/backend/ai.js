const OpenAI = require('openai');
const { GoogleGenerativeAI } = require('@google/generative-ai');
const speechSdk = require('microsoft-cognitiveservices-speech-sdk');

// Initialize AI services
let openai = null;
let gemini = null;

try {
  if (process.env.OPENAI_API_KEY) {
    openai = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY
    });
  }
} catch (error) {
  console.log('OpenAI not configured');
}

try {
  if (process.env.GOOGLE_API_KEY) {
    gemini = new GoogleGenerativeAI(process.env.GOOGLE_API_KEY);
  }
} catch (error) {
  console.log('Google Gemini not configured');
}

/**
 * JARVIS AI System Prompts
 */
const SYSTEM_PROMPTS = {
  hindi: `तुम एक प्रोफेशनल हिंदी AI असिस्टेंट हो।
तुम मानव की तरह बात करते हो।
सरल, सम्मानजनक और स्पष्ट हिंदी में जवाब दो।
तुम्हारा नाम जार्विस है और तुम उपयोगकर्ताओं की मदद करने के लिए बनाए गए हो।

नियम:
- हमेशा हिंदी में जवाब दो
- मित्रवत और सहायक रवैया रखो
- तकनीकी सवालों का सरल जवाब दो
- अगर कुछ समझ में न आए तो पूछो
- धैर्य और विनम्र रहो`,

  english: `You are JARVIS, a professional AI assistant.
You speak like a human and help users with their tasks.
Always be helpful, respectful, and clear in your responses.

Rules:
- Be friendly and supportive
- Give clear, concise answers
- Ask for clarification if needed
- Be patient and polite`
};

/**
 * Process voice input to text (Speech-to-Text)
 */
async function processVoiceQuery(audioData, language = 'hi') {
  try {
    // Option 1: Use Microsoft Azure Speech Services
    if (process.env.AZURE_SPEECH_KEY && process.env.AZURE_SPEECH_REGION) {
      return await processAzureSpeechToText(audioData, language);
    }

    // Option 2: Use OpenAI Whisper (if available)
    if (openai) {
      return await processWhisperSpeechToText(audioData, language);
    }

    // Fallback: Return placeholder (frontend handles Web Speech API)
    console.log('Voice processing not configured, using Web Speech API');
    return audioData; // Frontend should handle this

  } catch (error) {
    console.error('Voice processing error:', error);
    return 'क्षमा करें, वॉइस प्रोसेसिंग में दिक्कत हुई।';
  }
}

/**
 * Generate speech from text (Text-to-Speech)
 */
async function generateSpeech(text, language = 'hi') {
  try {
    // Option 1: Use Microsoft Azure Text-to-Speech
    if (process.env.AZURE_SPEECH_KEY && process.env.AZURE_SPEECH_REGION) {
      return await generateAzureSpeech(text, language);
    }

    // Option 2: Use Web Speech API (return text for frontend)
    return {
      type: 'web-speech-api',
      text: text,
      voice: language === 'hi' ? 'hi-IN' : 'en-US'
    };

  } catch (error) {
    console.error('Speech generation error:', error);
    return null;
  }
}

/**
 * Process gesture data and generate contextual responses
 */
async function processGestureData(gesture, confidence, poseData, userId) {
  try {
    if (confidence < 0.7) return null;

    const gestureContext = {
      gesture: gesture,
      confidence: confidence,
      pose: poseData,
      timestamp: new Date()
    };

    // Use AI to generate contextual response based on gesture
    const prompt = `User made a ${gesture} gesture with ${confidence * 100}% confidence.
    Generate a contextual, friendly response in Hindi that acknowledges this gesture and continues the conversation naturally.`;

    const response = await processAIQuery(prompt, 'hi', { telegram_id: userId });

    return {
      gesture: gesture,
      response: response,
      confidence: confidence,
      context: gestureContext
    };

  } catch (error) {
    console.error('Gesture processing error:', error);
    return null;
  }
}

/**
 * Azure Speech-to-Text implementation
 */
async function processAzureSpeechToText(audioData, language) {
  return new Promise((resolve, reject) => {
    try {
      const speechConfig = speechSdk.SpeechConfig.fromSubscription(
        process.env.AZURE_SPEECH_KEY,
        process.env.AZURE_SPEECH_REGION
      );

      speechConfig.speechRecognitionLanguage = language === 'hi' ? 'hi-IN' : 'en-US';

      const audioConfig = speechSdk.AudioConfig.fromWavFileInput(audioData);
      const recognizer = new speechSdk.SpeechRecognizer(speechConfig, audioConfig);

      recognizer.recognizeOnceAsync(result => {
        if (result.reason === speechSdk.ResultReason.RecognizedSpeech) {
          resolve(result.text);
        } else {
          resolve('वॉइस नहीं समझा गया');
        }
        recognizer.close();
      }, error => {
        console.error('Azure STT error:', error);
        reject(error);
      });

    } catch (error) {
      reject(error);
    }
  });
}

/**
 * Azure Text-to-Speech implementation
 */
async function generateAzureSpeech(text, language) {
  return new Promise((resolve, reject) => {
    try {
      const speechConfig = speechSdk.SpeechConfig.fromSubscription(
        process.env.AZURE_SPEECH_KEY,
        process.env.AZURE_SPEECH_REGION
      );

      speechConfig.speechSynthesisLanguage = language === 'hi' ? 'hi-IN' : 'en-US';
      speechConfig.speechSynthesisVoiceName = language === 'hi' ? 'hi-IN-MadhurNeural' : 'en-US-AriaNeural';

      const synthesizer = new speechSdk.SpeechSynthesizer(speechConfig);

      synthesizer.speakTextAsync(text, result => {
        if (result.reason === speechSdk.ResultReason.SynthesizingAudioCompleted) {
          resolve(result.audioData);
        } else {
          resolve(null);
        }
        synthesizer.close();
      }, error => {
        console.error('Azure TTS error:', error);
        reject(error);
      });

    } catch (error) {
      reject(error);
    }
  });
}

/**
 * OpenAI Whisper implementation
 */
async function processWhisperSpeechToText(audioData, language) {
  try {
    // Convert audio data to proper format for Whisper
    const transcription = await openai.audio.transcriptions.create({
      file: audioData,
      model: 'whisper-1',
      language: language === 'hi' ? 'hi' : 'en'
    });

    return transcription.text;
  } catch (error) {
    console.error('Whisper error:', error);
    return 'वॉइस प्रोसेसिंग विफल';
  }
}

/**
 * Fallback responses for different scenarios
 */
const FALLBACK_RESPONSES = {
  hindi: {
    greeting: [
      "नमस्ते! मैं जार्विस हूं, आपकी मदद के लिए यहां हूं 🙏",
      "हैलो! मैं आपका AI असिस्टेंट जार्विस हूं। क्या मदद चाहिए?",
      "नमस्कार! मैं जार्विस हूं। बताएं, क्या सेवा कर सकता हूं?"
    ],
    help: "मैं आपकी मदद करने के लिए हूं। आप पूछ सकते हैं:\n• मौसम की जानकारी\n• गणित के सवाल\n• सामान्य ज्ञान\n• दैनिक सहायता",
    unknown: "माफ़ कीजिए, यह सवाल मुझे समझ नहीं आया। कृपया और स्पष्ट करें।",
    error: "क्षमा करें, कुछ तकनीकी दिक्कत है। बाद में फिर से कोशिश करें।"
  },
  english: {
    greeting: [
      "Hello! I'm JARVIS, your AI assistant. How can I help you?",
      "Hi there! I'm JARVIS. What can I do for you today?",
      "Greetings! I'm JARVIS, ready to assist you."
    ],
    help: "I'm here to help you with:\n• Weather information\n• Math problems\n• General knowledge\n• Daily assistance",
    unknown: "I'm sorry, I didn't understand that. Could you please clarify?",
    error: "Sorry, there's a technical issue. Please try again later."
  }
};

/**
 * Process AI query and generate response
 * @param {string} message - User message
 * @param {string} language - Language preference ('hi' or 'en')
 * @param {object} context - Additional context (user info, chat history, etc.)
 * @returns {Promise<string>} - AI response
 */
async function processAIQuery(message, language = 'hi', context = {}) {
  try {
    const lang = language.toLowerCase();
    const isHindi = lang === 'hi' || lang === 'hindi';

    // Clean and normalize message
    const cleanMessage = message.trim().toLowerCase();

    // Handle greetings
    if (isGreeting(cleanMessage)) {
      const greetings = isHindi ? FALLBACK_RESPONSES.hindi.greeting : FALLBACK_RESPONSES.english.greeting;
      return greetings[Math.floor(Math.random() * greetings.length)];
    }

    // Handle help requests
    if (isHelpRequest(cleanMessage)) {
      return isHindi ? FALLBACK_RESPONSES.hindi.help : FALLBACK_RESPONSES.english.help;
    }

    // Try OpenAI if available
    if (openai) {
      return await getOpenAIResponse(message, isHindi, context);
    }

    // Fallback to rule-based responses
    return getRuleBasedResponse(message, isHindi);

  } catch (error) {
    console.error('AI processing error:', error);
    const isHindi = language.toLowerCase() === 'hi';
    return isHindi ? FALLBACK_RESPONSES.hindi.error : FALLBACK_RESPONSES.english.error;
  }
}

/**
 * Get response from OpenAI
 */
async function getOpenAIResponse(message, isHindi, context) {
  try {
    const systemPrompt = isHindi ? SYSTEM_PROMPTS.hindi : SYSTEM_PROMPTS.english;

    const messages = [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: message }
    ];

    // Add context if available
    if (context.previousMessages && context.previousMessages.length > 0) {
      // Add last few messages for context (max 5)
      const recentMessages = context.previousMessages.slice(-5);
      messages.splice(1, 0, ...recentMessages.map(msg => ({
        role: msg.role || 'user',
        content: msg.content
      })));
    }

    const completion = await openai.chat.completions.create({
      model: 'gpt-3.5-turbo',
      messages: messages,
      max_tokens: 500,
      temperature: 0.7,
    });

    return completion.choices[0].message.content.trim();

  } catch (error) {
    console.error('OpenAI API error:', error);
    throw error;
  }
}

/**
 * Rule-based response system (fallback)
 */
function getRuleBasedResponse(message, isHindi) {
  const msg = message.toLowerCase();

  // Weather queries
  if (msg.includes('weather') || msg.includes('मौसम')) {
    return isHindi
      ? "मौसम की जानकारी के लिए कृपया अपना शहर बताएं। मैं मौजूदा तापमान और पूर्वानुमान दे सकता हूं।"
      : "Please tell me your city for weather information. I can provide current temperature and forecast.";
  }

  // Time queries
  if (msg.includes('time') || msg.includes('समय')) {
    const now = new Date();
    return isHindi
      ? `अभी समय है: ${now.toLocaleTimeString('hi-IN')}`
      : `Current time is: ${now.toLocaleTimeString()}`;
  }

  // Math queries
  if (msg.includes('calculate') || msg.includes('गणना') || /[0-9+\-*/=]/.test(msg)) {
    return isHindi
      ? "गणित के सवालों के लिए कृपया स्पष्ट रूप से बताएं। उदाहरण: '5 + 3' या '10 का वर्ग'"
      : "For math problems, please be specific. Example: '5 + 3' or 'square of 10'";
  }

  // Default response
  return isHindi ? FALLBACK_RESPONSES.hindi.unknown : FALLBACK_RESPONSES.english.unknown;
}

/**
 * Check if message is a greeting
 */
function isGreeting(message) {
  const greetings = [
    'hello', 'hi', 'hey', 'नमस्ते', 'नमस्कार', 'हैलो', 'हाय',
    'good morning', 'good afternoon', 'good evening',
    'सुप्रभात', 'शुभ दोपहर', 'शुभ संध्या'
  ];

  return greetings.some(greeting => message.includes(greeting));
}

/**
 * Check if message is a help request
 */
function isHelpRequest(message) {
  const helpWords = [
    'help', 'मदद', 'सहायता', 'क्या कर सकते हो',
    'what can you do', 'capabilities', 'features'
  ];

  return helpWords.some(word => message.includes(word));
}

/**
 * Analyze sentiment of message (basic)
 */
function analyzeSentiment(message) {
  const positiveWords = ['good', 'great', 'awesome', 'thanks', 'thank you', 'अच्छा', 'धन्यवाद', 'शुक्रिया'];
  const negativeWords = ['bad', 'terrible', 'awful', 'sorry', 'क्षमा', 'माफ़'];

  const lowerMsg = message.toLowerCase();
  const positiveCount = positiveWords.filter(word => lowerMsg.includes(word)).length;
  const negativeCount = negativeWords.filter(word => lowerMsg.includes(word)).length;

  if (positiveCount > negativeCount) return 'positive';
  if (negativeCount > positiveCount) return 'negative';
  return 'neutral';
}

/**
 * Generate contextual response based on user history
 */
function generateContextualResponse(message, userHistory = []) {
  if (userHistory.length === 0) return null;

  // Analyze conversation patterns
  const recentTopics = userHistory.slice(-3).map(h => h.message.toLowerCase());

  // If user has been asking about weather, offer forecast
  if (recentTopics.some(msg => msg.includes('weather') || msg.includes('मौसम'))) {
    return "क्या आप मौसम के बारे में और जानना चाहेंगे? जैसे बारिश का पूर्वानुमान या हवा की दिशा?";
  }

  return null;
}

/**
 * Voice-to-text processing (placeholder for future enhancement)
 */
function processVoiceInput(audioData) {
  // This would integrate with speech-to-text services
  // For now, return placeholder
  return {
    text: "Voice input processing not implemented yet",
    confidence: 0.0
  };
}

/**
 * Text-to-speech preparation (placeholder)
 */
function prepareSpeechResponse(text, language = 'hi') {
  return {
    text: text,
    language: language,
    voice: language === 'hi' ? 'hi-IN' : 'en-US'
  };
}

/**
 * Emotion Detection System
 * Analyzes voice tone, face expressions, and text patterns to detect emotions
 */

/**
 * Analyze voice tone for emotion detection
 */
async function analyzeVoiceEmotion(audioData, language = 'hi') {
  try {
    // Extract audio features (pitch, volume, speed, etc.)
    const audioFeatures = await extractAudioFeatures(audioData);

    // Use AI to analyze emotional content from voice
    const emotionPrompt = `Analyze the following voice audio features and determine the primary emotion:
    Features: ${JSON.stringify(audioFeatures)}
    Language: ${language}

    Return a JSON object with emotion probabilities:
    {
      "happy": 0.0-1.0,
      "sad": 0.0-1.0,
      "angry": 0.0-1.0,
      "neutral": 0.0-1.0,
      "excited": 0.0-1.0,
      "confused": 0.0-1.0
    }`;

    const analysis = await processAIQuery(emotionPrompt, 'en', { system: true });

    try {
      return JSON.parse(analysis);
    } catch (parseError) {
      // Fallback emotion detection based on basic features
      return fallbackVoiceEmotionDetection(audioFeatures);
    }

  } catch (error) {
    console.error('Voice emotion analysis error:', error);
    return { neutral: 1.0, happy: 0, sad: 0, angry: 0, excited: 0, confused: 0 };
  }
}

/**
 * Extract basic audio features for emotion analysis
 */
async function extractAudioFeatures(audioData) {
  // In a real implementation, this would use libraries like librosa or speechbrain
  // For now, return simulated features
  return {
    pitch: Math.random() * 200 + 80, // Hz
    volume: Math.random() * 0.8 + 0.2, // 0-1
    speed: Math.random() * 0.5 + 0.8, // relative to normal
    energy: Math.random() * 0.9 + 0.1, // 0-1
    duration: Math.random() * 5 + 1, // seconds
    pauses: Math.floor(Math.random() * 5), // number of pauses
    tone: ['high', 'medium', 'low'][Math.floor(Math.random() * 3)]
  };
}

/**
 * Fallback voice emotion detection based on basic features
 */
function fallbackVoiceEmotionDetection(features) {
  let emotions = { happy: 0.1, sad: 0.1, angry: 0.1, neutral: 0.5, excited: 0.1, confused: 0.1 };

  // High pitch and volume often indicates excitement or anger
  if (features.pitch > 150 && features.volume > 0.6) {
    emotions.excited = 0.4;
    emotions.angry = 0.3;
    emotions.neutral = 0.3;
  }

  // Low pitch and volume might indicate sadness
  if (features.pitch < 100 && features.volume < 0.4) {
    emotions.sad = 0.5;
    emotions.neutral = 0.3;
  }

  // High energy with normal pitch might indicate happiness
  if (features.energy > 0.7 && features.pitch > 100 && features.pitch < 150) {
    emotions.happy = 0.4;
    emotions.excited = 0.3;
    emotions.neutral = 0.3;
  }

  return emotions;
}

/**
 * Analyze face expressions for emotion detection
 */
async function analyzeFaceEmotion(faceData, landmarks) {
  try {
    // Analyze facial landmarks and expressions
    const facialFeatures = extractFacialFeatures(landmarks);

    // Use AI to analyze emotional content from face
    const emotionPrompt = `Analyze the following facial features and determine the primary emotion:
    Features: ${JSON.stringify(facialFeatures)}

    Return a JSON object with emotion probabilities:
    {
      "happy": 0.0-1.0,
      "sad": 0.0-1.0,
      "angry": 0.0-1.0,
      "neutral": 0.0-1.0,
      "surprised": 0.0-1.0,
      "disgusted": 0.0-1.0
    }`;

    const analysis = await processAIQuery(emotionPrompt, 'en', { system: true });

    try {
      return JSON.parse(analysis);
    } catch (parseError) {
      // Fallback emotion detection based on facial features
      return fallbackFaceEmotionDetection(facialFeatures);
    }

  } catch (error) {
    console.error('Face emotion analysis error:', error);
    return { neutral: 1.0, happy: 0, sad: 0, angry: 0, surprised: 0, disgusted: 0 };
  }
}

/**
 * Extract facial features from landmarks
 */
function extractFacialFeatures(landmarks) {
  // In a real implementation, this would analyze specific facial landmark positions
  // For now, return simulated features
  return {
    mouthCurvature: Math.random() * 2 - 1, // -1 (frown) to 1 (smile)
    eyeOpenness: Math.random() * 0.8 + 0.2, // 0-1
    eyebrowRaise: Math.random() * 0.6, // 0-0.6
    noseWrinkle: Math.random() * 0.4, // 0-0.4
    jawTension: Math.random() * 0.7, // 0-0.7
    asymmetry: Math.random() * 0.3 // 0-0.3 (facial symmetry)
  };
}

/**
 * Fallback face emotion detection based on facial features
 */
function fallbackFaceEmotionDetection(features) {
  let emotions = { happy: 0.1, sad: 0.1, angry: 0.1, neutral: 0.5, surprised: 0.1, disgusted: 0.1 };

  // High mouth curvature indicates happiness
  if (features.mouthCurvature > 0.5) {
    emotions.happy = 0.6;
    emotions.neutral = 0.2;
    emotions.surprised = 0.2;
  }

  // Low mouth curvature indicates sadness
  if (features.mouthCurvature < -0.3) {
    emotions.sad = 0.5;
    emotions.neutral = 0.3;
    emotions.angry = 0.2;
  }

  // High eyebrow raise and eye openness indicates surprise
  if (features.eyebrowRaise > 0.4 && features.eyeOpenness > 0.7) {
    emotions.surprised = 0.5;
    emotions.neutral = 0.3;
    emotions.happy = 0.2;
  }

  // Nose wrinkle and jaw tension indicates anger or disgust
  if (features.noseWrinkle > 0.2 && features.jawTension > 0.4) {
    emotions.angry = 0.4;
    emotions.disgusted = 0.3;
    emotions.neutral = 0.3;
  }

  return emotions;
}

/**
 * Analyze text patterns for emotion detection
 */
async function analyzeTextEmotion(text, language = 'hi') {
  try {
    // Use AI to analyze emotional content from text
    const emotionPrompt = `Analyze the emotional content of this text and return emotion probabilities:
    Text: "${text}"
    Language: ${language}

    Consider:
    - Positive/negative sentiment
    - Emotional intensity
    - Cultural context (especially for Hindi text)

    Return a JSON object with emotion probabilities:
    {
      "happy": 0.0-1.0,
      "sad": 0.0-1.0,
      "angry": 0.0-1.0,
      "neutral": 0.0-1.0,
      "excited": 0.0-1.0,
      "worried": 0.0-1.0,
      "confused": 0.0-1.0
    }`;

    const analysis = await processAIQuery(emotionPrompt, 'en', { system: true });

    try {
      return JSON.parse(analysis);
    } catch (parseError) {
      // Fallback text emotion detection
      return fallbackTextEmotionDetection(text, language);
    }

  } catch (error) {
    console.error('Text emotion analysis error:', error);
    return { neutral: 1.0, happy: 0, sad: 0, angry: 0, excited: 0, worried: 0, confused: 0 };
  }
}

/**
 * Fallback text emotion detection using keyword analysis
 */
function fallbackTextEmotionDetection(text, language) {
  const lowerText = text.toLowerCase();

  let emotions = { happy: 0.1, sad: 0.1, angry: 0.1, neutral: 0.5, excited: 0.1, worried: 0.1, confused: 0.1 };

  // Define emotion keywords for both Hindi and English
  const emotionKeywords = {
    happy: ['खुश', 'happy', 'great', 'awesome', 'excellent', 'wonderful', 'fantastic', '😊', '😂', '😄'],
    sad: ['दुखी', 'sad', 'unhappy', 'depressed', 'sorry', 'upset', '😢', '😭', '😔'],
    angry: ['गुस्सा', 'angry', 'mad', 'furious', 'annoyed', 'irritated', '😠', '😡', '💢'],
    excited: ['उत्तेजित', 'excited', 'thrilled', 'pumped', 'wow', 'amazing', 'incredible', '🤩', '😍'],
    worried: ['चिंतित', 'worried', 'concerned', 'anxious', 'nervous', 'scared', '😰', '😨'],
    confused: ['confused', 'puzzled', 'bewildered', 'lost', 'unsure', '🤔', '😕']
  };

  // Count emotion keywords
  let totalMatches = 0;
  Object.entries(emotionKeywords).forEach(([emotion, keywords]) => {
    const matches = keywords.filter(keyword => lowerText.includes(keyword)).length;
    if (matches > 0) {
      emotions[emotion] += matches * 0.2; // Weight each match
      totalMatches += matches;
    }
  });

  // Normalize if we found emotion keywords
  if (totalMatches > 0) {
    const total = Object.values(emotions).reduce((sum, val) => sum + val, 0);
    Object.keys(emotions).forEach(key => {
      emotions[key] = emotions[key] / total;
    });
  }

  return emotions;
}

/**
 * Combine multiple emotion sources for final emotion detection
 */
function combineEmotions(voiceEmotions, faceEmotions, textEmotions, weights = {}) {
  const defaultWeights = {
    voice: 0.4,    // Voice tone is very reliable
    face: 0.4,     // Facial expressions are very reliable
    text: 0.2      // Text can be ambiguous
  };

  const finalWeights = { ...defaultWeights, ...weights };

  const combinedEmotions = {};

  // Get all emotion types
  const allEmotions = new Set([
    ...Object.keys(voiceEmotions || {}),
    ...Object.keys(faceEmotions || {}),
    ...Object.keys(textEmotions || {})
  ]);

  // Combine emotions with weights
  allEmotions.forEach(emotion => {
    const voiceVal = (voiceEmotions && voiceEmotions[emotion]) || 0;
    const faceVal = (faceEmotions && faceEmotions[emotion]) || 0;
    const textVal = (textEmotions && textEmotions[emotion]) || 0;

    combinedEmotions[emotion] = (
      voiceVal * finalWeights.voice +
      faceVal * finalWeights.face +
      textVal * finalWeights.text
    );
  });

  // Normalize to ensure sum equals 1
  const total = Object.values(combinedEmotions).reduce((sum, val) => sum + val, 0);
  if (total > 0) {
    Object.keys(combinedEmotions).forEach(key => {
      combinedEmotions[key] = combinedEmotions[key] / total;
    });
  }

  return combinedEmotions;
}

/**
 * Get dominant emotion from emotion probabilities
 */
function getDominantEmotion(emotions) {
  if (!emotions || Object.keys(emotions).length === 0) {
    return 'neutral';
  }

  return Object.entries(emotions).reduce((max, [emotion, probability]) =>
    probability > max.probability ? { emotion, probability } : max,
    { emotion: 'neutral', probability: 0 }
  ).emotion;
}

/**
 * Generate emotion-aware response
 */
async function generateEmotionResponse(dominantEmotion, userMessage, language = 'hi', context = {}) {
  try {
    const emotionResponses = {
      happy: {
        hi: "आप इतने खुश दिख रहे हैं! 😊 यह बहुत अच्छा है। क्या आप इस खुशी को और बांटना चाहेंगे?",
        en: "You look so happy! 😊 That's wonderful. Would you like to share what's making you smile?"
      },
      sad: {
        hi: "आप दुखी लग रहे हैं। 😔 क्या मैं आपकी कोई मदद कर सकता हूं? कृपया बताएं।",
        en: "You seem sad. 😔 Can I help you with anything? Please tell me what's bothering you."
      },
      angry: {
        hi: "आप गुस्से में दिख रहे हैं। 😠 क्या कुछ गलत हुआ है? मैं आपकी मदद करने के लिए यहां हूं।",
        en: "You seem angry. 😠 Did something go wrong? I'm here to help you."
      },
      excited: {
        hi: "वाह! आप बहुत उत्साहित दिख रहे हैं! 🤩 क्या कोई अच्छी खबर है?",
        en: "Wow! You look so excited! 🤩 Is there some good news?"
      },
      worried: {
        hi: "आप चिंतित लग रहे हैं। 😰 क्या कोई समस्या है? मैं आपकी मदद कर सकता हूं।",
        en: "You look worried. 😰 Is there a problem? I can help you."
      },
      confused: {
        hi: "आप उलझन में दिख रहे हैं। 🤔 क्या आप स्पष्ट करना चाहेंगे कि क्या समझ में नहीं आया?",
        en: "You look confused. 🤔 Would you like to clarify what you don't understand?"
      },
      neutral: {
        hi: "ठीक है, मैं आपकी मदद करने के लिए तैयार हूं।",
        en: "Alright, I'm ready to help you."
      }
    };

    // Get appropriate response
    const responses = emotionResponses[dominantEmotion] || emotionResponses.neutral;
    const baseResponse = responses[language] || responses.en;

    // If emotion is strong, use the emotion-aware response
    if (context.emotionConfidence > 0.6) {
      return baseResponse;
    }

    // Otherwise, proceed with normal AI processing
    return null;

  } catch (error) {
    console.error('Emotion response generation error:', error);
    return null;
  }
}

module.exports = {
  processAIQuery,
  analyzeSentiment,
  generateContextualResponse,
  processVoiceInput,
  prepareSpeechResponse,
  processVoiceQuery,
  generateSpeech,
  processGestureData,
  analyzeVoiceEmotion,
  analyzeFaceEmotion,
  analyzeTextEmotion,
  combineEmotions,
  getDominantEmotion,
  generateEmotionResponse,
  SYSTEM_PROMPTS,
  FALLBACK_RESPONSES
};