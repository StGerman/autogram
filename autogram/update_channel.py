import asyncio
import logging
import json
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, MessageNotModifiedError
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
DESTINATION_CHANNEL_NAME = os.getenv('DESTINATION_CHANNEL_NAME')
SESSION_STRING = os.getenv('TELEGRAM_SESSION_STRING')

logging.basicConfig(level=logging.INFO)

class ChannelUpdater:
    def __init__(self, api_id, api_hash, session_string=None):
        if session_string:
            self.client = TelegramClient(StringSession(session_string), api_id, api_hash)
        else:
            self.client = TelegramClient('channel_updater_session', api_id, api_hash)

    async def start(self):
        await self.client.start()
        if not await self.client.is_user_authorized():
            try:
                await self.client.send_code_request(os.getenv('PHONE_NUMBER'))
                await self.client.sign_in(os.getenv('PHONE_NUMBER'), input('Enter the code: '))
            except SessionPasswordNeededError:
                await self.client.sign_in(password=input('Password: '))

    async def update_channel(self, summaries_data):
        await self.start()
        for item in summaries_data:
            summary = item['summary']
            try:
                new_message = await self.client.send_message(DESTINATION_CHANNEL_NAME, summary)
                logging.info(f'Sent new message with ID {new_message.id} to {DESTINATION_CHANNEL_NAME}')
            except Exception as e:
                logging.error(f'Error sending message: {e}')
        await self.client.disconnect()

if __name__ == '__main__':
    with open('summaries.json', 'r', encoding='utf-8') as f:
        summaries_data = json.load(f)

    updater = ChannelUpdater(API_ID, API_HASH, SESSION_STRING)
    asyncio.run(updater.update_channel(summaries_data))
