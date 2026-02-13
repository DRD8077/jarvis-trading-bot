require('dotenv').config({ path: require('path').resolve(__dirname, '../.env') });
// Also try loading from workspace root if vars are missing
if (!process.env.BOT_TOKEN) {
  require('dotenv').config({ path: require('path').resolve(__dirname, '../../.env') });
}
const TelegramBot = require('node-telegram-bot-api');

// Bot configuration
const BOT_TOKEN = process.env.BOT_TOKEN || process.env.TELEGRAM_BOT_TOKEN;
const WEBAPP_URL = process.env.WEBAPP_URL || process.env.MINI_APP_URL || 'https://your-domain.com';

if (!BOT_TOKEN) {
  console.error('❌ BOT_TOKEN not found in environment variables');
  console.error('   Set BOT_TOKEN or TELEGRAM_BOT_TOKEN in .env file');
  process.exit(1);
}

if (WEBAPP_URL.includes('your-domain') || WEBAPP_URL.includes('ngrok')) {
  console.warn('⚠️  WARNING: WEBAPP_URL may be invalid:', WEBAPP_URL);
  console.warn('   Update WEBAPP_URL in .env to your codespace URL');
}

// Create bot instance
const bot = new TelegramBot(BOT_TOKEN, { polling: true });

console.log('🤖 JARVIS Telegram Bot started...');
console.log(`🌐 WebApp URL: ${WEBAPP_URL}`);
console.log(`🔑 Bot Token: ${BOT_TOKEN.slice(0, 10)}...`);

// Bot commands and responses
const BOT_COMMANDS = {
  start: {
    description: 'Start the JARVIS AI Assistant',
    handler: handleStart
  },
  help: {
    description: 'Show help information',
    handler: handleHelp
  },
  settings: {
    description: 'Access your settings',
    handler: handleSettings
  },
  premium: {
    description: 'Upgrade to premium features',
    handler: handlePremium
  }
};

// Register commands with Telegram
bot.setMyCommands([
  { command: 'start', description: '🚀 Start JARVIS AI Assistant' },
  { command: 'help', description: '❓ Get help and information' },
  { command: 'settings', description: '⚙️ Access your settings' },
  { command: 'premium', description: '⭐ Upgrade to premium' }
]).then(() => {
  console.log('✅ Bot commands registered');
}).catch(err => console.error('Commands registration error:', err));

// Set the Menu Button to open Mini App
bot.setChatMenuButton({
  menu_button: JSON.stringify({
    type: 'web_app',
    text: '🚀 JARVIS',
    web_app: { url: WEBAPP_URL }
  })
}).then(() => {
  console.log('✅ Menu button set to Mini App');
}).catch(err => console.warn('Menu button setup error (non-critical):', err.message));

// Handle /start command
async function handleStart(msg) {
  const chatId = msg.chat.id;
  const user = msg.from;

  const welcomeMessage = `
🤖 *नमस्ते ${user.first_name || 'दोस्त'}!*

मैं *जार्विस* हूं, आपका AI असिस्टेंट। मैं हिंदी और अंग्रेजी दोनों में बात कर सकता हूं।

🚀 *मेरी सेवाएं:*
• 💬 AI चैट और सवाल जवाब
• 🎙️ आवाज़ इनपुट सपोर्ट
• 📊 स्मार्ट एनालिटिक्स
• 💰 पेमेंट और सब्सक्रिप्शन
• ⚙️ कस्टम सेटिंग्स

👇 नीचे दिए गए बटन पर क्लिक करके शुरू करें:
  `.trim();

  const keyboard = {
    inline_keyboard: [
      [
        {
          text: '🚀 जार्विस खोलें',
          web_app: { url: WEBAPP_URL }
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

  await bot.sendMessage(chatId, welcomeMessage, {
    parse_mode: 'Markdown',
    reply_markup: keyboard
  });
}

// Handle /help command
async function handleHelp(msg) {
  const chatId = msg.chat.id;

  const helpMessage = `
🆘 *जार्विस हेल्प सेंटर*

📱 *मिनी ऐप इस्तेमाल करें:*
• मुख्य फीचर्स के लिए Web App खोलें
• सभी AI फीचर्स ऐप में उपलब्ध हैं

📋 *कमांड्स:*
• /start - बॉट शुरू करें
• /help - यह मदद मैसेज
• /settings - सेटिंग्स बदलें
• /premium - प्रीमियम अपग्रेड

🎯 *मिनी ऐप फीचर्स:*
• 🎤 वॉइस रिकग्निशन
• 😊 इमोशन डिटेक्शन
• 👑 एडमिन पैनल
• 💳 पेमेंट इंटीग्रेशन
  `.trim();

  const keyboard = {
    inline_keyboard: [
      [
        {
          text: '🚀 मिनी ऐप खोलें',
          web_app: { url: WEBAPP_URL }
        }
      ],
      [
        { text: '💬 चैट शुरू करें', callback_data: 'chat_start' },
        { text: '⚙️ सेटिंग्स', callback_data: 'settings' }
      ]
    ]
  };

  await bot.sendMessage(chatId, helpMessage, {
    parse_mode: 'Markdown',
    reply_markup: keyboard
  });
}

// Handle /settings command
async function handleSettings(msg) {
  const chatId = msg.chat.id;

  const settingsMessage = `
⚙️ *जार्विस सेटिंग्स*

वर्तमान सेटिंग्स:
• भाषा: हिंदी/English
• वॉइस: चालू
• नोटिफिकेशन: चालू
• थीम: ऑटो

मिनी ऐप में जाकर सेटिंग्स बदलें:
  `.trim();

  const keyboard = {
    inline_keyboard: [
      [
        {
          text: '⚙️ सेटिंग्स खोलें',
          web_app: { url: WEBAPP_URL + '/settings' }
        }
      ],
      [
        { text: '⬅️ वापस', callback_data: 'back_to_main' }
      ]
    ]
  };

  await bot.sendMessage(chatId, settingsMessage, {
    parse_mode: 'Markdown',
    reply_markup: keyboard
  });
}

// Handle /premium command
async function handlePremium(msg) {
  const chatId = msg.chat.id;

  const premiumMessage = `
⭐ *जार्विस प्रीमियम*

💎 *प्रीमियम फीचर्स:*
• असीमित AI चैट
• वॉइस रिकग्निशन
• जेस्चर कंट्रोल
• भाव विश्लेषण
• प्रायोरिटी सपोर्ट

💰 *कीमत: ₹99/माह*

मिनी ऐप में अपग्रेड करें:
  `.trim();

  const keyboard = {
    inline_keyboard: [
      [
        {
          text: '⭐ प्रीमियम अपग्रेड',
          web_app: { url: WEBAPP_URL }
        }
      ],
      [
        { text: '⬅️ वापस', callback_data: 'back_to_main' }
      ]
    ]
  };

  await bot.sendMessage(chatId, premiumMessage, {
    parse_mode: 'Markdown',
    reply_markup: keyboard
  });
}

// Handle callback queries
bot.on('callback_query', async (query) => {
  const chatId = query.message.chat.id;
  const data = query.data;

  try {
    switch (data) {
      case 'chat_start':
        await bot.sendMessage(chatId, '💬 चैट मोड शुरू! मिनी ऐप में बात करें:', {
          reply_markup: {
            inline_keyboard: [[
              {
                text: '🚀 चैट खोलें',
                web_app: { url: WEBAPP_URL + '/chat' }
              }
            ]]
          }
        });
        break;

      case 'help':
        await handleHelp(query.message);
        break;

      case 'settings':
        await handleSettings(query.message);
        break;

      case 'premium':
        await handlePremium(query.message);
        break;

      case 'back_to_main':
        await handleStart(query.message);
        break;

      default:
        await bot.sendMessage(chatId, '❓ अज्ञात कमांड');
    }

    await bot.answerCallbackQuery(query.id);
  } catch (error) {
    console.error('Callback query error:', error);
    await bot.answerCallbackQuery(query.id, { text: '❌ एरर हुआ' });
  }
});

// Handle text messages (basic AI responses)
bot.on('message', async (msg) => {
  const chatId = msg.chat.id;
  const text = msg.text;

  // Skip commands (they're handled separately)
  if (text && text.startsWith('/')) return;

  // Basic responses for demo
  if (text) {
    let response = '';

    if (text.toLowerCase().includes('hello') || text.toLowerCase().includes('hi')) {
      response = 'नमस्ते! मैं जार्विस हूं। कैसे मदद कर सकता हूं?';
    } else if (text.includes('मौसम') || text.includes('weather')) {
      response = 'क्षमा करें, मैं मौसम की जानकारी नहीं दे सकता। मिनी ऐप में अन्य फीचर्स आजमाएं!';
    } else {
      response = 'मैं आपकी मदद करने के लिए यहां हूं! मिनी ऐप खोलकर सभी फीचर्स का मजा लें 🚀';
    }

    const keyboard = {
      inline_keyboard: [[
        {
          text: '🚀 मिनी ऐप खोलें',
          web_app: { url: WEBAPP_URL }
        }
      ]]
    };

    await bot.sendMessage(chatId, response, {
      reply_markup: keyboard
    });
  }
});

// Handle polling errors
bot.on('polling_error', (error) => {
  console.error('Polling error:', error);
});

// Handle webhook errors
bot.on('webhook_error', (error) => {
  console.error('Webhook error:', error);
});

console.log('✅ JARVIS Bot is ready and listening for messages...');

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('🔄 Shutting down JARVIS bot...');
  bot.stopPolling();
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('🔄 Shutting down JARVIS bot...');
  bot.stopPolling();
  process.exit(0);
});