// Bot commands configuration and handlers
// This file contains reusable command handlers and utilities

const COMMANDS = {
  START: 'start',
  HELP: 'help',
  SETTINGS: 'settings',
  PREMIUM: 'premium',
  CHAT: 'chat',
  VOICE: 'voice'
};

const COMMAND_DESCRIPTIONS = {
  [COMMANDS.START]: '🚀 Start JARVIS AI Assistant',
  [COMMANDS.HELP]: '❓ Get help and information',
  [COMMANDS.SETTINGS]: '⚙️ Access your settings',
  [COMMANDS.PREMIUM]: '⭐ Upgrade to premium features',
  [COMMANDS.CHAT]: '💬 Start AI chat',
  [COMMANDS.VOICE]: '🎙️ Voice input mode'
};

/**
 * Create main menu keyboard
 */
function createMainKeyboard() {
  return {
    inline_keyboard: [
      [
        {
          text: '🚀 जार्विस खोलें',
          web_app: { url: process.env.WEBAPP_URL || 'https://your-domain.com' }
        }
      ],
      [
        { text: '💬 चैट शुरू करें', callback_data: 'chat_start' },
        { text: '❓ मदद', callback_data: 'help' }
      ],
      [
        { text: '⚙️ सेटिंग्स', callback_data: 'settings' },
        { text: '⭐ प्रीमियम', callback_data: 'premium' }
      ]
    ]
  };
}

/**
 * Create settings keyboard
 */
function createSettingsKeyboard() {
  return {
    inline_keyboard: [
      [
        {
          text: '⚙️ सेटिंग्स खोलें',
          web_app: { url: `${process.env.WEBAPP_URL || 'https://your-domain.com'}/settings` }
        }
      ],
      [
        { text: '🏠 होम', callback_data: 'home' }
      ]
    ]
  };
}

/**
 * Create premium keyboard
 */
function createPremiumKeyboard() {
  return {
    inline_keyboard: [
      [
        {
          text: '💳 प्रीमियम खरीदें',
          web_app: { url: `${process.env.WEBAPP_URL || 'https://your-domain.com'}/premium` }
        }
      ],
      [
        { text: '🏠 होम', callback_data: 'home' }
      ]
    ]
  };
}

/**
 * Format user greeting
 */
function formatUserGreeting(user) {
  const firstName = user.first_name || 'दोस्त';
  return `🤖 *नमस्ते ${firstName}!*`;
}

/**
 * Format welcome message
 */
function formatWelcomeMessage(user) {
  return `
${formatUserGreeting(user)}

मैं *जार्विस* हूं, आपका AI असिस्टेंट। मैं हिंदी और अंग्रेजी दोनों में बात कर सकता हूं।

🚀 *मेरी सेवाएं:*
• 💬 AI चैट और सवाल जवाब
• 🎙️ आवाज़ इनपुट सपोर्ट
• 📊 स्मार्ट एनालिटिक्स
• 💰 पेमेंट और सब्सक्रिप्शन
• ⚙️ कस्टम सेटिंग्स

👇 नीचे दिए गए बटन पर क्लिक करके शुरू करें:
  `.trim();
}

/**
 * Format help message
 */
function formatHelpMessage() {
  return `
🆘 *जार्विस हेल्प सेंटर*

📱 *मिनी ऐप इस्तेमाल करें:*
• मुख्य फीचर्स के लिए Web App खोलें
• सभी AI फीचर्स ऐप में उपलब्ध हैं

🤖 *बोट कमांड्स:*
/start - जार्विस शुरू करें
/help - यह मदद मैसेज
/settings - सेटिंग्स ऐक्सेस करें
/premium - प्रीमियम अपग्रेड

💡 *टिप्स:*
• हिंदी में पूछें - हिंदी में जवाब मिलेगा
• वॉइस मैसेज भेजें - AI समझ लेगा
• प्रीमियम फीचर्स के लिए अपग्रेड करें

📞 *सपोर्ट:*
अगर कोई समस्या हो तो @jarvis_support से संपर्क करें

🔗 *लिंक्स:*
• वेबसाइट: https://jarvis.ai
• डॉक्स: https://docs.jarvis.ai
  `.trim();
}

/**
 * Format settings message
 */
function formatSettingsMessage() {
  return `
⚙️ *जार्विस सेटिंग्स*

वेब ऐप में जाकर अपनी प्राथमिकताएं सेट करें:

🎯 *सेटिंग विकल्प:*
• भाषा चुनें (हिंदी/अंग्रेजी)
• वॉइस इनपुट चालू/बंद
• नोटिफिकेशन सेटिंग्स
• थीम (लाइट/डार्क/ऑटो)

👇 ऐप खोलकर सेटिंग्स बदलें:
  `.trim();
}

/**
 * Format premium message
 */
function formatPremiumMessage() {
  return `
⭐ *जार्विस प्रीमियम*

असीमित AI चैट, प्राथमिकता सपोर्ट और एक्सक्लूसिव फीचर्स पाएं!

💎 *प्रीमियम बेनिफिट्स:*
• 🚀 असीमित AI चैट
• 🎙️ वॉइस इनपुट (पूरी सपोर्ट)
• 📊 एडवांस्ड एनालिटिक्स
• ⚡ फास्ट रिस्पांस
• 🎯 प्राथमिकता सपोर्ट
• 📱 ऑफलाइन मोड

💰 *प्लान्स:*
• मासिक: ₹199/माह
• सालाना: ₹1,999/साल (17% बचत)

👇 अभी अपग्रेड करें:
  `.trim();
}

/**
 * Handle callback data
 */
function handleCallback(callbackData) {
  const handlers = {
    'chat_start': () => ({
      message: '💬 चैट शुरू करने के लिए Web App खोलें:',
      keyboard: {
        inline_keyboard: [[
          {
            text: '🚀 चैट शुरू करें',
            web_app: { url: process.env.WEBAPP_URL || 'https://your-domain.com' }
          }
        ]]
      }
    }),

    'help': () => ({
      message: formatHelpMessage(),
      keyboard: {
        inline_keyboard: [
          [
            {
              text: '🚀 ऐप खोलें',
              web_app: { url: process.env.WEBAPP_URL || 'https://your-domain.com' }
            }
          ],
          [
            { text: '💬 चैट शुरू करें', callback_data: 'chat_start' },
            { text: '⭐ प्रीमियम', callback_data: 'premium' }
          ]
        ]
      }
    }),

    'settings': () => ({
      message: formatSettingsMessage(),
      keyboard: createSettingsKeyboard()
    }),

    'premium': () => ({
      message: formatPremiumMessage(),
      keyboard: createPremiumKeyboard()
    }),

    'home': () => ({
      message: '🏠 होम स्क्रीन पर वापस...',
      keyboard: createMainKeyboard()
    })
  };

  return handlers[callbackData] ? handlers[callbackData]() : null;
}

/**
 * Validate bot token
 */
function validateBotToken(token) {
  if (!token) {
    throw new Error('BOT_TOKEN is required in environment variables');
  }

  // Basic validation - should be a string with numbers and letters
  if (!/^[0-9]+:[A-Za-z0-9_-]+$/.test(token)) {
    throw new Error('Invalid BOT_TOKEN format');
  }

  return true;
}

/**
 * Get bot info
 */
function getBotInfo() {
  return {
    name: 'JARVIS AI Assistant',
    version: '1.0.0',
    description: 'AI-powered Telegram Mini App with Hindi support',
    features: [
      'AI Chat in Hindi & English',
      'Voice Input Support',
      'Secure Authentication',
      'Payment Integration',
      'User Management',
      'Real-time Responses'
    ],
    commands: Object.keys(COMMAND_DESCRIPTIONS).map(cmd => ({
      command: cmd,
      description: COMMAND_DESCRIPTIONS[cmd]
    }))
  };
}

module.exports = {
  COMMANDS,
  COMMAND_DESCRIPTIONS,
  createMainKeyboard,
  createSettingsKeyboard,
  createPremiumKeyboard,
  formatUserGreeting,
  formatWelcomeMessage,
  formatHelpMessage,
  formatSettingsMessage,
  formatPremiumMessage,
  handleCallback,
  validateBotToken,
  getBotInfo
};