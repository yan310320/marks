#!/usr/bin/env python3
"""
Marks E-Daybook - Telegram Bot for School Grade Management
"""

import os
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import backend

def main():
    """Main entry point for the Marks E-Daybook bot."""
    print("Starting Marks E-Daybook...")

    # Check if token is set
    if not os.getenv("TELEGRAM_TOKEN"):
        print("Error: TELEGRAM_TOKEN environment variable not set!")
        print("Please set your Telegram bot token:")
        print("export TELEGRAM_TOKEN='your_bot_token_here'")
        return

    # The bot polling is handled in backend.py when run as main
    if backend.bot:
        print("Bot is running. Press Ctrl+C to stop.")
        try:
            backend.bot.polling(none_stop=True)
        except KeyboardInterrupt:
            print("\nBot stopped by user.")
        except Exception as e:
            print(f"Error running bot: {e}")
    else:
        print("Failed to initialize bot. Check your token and dependencies.")

if __name__ == "__main__":
    main()