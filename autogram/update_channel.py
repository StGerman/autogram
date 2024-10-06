"""
Update Telegram channel with summarized content.

This script reads summaries from a JSON file and posts them to a Telegram channel,
including metadata and the original URL at the bottom of each post.
Posts are sorted by message_id in ascending order before being sent.
Handles rate limits by catching FloodWait exceptions.
"""

import os
import json
import logging
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, FloodWaitError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
SESSION_STRING = os.getenv('TELEGRAM_SESSION_STRING')
PHONE_NUMBER = os.getenv('PHONE_NUMBER')
DESTINATION_CHANNEL_NAME = os.getenv('DESTINATION_CHANNEL_NAME')
INPUT_FILE = 'summaries.json'

logging.basicConfig(level=logging.INFO)

async def main():
    """Main function to post summaries to a Telegram channel."""
    if SESSION_STRING:
        client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    else:
        client = TelegramClient('autogram', API_ID, API_HASH)

    async with client:
        if not await client.is_user_authorized():
            try:
                await client.send_code_request(PHONE_NUMBER)
                code = input('Enter the code you received: ')
                await client.sign_in(PHONE_NUMBER, code)
            except SessionPasswordNeededError:
                password = input('Two-Step Verification enabled. Please enter your password: ')
                await client.sign_in(password=password)

        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            summaries_data = json.load(f)

        # Sort the summaries by message_id in ascending order
        summaries_data.sort(key=lambda x: x['message_id'])

        for item in summaries_data:
            summary = item['summary']
            metadata = item.get('metadata', '')
            url = item.get('url', '')

            # Construct the message
            message_text = f"{summary}\n\n{metadata}\n {url}"
            sent = False
            while not sent:
                try:
                    new_message = await client.send_message(DESTINATION_CHANNEL_NAME, message_text)
                    logging.info(f'Sent new message with ID {new_message.id} to {DESTINATION_CHANNEL_NAME}')
                    sent = True
                except FloodWaitError as e:
                    wait_time = e.seconds
                    logging.warning(f'Rate limit exceeded. Waiting for {wait_time} seconds...')
                    await asyncio.sleep(wait_time)
                except Exception as e:
                    logging.error(f'Error sending message: {e}')
                    sent = True  # Skip this message to prevent infinite loop

if __name__ == '__main__':
    asyncio.run(main())
