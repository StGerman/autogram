# telegram_client_handler.py

from telethon import TelegramClient
import re

class TelegramClientHandler:
    """Handles interactions with the Telegram API."""

    def __init__(self, api_id, api_hash, session_name='autogram'):
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_name = session_name
        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)

    async def start(self):
        await self.client.start()

    async def stop(self):
        await self.client.disconnect()

    async def get_urls_from_channel(self, channel_name, limit=100):
        if not self.client.is_connected():
            await self.start()

        messages = await self.client.get_messages(channel_name, limit=limit)
        urls = []

        url_pattern = re.compile(r'https?://\S+')

        for message in messages:
            if message.message:
                found_urls = url_pattern.findall(message.message)
                urls.extend(found_urls)

        return urls
