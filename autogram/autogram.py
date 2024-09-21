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
from autogram.article_fetcher import ArticleFetcher
from autogram.article_parser import ArticleParser
from autogram.summarizer import Summarizer
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
        self.message_updater = MessageUpdater(self.telegram_handler, self.file_manager)

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


class MessageProcessor:
    """
    Handles the extraction and processing of messages with URLs, including fetching,
    parsing, summarizing content, and saving summaries to files.
    """

    def __init__(self, config, file_manager):
        self.config = config
        self.file_manager = file_manager
        self.fetcher = ArticleFetcher()
        self.parser = ArticleParser()
        self.summarizer = Summarizer(config.OPENAI_API_KEY, lang=config.LANG)

    async def process_messages(self, messages_with_urls):
        """Processes a list of messages with URLs and generates summaries."""
        mapping = {}
        for message, urls in messages_with_urls:
            message_id = message.id
            mapping[message_id] = []
            for url in urls:
                summary_info = await self.process_url(message_id, url)
                if summary_info:
                    mapping[message_id].append(summary_info)
        return mapping

    async def process_url(self, message_id, url):
        """Processes a single URL: fetches content, parses it, generates a summary, and saves it."""
        filename = self.generate_filename(message_id, url)
        if self.file_manager.check_file_exists(filename):
            logging.info("File %s already exists. Skipping.", filename)
            return {'url': url, 'filename': filename}

        html = await self.fetcher.fetch(url)
        if not html:
            logging.warning("No HTML content fetched for URL: %s", url)
            return None

        content = self.parser.parse(html)
        if not content:
            logging.warning("No content extracted from URL: %s", url)
            return None

        summary = self.summarizer.summarize(content)
        if not summary:
            logging.warning("No summary generated for URL: %s", url)
            return None

        self.file_manager.save_summary(filename, summary)
        logging.info("Summary saved for message %s, URL: %s", message_id, url)
        return {'url': url, 'filename': filename}

    @staticmethod
    def generate_filename(message_id, url):
        """Generates a sanitized filename based on message ID and URL."""
        sanitized_url = re.sub(r'\W+', '_', url)
        return f"{message_id}_{sanitized_url}.md"
