require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const path = require('path');
const http = require('http');
const socketIo = require('socket.io');
const jwt = require('jsonwebtoken');

// Import modules
const { connectDB, User, Chat, Payment, Session } = require('./db');
const { verifyTelegramAuth, generateJWT, authenticateToken } = require('./auth');
const { processAIQuery, processVoiceQuery, generateSpeech } = require('./ai');

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
  cors: {
    origin: [
      'https://web.telegram.org',
      'https://telegram.me',
      /^https:\/\/.*\.telegram\.org$/,
      /^https:\/\/.*\.t\.me$/,
      'http://localhost:3000',
      'http://localhost:8080',
      process.env.FRONTEND_URL
    ].filter(Boolean),
    methods: ["GET", "POST"],
    credentials: true
  }
});

const PORT = process.env.PORT || 3000;

// Security middleware
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "'unsafe-inline'", "https://telegram.org"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", "data:", "https:"],
      connectSrc: ["'self'", "https://api.openai.com"],
    },
  },
}));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: {
    success: false,
    message: 'Too many requests from this IP, please try again later.'
  }
});

app.use(limiter);

// CORS configuration
app.use(cors({
  origin: function (origin, callback) {
    // Allow requests from Telegram Web Apps and localhost for development
    const allowedOrigins = [
      'https://web.telegram.org',
      'https://telegram.me',
      /^https:\/\/.*\.telegram\.org$/,
      /^https:\/\/.*\.t\.me$/,
      'http://localhost:3000',
      'http://localhost:8080',
      process.env.FRONTEND_URL
    ].filter(Boolean);

    // Allow requests with no origin (mobile apps, etc.)
    if (!origin) return callback(null, true);

    const isAllowed = allowedOrigins.some(allowedOrigin => {
      if (typeof allowedOrigin === 'string') {
        return allowedOrigin === origin;
      }
      return allowedOrigin.test(origin);
    });

    if (isAllowed) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true
}));

// Ngrok skip browser warning header (for free ngrok accounts)
app.use((req, res, next) => {
  res.setHeader('ngrok-skip-browser-warning', 'true');
  next();
});

// Body parsing middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Static files
app.use(express.static(path.join(__dirname, '../telegram-mini-app/dist')));

// Socket.IO connection handling
io.on('connection', (socket) => {
  console.log('🔗 User connected:', socket.id);

  // Authenticate socket connection
  socket.on('authenticate', async (data) => {
    try {
      const { token } = data;
      const decoded = jwt.verify(token, process.env.JWT_SECRET);
      socket.userId = decoded.telegram_id;
      socket.authenticated = true;
      socket.emit('authenticated', { success: true });
    } catch (error) {
      socket.emit('authenticated', { success: false, message: 'Invalid token' });
    }
  });

  // Live voice chat
  socket.on('voice-message', async (data) => {
    if (!socket.authenticated) return;

    try {
      const { audioData, language = 'hi' } = data;

      // Process voice to text (placeholder - integrate with Whisper later)
      const text = await processVoiceQuery(audioData, language);

      // Get AI response
      const aiResponse = await processAIQuery(text, language, {
        telegram_id: socket.userId,
        socket: socket
      });

      // Generate speech from AI response
      const audioResponse = await generateSpeech(aiResponse, language);

      // Send back to client
      socket.emit('ai-response', {
        text: aiResponse,
        audio: audioResponse,
        language
      });

    } catch (error) {
      socket.emit('error', { message: 'Voice processing failed' });
    }
  });

  // Gesture recognition
  socket.on('gesture-data', async (data) => {
    if (!socket.authenticated) return;

    try {
      const { gesture, confidence, poseData } = data;

      // Process gesture data
      const gestureResponse = await processGesture(gesture, confidence, poseData, socket.userId);

      if (gestureResponse) {
        socket.emit('gesture-response', gestureResponse);
      }

    } catch (error) {
      console.error('Gesture processing error:', error);
    }
  });

  // Real-time chat
  socket.on('chat-message', async (data) => {
    if (!socket.authenticated) return;

    try {
      const { message, language = 'hi' } = data;

      // Process AI query
      const response = await processAIQuery(message, language, {
        telegram_id: socket.userId,
        socket: socket
      });

      socket.emit('chat-response', {
        message: response,
        language
      });

    } catch (error) {
      socket.emit('error', { message: 'Chat processing failed' });
    }
  });

  // Emotion detection
  socket.on('emotion-data', async (data) => {
    if (!socket.authenticated) return;

    try {
      const { voiceData, faceData, text, language = 'hi' } = data;

      const {
        analyzeVoiceEmotion,
        analyzeFaceEmotion,
        analyzeTextEmotion,
        combineEmotions,
        getDominantEmotion,
        generateEmotionResponse
      } = require('./ai');

      // Analyze each input type
      const voiceEmotions = voiceData ? await analyzeVoiceEmotion(voiceData, language) : null;
      const faceEmotions = faceData ? await analyzeFaceEmotion(faceData, faceData.landmarks) : null;
      const textEmotions = text ? await analyzeTextEmotion(text, language) : null;

      // Combine emotions
      const combinedEmotions = combineEmotions(voiceEmotions, faceEmotions, textEmotions);
      const dominantEmotion = getDominantEmotion(combinedEmotions);

      // Generate emotion-aware response if text is provided
      let emotionResponse = null;
      if (text) {
        emotionResponse = await generateEmotionResponse(dominantEmotion, text, language, {
          emotionConfidence: Math.max(...Object.values(combinedEmotions))
        });
      }

      const emotionResult = {
        emotions: combinedEmotions,
        dominantEmotion,
        confidence: Math.max(...Object.values(combinedEmotions)),
        sources: {
          voice: !!voiceEmotions,
          face: !!faceEmotions,
          text: !!textEmotions
        },
        response: emotionResponse,
        timestamp: new Date()
      };

      // Send to user
      socket.emit('emotion-result', emotionResult);

      // Broadcast to admin panel
      io.emit('emotion-data', {
        userId: socket.userId,
        ...emotionResult
      });

    } catch (error) {
      console.error('Emotion processing error:', error);
      socket.emit('error', { message: 'Emotion analysis failed' });
    }
  });

  // Admin emotion updates
  socket.on('emotion-update', async (data) => {
    // This is sent from admin panel to update emotion data
    io.emit('emotion-data', data);
  });

  socket.on('disconnect', () => {
    console.log('❌ User disconnected:', socket.id);
  });
});

// Gesture processing function
async function processGesture(gesture, confidence, poseData, userId) {
  if (confidence < 0.7) return null; // Low confidence

  const gestureResponses = {
    'wave': 'नमस्ते! आपने हाथ हिलाया!',
    'thumbs_up': '👍 बढ़िया! आप सहमत हैं!',
    'pointing': '👆 आप क्या दिखा रहे हैं?',
    'nod': '🙂 आप सहमत हैं!',
    'shake_head': '🙁 आप असहमत हैं?',
    'clap': '👏 वाह! बहुत बढ़िया!',
    'raise_hand': '🙋 आप कुछ पूछना चाहते हैं?'
  };

  const response = gestureResponses[gesture];
  if (response) {
    // Save gesture interaction
    await Chat.create({
      telegram_id: userId,
      message: `Gesture: ${gesture}`,
      reply: response,
      message_type: 'gesture'
    });

    return {
      gesture,
      response,
      confidence
    };
  }

  return null;
}

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    success: true,
    message: 'JARVIS AI App is running',
    timestamp: new Date().toISOString(),
    version: '1.0.0'
  });
});

// Telegram authentication endpoint
app.post('/auth/verify', async (req, res) => {
  try {
    const { initData } = req.body;

    if (!initData) {
      return res.status(400).json({
        success: false,
        message: 'initData is required'
      });
    }

    const botToken = process.env.BOT_TOKEN;
    if (!botToken) {
      return res.status(500).json({
        success: false,
        message: 'Server configuration error'
      });
    }

    // Verify Telegram authentication
    const userData = verifyTelegramAuth(initData, botToken);

    if (!userData) {
      return res.status(401).json({
        success: false,
        message: 'Invalid authentication data'
      });
    }

    // Check if user exists, create if not
    let user = await User.findOne({ telegram_id: userData.id });

    if (!user) {
      user = new User({
        telegram_id: userData.id,
        name: `${userData.first_name} ${userData.last_name || ''}`.trim(),
        username: userData.username,
        language: userData.language_code === 'hi' ? 'hi' : 'en',
        settings: {
          voice_enabled: true,
          notifications: true,
          theme: 'auto'
        }
      });
      await user.save();
    } else {
      // Update last active
      user.last_active = new Date();
      await user.save();
    }

    // Generate JWT token
    const token = generateJWT(userData);

    res.json({
      success: true,
      message: 'Authentication successful',
      user: {
        id: user.telegram_id,
        name: user.name,
        username: user.username,
        language: user.language,
        is_premium: user.is_premium,
        settings: user.settings
      },
      token: token
    });

  } catch (error) {
    console.error('Auth verification error:', error);
    res.status(500).json({
      success: false,
      message: 'Authentication failed'
    });
  }
});

// AI chat endpoint
app.post('/ai/chat', authenticateToken, async (req, res) => {
  try {
    const { message, language = 'hi' } = req.body;
    const telegramId = req.user.telegram_id;

    if (!message || message.trim().length === 0) {
      return res.status(400).json({
        success: false,
        message: 'Message is required'
      });
    }

    // Get user context
    const user = await User.findOne({ telegram_id: telegramId });
    if (!user) {
      return res.status(404).json({
        success: false,
        message: 'User not found'
      });
    }

    // Get recent chat history for context (last 5 messages)
    const recentChats = await Chat.find({ telegram_id: telegramId })
      .sort({ timestamp: -1 })
      .limit(5)
      .select('message reply')
      .lean();

    const context = {
      previousMessages: recentChats.reverse().map(chat => [
        { role: 'user', content: chat.message },
        { role: 'assistant', content: chat.reply }
      ]).flat()
    };

    // Start timing
    const startTime = Date.now();

    // Process AI query
    const reply = await processAIQuery(message, language, context);

    // Calculate response time
    const responseTime = Date.now() - startTime;

    // Save chat to database
    const chatEntry = new Chat({
      telegram_id: telegramId,
      message: message.trim(),
      reply: reply,
      message_type: 'text',
      ai_model: 'jarvis-hindi',
      response_time: responseTime
    });

    await chatEntry.save();

    res.json({
      success: true,
      reply: reply,
      response_time: responseTime,
      language: language
    });

  } catch (error) {
    console.error('AI chat error:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to process AI request',
      reply: user.language === 'hi' ?
        'क्षमा करें, कुछ तकनीकी दिक्कत है। बाद में फिर से कोशिश करें।' :
        'Sorry, there\'s a technical issue. Please try again later.'
    });
  }
});

// Voice input endpoint
app.post('/ai/voice', authenticateToken, async (req, res) => {
  try {
    const { audioData, language = 'hi' } = req.body;
    const telegramId = req.user.telegram_id;

    // TODO: Implement speech-to-text processing
    // For now, return placeholder response

    const reply = language === 'hi' ?
      'आवाज़ इनपुट अभी कार्यान्वयनाधीन है। कृपया टेक्स्ट का उपयोग करें।' :
      'Voice input is currently under development. Please use text input.';

    res.json({
      success: true,
      reply: reply,
      language: language,
      voice_processed: false
    });

  } catch (error) {
    console.error('Voice processing error:', error);
    res.status(500).json({
      success: false,
      message: 'Voice processing failed'
    });
  }
});

// Get user profile
app.get('/user/profile', authenticateToken, async (req, res) => {
  try {
    const telegramId = req.user.telegram_id;

    const user = await User.findOne({ telegram_id: telegramId });
    if (!user) {
      return res.status(404).json({
        success: false,
        message: 'User not found'
      });
    }

    res.json({
      success: true,
      user: {
        id: user.telegram_id,
        name: user.name,
        username: user.username,
        language: user.language,
        is_premium: user.is_premium,
        subscription_end: user.subscription_end,
        created_at: user.created_at,
        last_active: user.last_active,
        settings: user.settings
      }
    });

  } catch (error) {
    console.error('Get profile error:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to get user profile'
    });
  }
});

// Update user settings
app.put('/user/settings', authenticateToken, async (req, res) => {
  try {
    const telegramId = req.user.telegram_id;
    const { settings } = req.body;

    if (!settings || typeof settings !== 'object') {
      return res.status(400).json({
        success: false,
        message: 'Settings object is required'
      });
    }

    const user = await User.findOne({ telegram_id: telegramId });
    if (!user) {
      return res.status(404).json({
        success: false,
        message: 'User not found'
      });
    }

    // Update only allowed settings
    const allowedSettings = ['voice_enabled', 'notifications', 'theme'];
    allowedSettings.forEach(setting => {
      if (settings[setting] !== undefined) {
        user.settings[setting] = settings[setting];
      }
    });

    await user.save();

    res.json({
      success: true,
      message: 'Settings updated successfully',
      settings: user.settings
    });

  } catch (error) {
    console.error('Update settings error:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to update settings'
    });
  }
});

// Get chat history
app.get('/user/chat-history', authenticateToken, async (req, res) => {
  try {
    const telegramId = req.user.telegram_id;
    const { limit = 20, offset = 0 } = req.query;

    const chats = await Chat.find({ telegram_id: telegramId })
      .sort({ timestamp: -1 })
      .limit(parseInt(limit))
      .skip(parseInt(offset))
      .select('message reply timestamp response_time')
      .lean();

    const total = await Chat.countDocuments({ telegram_id: telegramId });

    res.json({
      success: true,
      chats: chats,
      pagination: {
        total: total,
        limit: parseInt(limit),
        offset: parseInt(offset),
        has_more: total > parseInt(offset) + chats.length
      }
    });

  } catch (error) {
    console.error('Get chat history error:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to get chat history'
    });
  }
});

// Payment endpoints (placeholder for Razorpay integration)
app.post('/payment/create-order', authenticateToken, async (req, res) => {
  try {
    const { plan_type, amount } = req.body;
    const telegramId = req.user.telegram_id;

    // TODO: Integrate with Razorpay
    // For now, return mock response

    const orderId = `order_${Date.now()}_${telegramId}`;

    res.json({
      success: true,
      order: {
        id: orderId,
        amount: amount,
        currency: 'INR',
        plan_type: plan_type,
        status: 'created'
      }
    });

  } catch (error) {
    console.error('Create payment order error:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to create payment order'
    });
  }
});

// Webhook for payment confirmation (placeholder)
app.post('/payment/webhook', express.raw({ type: 'application/json' }), (req, res) => {
  try {
    // TODO: Verify Razorpay webhook signature
    const event = req.body;

    console.log('Payment webhook received:', event);

    res.json({ success: true });

  } catch (error) {
    console.error('Payment webhook error:', error);
    res.status(500).json({ success: false });
  }
});

// Error handling middleware
app.use((error, req, res, next) => {
  console.error('Express error:', error);

  if (error.name === 'ValidationError') {
    return res.status(400).json({
      success: false,
      message: 'Validation error',
      errors: Object.values(error.errors).map(e => e.message)
    });
  }

  res.status(500).json({
    success: false,
    message: 'Internal server error'
  });
});

// Admin Routes (Protected)
const adminAuth = async (req, res, next) => {
  try {
    const token = req.headers.authorization?.split(' ')[1];
    if (!token) {
      return res.status(401).json({ success: false, message: 'No token provided' });
    }

    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    const user = await User.findOne({ telegramId: decoded.telegramId });

    if (!user || !user.isAdmin) {
      return res.status(403).json({ success: false, message: 'Admin access required' });
    }

    req.user = user;
    next();
  } catch (error) {
    return res.status(401).json({ success: false, message: 'Invalid token' });
  }
};

// Get admin stats
app.get('/api/admin/stats', adminAuth, async (req, res) => {
  try {
    const totalUsers = await User.countDocuments();
    const premiumUsers = await User.countDocuments({ isPremium: true });
    const totalChats = await Chat.countDocuments();

    // Calculate revenue (simplified)
    const payments = await Payment.find({ status: 'completed' });
    const totalRevenue = payments.reduce((sum, payment) => sum + (payment.amount || 0), 0);

    // Get user activity (last 24h)
    const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000);
    const activeUsers = await Chat.distinct('userId', { createdAt: { $gte: yesterday } });

    // Calculate changes (simplified - in production use proper analytics)
    const lastWeekUsers = await User.countDocuments({
      createdAt: { $gte: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000) }
    });

    res.json({
      success: true,
      data: {
        totalUsers,
        premiumUsers,
        totalChats,
        totalRevenue,
        activeUsers: activeUsers.length,
        usersChange: totalUsers > 0 ? ((lastWeekUsers / totalUsers) * 100) : 0,
        chatsChange: 0, // Would need historical data
        premiumChange: 0, // Would need historical data
        revenueChange: 0, // Would need historical data
        activityData: {
          labels: ['12AM', '6AM', '12PM', '6PM', 'Now'],
          values: [12, 25, 18, 32, activeUsers.length]
        },
        emotionData: [35, 25, 15, 25] // Happy, Sad, Angry, Neutral
      }
    });
  } catch (error) {
    console.error('Admin stats error:', error);
    res.status(500).json({ success: false, message: 'Failed to fetch stats' });
  }
});

// Get users list
app.get('/api/admin/users', adminAuth, async (req, res) => {
  try {
    const users = await User.find({})
      .select('telegramId name isPremium createdAt lastActive')
      .sort({ createdAt: -1 })
      .limit(100);

    const userData = users.map(user => ({
      telegramId: user.telegramId,
      name: user.name || `User ${user.telegramId}`,
      isPremium: user.isPremium || false,
      createdAt: user.createdAt,
      lastActive: user.lastActive || user.createdAt
    }));

    res.json({ success: true, data: userData });
  } catch (error) {
    console.error('Admin users error:', error);
    res.status(500).json({ success: false, message: 'Failed to fetch users' });
  }
});

// Get analytics data
app.get('/api/admin/analytics', adminAuth, async (req, res) => {
  try {
    const { range = '24h' } = req.query;

    // Calculate date range
    let startDate;
    switch (range) {
      case '7d':
        startDate = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
        break;
      case '30d':
        startDate = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
        break;
      case '90d':
        startDate = new Date(Date.now() - 90 * 24 * 60 * 60 * 1000);
        break;
      default: // 24h
        startDate = new Date(Date.now() - 24 * 60 * 60 * 1000);
    }

    // Get usage data
    const usageData = await Chat.aggregate([
      { $match: { createdAt: { $gte: startDate } } },
      {
        $group: {
          _id: {
            $dateToString: { format: '%Y-%m-%d', date: '$createdAt' }
          },
          count: { $sum: 1 }
        }
      },
      { $sort: { '_id': 1 } }
    ]);

    // Get revenue data
    const revenueData = await Payment.aggregate([
      { $match: { createdAt: { $gte: startDate }, status: 'completed' } },
      {
        $group: {
          _id: {
            $dateToString: { format: '%Y-%m-%d', date: '$createdAt' }
          },
          total: { $sum: '$amount' }
        }
      },
      { $sort: { '_id': 1 } }
    ]);

    res.json({
      success: true,
      data: {
        usageData: {
          labels: usageData.map(d => d._id),
          values: usageData.map(d => d.count)
        },
        revenueData: {
          labels: revenueData.map(d => d._id),
          values: revenueData.map(d => d.total)
        }
      }
    });
  } catch (error) {
    console.error('Admin analytics error:', error);
    res.status(500).json({ success: false, message: 'Failed to fetch analytics' });
  }
});

// Save admin settings
app.post('/api/admin/settings', adminAuth, async (req, res) => {
  try {
    const { aiProvider, emotionEnabled, rateLimit } = req.body;

    // In a real app, you'd save these to a settings collection
    // For now, just acknowledge
    console.log('Admin settings updated:', { aiProvider, emotionEnabled, rateLimit });

    res.json({ success: true, message: 'Settings saved successfully' });
  } catch (error) {
    console.error('Admin settings error:', error);
    res.status(500).json({ success: false, message: 'Failed to save settings' });
  }
});

// Reset admin settings
app.post('/api/admin/settings/reset', adminAuth, async (req, res) => {
  try {
    // Reset to defaults
    const defaults = {
      aiProvider: 'openai',
      emotionEnabled: true,
      rateLimit: 100
    };

    console.log('Admin settings reset to defaults:', defaults);

    res.json({ success: true, message: 'Settings reset to defaults' });
  } catch (error) {
    console.error('Admin settings reset error:', error);
    res.status(500).json({ success: false, message: 'Failed to reset settings' });
  }
});

// Emotion detection endpoint
app.post('/api/emotion/analyze', authenticateToken, async (req, res) => {
  try {
    const { voiceData, faceData, text, language = 'hi' } = req.body;

    const {
      analyzeVoiceEmotion,
      analyzeFaceEmotion,
      analyzeTextEmotion,
      combineEmotions,
      getDominantEmotion
    } = require('./ai');

    // Analyze each input type
    const voiceEmotions = voiceData ? await analyzeVoiceEmotion(voiceData, language) : null;
    const faceEmotions = faceData ? await analyzeFaceEmotion(faceData.landmarks) : null;
    const textEmotions = text ? await analyzeTextEmotion(text, language) : null;

    // Combine emotions
    const combinedEmotions = combineEmotions(voiceEmotions, faceEmotions, textEmotions);
    const dominantEmotion = getDominantEmotion(combinedEmotions);

    res.json({
      success: true,
      data: {
        emotions: combinedEmotions,
        dominantEmotion,
        confidence: Math.max(...Object.values(combinedEmotions)),
        sources: {
          voice: !!voiceEmotions,
          face: !!faceEmotions,
          text: !!textEmotions
        }
      }
    });
  } catch (error) {
    console.error('Emotion analysis error:', error);
    res.status(500).json({ success: false, message: 'Failed to analyze emotions' });
  }
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    success: false,
    message: 'Endpoint not found'
  });
});

// Start server
async function startServer() {
  try {
    // Connect to database
    await connectDB();

    // Start server with Socket.IO
    server.listen(PORT, () => {
      console.log(`🚀 JARVIS AI App server running on port ${PORT}`);
      console.log(`📱 WebApp URL: http://localhost:${PORT}`);
      console.log(`🔗 Health check: http://localhost:${PORT}/health`);
      console.log(`🎙️ Real-time features: Socket.IO enabled`);
      console.log(`🤖 Live AI speaking: Enabled`);
      console.log(`👋 Gesture recognition: Enabled`);
    });

  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

// Market data endpoint
app.get('/api/market-data', async (req, res) => {
  try {
    // For now, return mock data. Later integrate with Python scripts
    const marketData = {
      nifty: {
        value: 22500.50,
        change: 125.75,
        changePercent: 0.56,
        trend: 'up'
      },
      sensex: {
        value: 73500.25,
        change: 350.50,
        changePercent: 0.48,
        trend: 'up'
      },
      crypto: {
        bitcoin: { price: 45000, change: 2.5 },
        ethereum: { price: 2800, change: -1.2 }
      },
      commodities: {
        gold: { price: 1950, change: 0.8 },
        silver: { price: 24, change: -0.5 }
      }
    };

    res.json({
      success: true,
      data: marketData,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('Market data error:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to fetch market data'
    });
  }
});

// Portfolio endpoint
app.get('/api/portfolio', authenticateToken, async (req, res) => {
  try {
    const telegramId = req.user.telegram_id;

    // Mock portfolio data
    const portfolio = {
      totalValue: 28500.75,
      totalChange: 1250.50,
      totalChangePercent: 4.6,
      holdings: [
        { symbol: 'RELIANCE', shares: 10, avgPrice: 2500, currentPrice: 2650, change: 150 },
        { symbol: 'TCS', shares: 5, avgPrice: 3200, currentPrice: 3350, change: 75 },
        { symbol: 'INFY', shares: 8, avgPrice: 1400, currentPrice: 1520, change: 960 }
      ]
    };

    res.json({
      success: true,
      data: portfolio
    });
  } catch (error) {
    console.error('Portfolio error:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to fetch portfolio'
    });
  }
});

// Trading execution endpoint
app.post('/api/trade', authenticateToken, async (req, res) => {
  try {
    const { symbol, type, quantity, price } = req.body;
    const telegramId = req.user.telegram_id;

    // Mock trade execution
    const trade = {
      id: Date.now(),
      symbol,
      type, // 'buy' or 'sell'
      quantity,
      price,
      total: quantity * price,
      status: 'executed',
      timestamp: new Date().toISOString()
    };

    res.json({
      success: true,
      data: trade,
      message: `Trade executed: ${type.toUpperCase()} ${quantity} ${symbol} at ₹${price}`
    });
  } catch (error) {
    console.error('Trade error:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to execute trade'
    });
  }
});

// AI insights endpoint
app.get('/api/ai-insights', authenticateToken, async (req, res) => {
  try {
    const telegramId = req.user.telegram_id;

    // Mock AI insights
    const insights = [
      {
        type: 'signal',
        symbol: 'RELIANCE',
        action: 'BUY',
        confidence: 85,
        reason: 'Strong technical indicators and positive news sentiment'
      },
      {
        type: 'analysis',
        market: 'NIFTY',
        prediction: 'Bullish',
        timeframe: '1-2 weeks',
        reason: 'Global markets showing recovery, FII buying increasing'
      }
    ];

    res.json({
      success: true,
      data: insights
    });
  } catch (error) {
    console.error('AI insights error:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to fetch AI insights'
    });
  }
});

// Real-time chart data endpoint
app.get('/api/chart-data/:symbol', async (req, res) => {
  try {
    const { symbol } = req.params;
    const { timeframe = '1D' } = req.query;

    // Mock chart data
    const chartData = {
      symbol,
      timeframe,
      data: Array.from({ length: 100 }, (_, i) => ({
        time: Date.now() - (100 - i) * 60000, // 1 minute intervals
        open: 22000 + Math.random() * 1000,
        high: 22100 + Math.random() * 1000,
        low: 21900 + Math.random() * 1000,
        close: 22000 + Math.random() * 1000,
        volume: Math.random() * 1000000
      }))
    };

    res.json({
      success: true,
      data: chartData
    });
  } catch (error) {
    console.error('Chart data error:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to fetch chart data'
    });
  }
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('🛑 Shutting down server...');
  process.exit(0);
});

process.on('SIGINT', async () => {
  console.log('🛑 Shutting down server...');
  process.exit(0);
});

// Start the server
startServer();

module.exports = app;