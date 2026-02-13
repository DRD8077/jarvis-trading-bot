#!/usr/bin/env python3
"""
JARVIS Telegram Bot Setup
Creates and configures the Telegram bot for the Mini App
"""

import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_bot():
    """Guide to create Telegram bot"""
    print("🚀 JARVIS Telegram Bot Setup")
    print("=" * 50)

    print("\n📝 Steps to create your bot:")
    print("1. Open Telegram and search for @BotFather")
    print("2. Send /newbot command")
    print("3. Enter bot name: JARVIS Trading Assistant")
    print("4. Enter username: jarvis_trading_bot")
    print("5. Copy the BOT TOKEN and paste below")

    bot_token = input("\n🔑 Enter your BOT TOKEN: ").strip()

    if not bot_token:
        print("❌ Bot token is required!")
        return

    # Save bot token
    with open('.env', 'a') as f:
        f.write(f"\nTELEGRAM_BOT_TOKEN={bot_token}\n")

    print("✅ Bot token saved!")

    # Test bot
    test_bot(bot_token)

def test_bot(token):
    """Test if bot token is valid"""
    try:
        url = f"https://api.telegram.org/bot{token}/getMe"
        response = requests.get(url)
        data = response.json()

        if data['ok']:
            bot_info = data['result']
            print(f"✅ Bot connected successfully!")
            print(f"🤖 Bot Name: {bot_info['first_name']}")
            print(f"👤 Username: @{bot_info['username']}")
            print(f"🆔 Bot ID: {bot_info['id']}")
        else:
            print("❌ Invalid bot token!")
    except Exception as e:
        print(f"❌ Error testing bot: {e}")

def setup_webhook():
    """Setup webhook for the bot"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("❌ Bot token not found! Run create_bot() first")
        return

    # Your server URL (change this to your actual domain)
    webhook_url = input("🌐 Enter your webhook URL (e.g., https://yourdomain.com/webhook): ").strip()

    if not webhook_url:
        print("❌ Webhook URL is required!")
        return

    try:
        url = f"https://api.telegram.org/bot{token}/setWebhook"
        data = {
            'url': webhook_url,
            'allowed_updates': ['message', 'callback_query']
        }

        response = requests.post(url, json=data)
        result = response.json()

        if result['ok']:
            print("✅ Webhook set successfully!")
            print(f"🔗 URL: {webhook_url}")
        else:
            print(f"❌ Failed to set webhook: {result}")

    except Exception as e:
        print(f"❌ Error setting webhook: {e}")

def create_bot_menu():
    """Create the bot menu with Mini App button"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("❌ Bot token not found!")
        return

    # Mini App URL (change this to your deployed Mini App URL)
    mini_app_url = input("🎮 Enter your Mini App URL (e.g., https://yourdomain.com): ").strip()

    if not mini_app_url:
        print("❌ Mini App URL is required!")
        return

    # Set bot commands
    commands_url = f"https://api.telegram.org/bot{token}/setMyCommands"
    commands = [
        {"command": "start", "description": "Start JARVIS Assistant"},
        {"command": "trade", "description": "Open Trading Interface"},
        {"command": "wallet", "description": "Check Wallet Balance"},
        {"command": "help", "description": "Get Help"}
    ]

    try:
        response = requests.post(commands_url, json={"commands": commands})
        if response.json()['ok']:
            print("✅ Bot commands set successfully!")
        else:
            print("❌ Failed to set commands")
    except Exception as e:
        print(f"❌ Error setting commands: {e}")

    print("\n🎯 Bot Setup Complete!")
    print(f"🤖 Bot is ready with Mini App: {mini_app_url}")
    print("\n📱 Users can now:")
    print("• Send /start to begin")
    print("• Click buttons to open Mini App")
    print("• Access all JARVIS features")

if __name__ == "__main__":
    print("🤖 JARVIS Telegram Bot Setup")
    print("=" * 40)

    while True:
        print("\nChoose an option:")
        print("1. Create new bot")
        print("2. Test existing bot")
        print("3. Setup webhook")
        print("4. Configure bot menu")
        print("5. Exit")

        choice = input("\nEnter choice (1-5): ").strip()

        if choice == '1':
            create_bot()
        elif choice == '2':
            token = os.getenv('TELEGRAM_BOT_TOKEN') or input("Enter bot token: ")
            test_bot(token)
        elif choice == '3':
            setup_webhook()
        elif choice == '4':
            create_bot_menu()
        elif choice == '5':
            break
        else:
            print("❌ Invalid choice!")

    print("\n👋 Setup complete! Your JARVIS Telegram Mini App is ready!")