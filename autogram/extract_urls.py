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
from typing import List, Dict, Any
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError
from telethon.tl.custom.message import Message
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_ID: str = os.getenv('TELEGRAM_API_ID', '')
API_HASH: str = os.getenv('TELEGRAM_API_HASH', '')
SESSION_STRING: str = os.getenv('TELEGRAM_SESSION_STRING', '')
PHONE_NUMBER: str = os.getenv('PHONE_NUMBER', '')
TWO_STEP_PASSWORD: str = os.getenv('TELEGRAM_TWO_STEP_PASSWORD', '')
CHANNEL_NAME: str = os.getenv('TELEGRAM_CHANNEL_NAME', '')
OUTPUT_FILE: str = 'urls.json'
SESSION_FILE: str = 'telegram_session.txt'

logging.basicConfig(level=logging.INFO)

async def main() -> None:
    """Main function to extract URLs from a Telegram channel."""
    client: TelegramClient = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

    await client.start()
    if not await client.is_user_authorized():
        try:
            await client.send_code_request(PHONE_NUMBER)
            code: str = input('Enter the code you received: ')
            await client.sign_in(PHONE_NUMBER, code)
        except SessionPasswordNeededError:
            if TWO_STEP_PASSWORD:
                await client.sign_in(password=TWO_STEP_PASSWORD)
            else:
                logging.error("Two-Step Verification password is required but not provided.")
                return

    # Generate and save the session string
    session_string: str = client.session.save()
    with open(SESSION_FILE, 'w', encoding="utf-8") as f:
        f.write(session_string)
        print(f"Session string saved to {SESSION_FILE}")

    url_pattern: re.Pattern = re.compile(r'https?://\S+')

    messages: List[Message] = await client.get_messages(CHANNEL_NAME, limit=10)
    url_data: List[Dict[str, Any]] = []

    for message in messages:
        if message.message:
            found_urls: List[str] = url_pattern.findall(message.message)
            if found_urls:
                url_data.append({
                    'message_id': message.id,
                    'urls': found_urls
                })

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(url_data, f, ensure_ascii=False, indent=4)

    logging.info('Extracted URLs saved to %s', OUTPUT_FILE)
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
