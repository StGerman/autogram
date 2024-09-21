"""
TelegramClientHandler handles interactions with the Telegram API using the Telethon library.

This class provides methods to:
- Start and stop the Telegram client.
- Retrieve messages containing URLs from a specified Telegram channel.
- Edit a message in a Telegram channel.
- Retrieve a specific message by its ID from a Telegram channel.

Attributes:
    api_id (str): The API ID for the Telegram client.
    api_hash (str): The API hash for the Telegram client.
    session_name (str): The session name for the Telegram client.
    client (TelegramClient): An instance of the TelegramClient from the Telethon library.

Methods:
    start(): Asynchronously starts the Telegram client.
    stop(): Asynchronously stops the Telegram client.
    get_messages_with_urls(channel_name, limit=100):
        Asynchronously retrieves messages containing URLs from the specified channel.
    edit_message(channel, message_id, new_text):
        Asynchronously edits a message in the channel with the new text.
    get_message(channel_name, message_id):
        Asynchronously retrieves a specific message by its ID from the specified channel.
"""

import re
import logging
from telethon import TelegramClient
from telethon.errors import MessageNotModifiedError

class TelegramClientHandler:
    """Handles interactions with the Telegram API."""

    def __init__(self, api_id, api_hash, session_name='autogram'):
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_name = session_name
        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)

    async def start(self):
        """Start the Telegram client."""
        await self.client.start()

    async def stop(self):
        """Stop the Telegram client."""
        await self.client.disconnect()

    async def get_messages_with_urls(self, channel_name, limit=100):
        """Retrieve messages containing URLs from the specified channel."""
        if not self.client.is_connected():
            await self.start()

        messages = await self.client.get_messages(channel_name, limit=limit)
        url_pattern = re.compile(r'https?://\S+')

        messages_with_urls = []

        for message in messages:
            if message.message:
                found_urls = url_pattern.findall(message.message)
                if found_urls:
                    messages_with_urls.append((message, found_urls))

        return messages_with_urls

    async def edit_message(self, channel, message_id, new_text):
        """Edit a message in the channel with the new text."""
        if not self.client.is_connected():
            await self.start()

        try:
            await self.client.edit_message(channel, message_id, new_text)
            logging.info(f"Message {message_id} updated successfully.")
        except MessageNotModifiedError:
            logging.warning(f"Message {message_id} not modified (content is the same). Skipping.")
        except Exception as e:
            logging.error(f"Error editing message {message_id}: {str(e)}")

    async def get_message(self, channel_name, message_id):
        """Retrieve a specific message by its ID."""
        if not self.client.is_connected():
            await self.start()
        try:
            message = await self.client.get_messages(channel_name, ids=message_id)
            return message
        except Exception as e:
            logging.error("Error retrieving message %s: %s", message_id, e)
            return None
