import asyncio
import re
import json
import logging
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
CHANNEL_NAME = os.getenv('TELEGRAM_CHANNEL_NAME')
SESSION_STRING = os.getenv('TELEGRAM_SESSION_STRING')

logging.basicConfig(level=logging.INFO)

class URLExtractor:
    def __init__(self, api_id, api_hash):
        self.client = TelegramClient('autogram', api_id, api_hash)

    async def start(self):
        await self.client.start()
        if not await self.client.is_user_authorized():
            try:
                await self.client.send_code_request(os.getenv('PHONE_NUMBER'))
                await self.client.sign_in(os.getenv('PHONE_NUMBER'), input('Enter the code: '))
            except SessionPasswordNeededError:
                await self.client.sign_in(password=input('Password: '))

    async def extract_urls(self, channel_name, limit=100):
        url_pattern = re.compile(r'https?://\S+')
        messages = await self.client.get_messages(channel_name, limit=limit)
        url_data = []

        for message in messages:
            if message.message:
                found_urls = url_pattern.findall(message.message)
                if found_urls:
                    url_data.append({
                        'message_id': message.id,
                        'urls': found_urls
                    })

        return url_data

    async def run(self, channel_name, output_file):
        await self.start()
        url_data = await self.extract_urls(channel_name)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(url_data, f, ensure_ascii=False, indent=4)
        logging.info(f'Extracted URLs saved to {output_file}')
        await self.client.disconnect()

if __name__ == '__main__':
    extractor = URLExtractor(API_ID, API_HASH)
    asyncio.run(extractor.run(CHANNEL_NAME, 'urls.json'))
