"""
This module contains the core Autogram class
that encapsulates the main functionality of the application.
It is responsible for
    - saving summaries
    - updating Telegram messages
    - restoring original messages.
"""

import re
import logging

from autogram.config import Config
from autogram.telegram_client_handler import TelegramClientHandler
from autogram.file_manager import FileManager
from autogram.mapping_manager import MappingManager
from autogram.message_updater import MessageUpdater
from autogram.message_processor import MessageProcessor

class Autogram:
    """
    Autogram class encapsulates the core functionality of the application,
    including saving summaries and updating Telegram messages.

    Attributes:
        config (Config): Configuration object containing API keys and settings.
        telegram_handler (TelegramClientHandler): Handles interactions with the Telegram API.
        file_manager (FileManager): Manages file operations for saving summaries.
        mapping_manager (MappingManager): Manages mapping between message IDs and summaries.
        message_processor (MessageProcessor): Processes messages and generates summaries.
        message_updater (MessageUpdater): Updates messages in Telegram.

    Methods:
        save_summaries(): Extracts messages with URLs, fetches content, generates summaries,
            saves them to files, and maps message IDs to summaries.
        update_messages(): Updates Telegram messages by appending summaries to them.
        restore_messages(): Restores original messages by updating them with the URL only.
    """

    def __init__(self):
        self.config = Config()

        # Configure logging once at the entry point
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        logging.info("Initializing Autogram...")

        self.telegram_handler = TelegramClientHandler(self.config.API_ID, self.config.API_HASH)
        self.file_manager = FileManager(lang=self.config.LANG)
        self.mapping_manager = MappingManager(self.file_manager)
        self.message_processor = MessageProcessor(self.config, self.file_manager)
        self.message_updater = MessageUpdater(self.telegram_handler, self.file_manager, self.config.CHANNEL_NAME)

    async def save_summaries(self):
        """Extract messages with URLs, fetch content, generate summaries, save them to files, and map message IDs to summaries."""
        logging.info("Starting Autogram Save...")
        try:
            await self.telegram_handler.start()
            messages_with_urls = await self.telegram_handler.get_messages_with_urls(self.config.CHANNEL_NAME)
            mapping = await self.message_processor.process_messages(messages_with_urls)
            self.mapping_manager.save_mapping(mapping)
        finally:
            await self.telegram_handler.stop()
            logging.info("Autogram Save finished.")

    async def update_messages(self):
        """Updates Telegram messages by appending summaries to them."""
        logging.info("Starting Autogram Update...")
        mapping = self.mapping_manager.load_mapping()
        if mapping is None:
            return
        try:
            await self.telegram_handler.start()
            await self.message_updater.update_messages(mapping, self.get_summary_content)
        finally:
            await self.telegram_handler.stop()
            logging.info("Autogram Update finished.")

    async def restore_messages(self):
        """Restores original messages by updating them with the URL only."""
        logging.info("Starting Autogram Restore...")
        mapping = self.mapping_manager.load_mapping()
        if mapping is None:
            return
        try:
            await self.telegram_handler.start()
            await self.message_updater.update_messages(mapping, self.get_url_content)
        finally:
            await self.telegram_handler.stop()
            logging.info("Autogram Restore finished.")

    def get_summary_content(self, message, summaries_info):
        """Builds new message content by appending summaries to the original message."""
        original_message = message.message
        summaries = []
        for info in summaries_info:
            summary = self.file_manager.load_summary(info['filename'])
            if summary:
                summaries.append(f"Summary for {info['url']}:\n{summary}")
        if summaries:
            return original_message + "\n\n" + "\n".join(summaries)
        else:
            return original_message

    def get_url_content(self, message, summaries_info):
        """Replaces message content with the URLs only."""
        urls = [info['url'] for info in summaries_info]
        return "\n".join(urls) if urls else message.message
