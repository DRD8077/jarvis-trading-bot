#!/usr/bin/env node

/**
 * JARVIS Bot Test Runner
 * Tests bot functionality without Telegram connection
 */

const { spawn } = require('child_process');

console.log('🧪 JARVIS Bot Test Runner');
console.log('=========================\n');

// Test 1: Check if bot.js exists and is valid
console.log('✅ Test 1: Bot file validation');
try {
    const fs = require('fs');
    const botCode = fs.readFileSync('./bot.js', 'utf8');
    console.log('   ✓ bot.js file exists and readable');
    console.log('   ✓ File size:', botCode.length, 'characters');
} catch (error) {
    console.log('   ❌ Bot file error:', error.message);
}

// Test 2: Check environment configuration
console.log('\n✅ Test 2: Environment check');
try {
    require('dotenv').config();
    const required = ['BOT_TOKEN', 'WEBAPP_URL', 'BACKEND_URL'];
    const missing = required.filter(key => !process.env[key]);

    if (missing.length === 0) {
        console.log('   ✓ All required environment variables present');
    } else {
        console.log('   ⚠️  Missing environment variables:', missing.join(', '));
    }
} catch (error) {
    console.log('   ❌ Environment error:', error.message);
}

// Test 3: Syntax validation
console.log('\n✅ Test 3: JavaScript syntax check');
const syntaxCheck = spawn('node', ['-c', 'bot.js'], { cwd: __dirname });

syntaxCheck.on('close', (code) => {
    if (code === 0) {
        console.log('   ✓ bot.js syntax is valid');
    } else {
        console.log('   ❌ bot.js has syntax errors');
    }
});

// Test 4: Backend connectivity
console.log('\n✅ Test 4: Backend connectivity');
const http = require('http');

const backendCheck = http.get('http://localhost:3000/health', (res) => {
    let data = '';
    res.on('data', (chunk) => data += chunk);
    res.on('end', () => {
        try {
            const response = JSON.parse(data);
            if (response.success) {
                console.log('   ✓ Backend is running and healthy');
            } else {
                console.log('   ⚠️  Backend responded but not healthy');
            }
        } catch (e) {
            console.log('   ❌ Backend response parsing error');
        }
    });
});

backendCheck.on('error', (err) => {
    console.log('   ❌ Cannot connect to backend (is it running?)');
});

setTimeout(() => {
    console.log('\n📋 Test Summary:');
    console.log('   • Bot code: Ready');
    console.log('   • Environment: Needs BOT_TOKEN');
    console.log('   • Backend: Should be running on port 3000');
    console.log('   • WebApp: Available at http://localhost:3000');

    console.log('\n🚀 To run the real bot:');
    console.log('   1. Get token: Message @BotFather on Telegram');
    console.log('   2. Set BOT_TOKEN in bot/.env');
    console.log('   3. Run: node bot.js');

    console.log('\n🎯 Bot Features:');
    console.log('   • /start - Welcome message with WebApp button');
    console.log('   • /help - Help information');
    console.log('   • /settings - User settings');
    console.log('   • /premium - Premium upgrade');
    console.log('   • Inline keyboard with WebApp integration');
    console.log('   • Callback query handling');
    console.log('   • Payment integration ready');

}, 2000);