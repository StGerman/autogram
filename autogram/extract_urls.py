"""
Extract URLs from Telegram channel messages.

This script connects to a Telegram channel and extracts URLs from the messages,
saving them to a JSON file.
"""

import os
import re
import json
import logging
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
SESSION_STRING = os.getenv('TELEGRAM_SESSION_STRING')
PHONE_NUMBER = os.getenv('PHONE_NUMBER')
CHANNEL_NAME = os.getenv('TELEGRAM_CHANNEL_NAME')
OUTPUT_FILE = 'urls.json'

logging.basicConfig(level=logging.INFO)

async def main():
    """Main function to extract URLs from a Telegram channel."""
    if SESSION_STRING:
        client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    else:
        client = TelegramClient('autogram', API_ID, API_HASH)

    await client.start()
    if not await client.is_user_authorized():
        try:
            print("Your session string is:", client.session.save())
            await client.send_code_request(PHONE_NUMBER)
            code = input('Enter the code you received: ')
            await client.sign_in(PHONE_NUMBER, code)
        except SessionPasswordNeededError:
            password = input('Two-Step Verification enabled. Please enter your password: ')
            await client.sign_in(password=password)

    url_pattern = re.compile(r'https?://\S+')

    messages = await client.get_messages(CHANNEL_NAME, limit=100)
    url_data = []

    for message in messages:
        if message.message:
            found_urls = url_pattern.findall(message.message)
            if found_urls:
                url_data.append({
                    'message_id': message.id,
                    'urls': found_urls
                })

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(url_data, f, ensure_ascii=False, indent=4)

    logging.info(f'Extracted URLs saved to {OUTPUT_FILE}')
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
