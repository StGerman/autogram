# autogram/autogram.py

import asyncio
import re
import logging
import json
import os

from autogram.config import Config
from autogram.telegram_client_handler import TelegramClientHandler
from autogram.article_fetcher import ArticleFetcher
from autogram.article_parser import ArticleParser
from autogram.summarizer import Summarizer
from autogram.file_manager import FileManager

class Autogram:
    """
    Autogram class encapsulates the core functionality of the application,
    including saving summaries and updating Telegram messages.

    Attributes:
        config (Config): Configuration object containing API keys and settings.
        telegram_handler (TelegramClientHandler): Handles interactions with the Telegram API.
        fetcher (ArticleFetcher): Fetches article content from URLs.
        parser (ArticleParser): Parses HTML content to extract article text.
        summarizer (Summarizer): Generates summaries for articles using OpenAI's API.
        file_manager (FileManager): Manages file operations for saving summaries.

    Methods:
        save_summaries(): Extracts messages with URLs, fetches content, generates summaries,
            saves them to files, and maps message IDs to summaries.
        restore_messages(): Restores original messages by updating them with the URL only.
        update_messages(): Updates Telegram messages by appending summaries to them.
    """

    def __init__(self):
        self.config = Config()

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        logging.info("Initializing Autogram...")

        self.telegram_handler = TelegramClientHandler(self.config.API_ID, self.config.API_HASH)
        self.fetcher = ArticleFetcher()
        self.parser = ArticleParser()
        self.summarizer = Summarizer(self.config.OPENAI_API_KEY, lang=self.config.LANG)
        self.file_manager = FileManager(lang=self.config.LANG)

    async def save_summaries(self):
        """Extract messages with URLs, fetch content, generate summaries, save them to files, and map message IDs to summaries."""
        logging.info("Starting Autogram Save...")

        mapping = {}

        try:
            messages_with_urls = await self.telegram_handler.get_messages_with_urls(self.config.CHANNEL_NAME)

            for message, urls in messages_with_urls:
                message_id = message.id
                mapping[message_id] = []
                for url in urls:
                    try:
                        sanitized_url = re.sub(r'\W+', '_', url)
                        filename = f"{message_id}_{sanitized_url}.md"

                        if self.file_manager.check_file_exists(filename):
                            logging.info("File %s already exists. Skipping.", filename)
                            mapping[message_id].append({'url': url, 'filename': filename})
                            continue

                        html = await self.fetcher.fetch(url)
                        if html:
                            content = self.parser.parse(html)
                            if content:
                                summary = self.summarizer.summarize(content)
                                if summary:
                                    self.file_manager.save_summary(filename, summary)
                                    mapping[message_id].append({'url': url, 'filename': filename})
                                    logging.info("Summary saved for message %s, URL: %s", message_id, url)
                                else:
                                    logging.warning("No summary generated for URL: %s", url)
                            else:
                                logging.warning("No content extracted from URL: %s", url)
                        else:
                            logging.warning("No HTML content fetched for URL: %s", url)
                    except Exception as e:
                        logging.error("Error processing URL %s: %s", url, e)

            mapping_file = os.path.join(self.file_manager.base_dir, 'message_summary_mapping.json')
            with open(mapping_file, 'w', encoding='utf-8') as f:
                json.dump(mapping, f, ensure_ascii=False, indent=4)
            logging.info("Mapping saved to %s", mapping_file)

        finally:
            await self.telegram_handler.stop()
            logging.info("Autogram Save finished.")

    async def _process_messages(self, content_func):
        """Helper function to process messages and edit them based on a provided content function."""
        mapping_file = os.path.join(self.file_manager.base_dir, 'message_summary_mapping.json')
        if not os.path.exists(mapping_file):
            logging.error("Mapping file %s does not exist. Run 'save' first.", mapping_file)
            return

        with open(mapping_file, 'r', encoding='utf-8') as f:
            mapping = json.load(f)

        logging.info("Mapping loaded from %s", mapping_file)

        try:
            for message_id_str, summaries_info in mapping.items():
                message_id = int(message_id_str)
                message = await self.telegram_handler.get_message(self.config.CHANNEL_NAME, message_id)
                if not message:
                    logging.warning("Message with ID %s not found.", message_id)
                    continue

                # Use the content_func to determine how the message content will be built (either URL or summary)
                new_message = content_func(summaries_info)

                await self.telegram_handler.edit_message(self.config.CHANNEL_NAME, message_id, new_message)
                logging.info("Message %s updated.", message_id)

        finally:
            await self.telegram_handler.stop()

    async def restore_messages(self):
        """Restores messages by updating them with URLs only."""
        logging.info("Starting Autogram Restore...")

        def get_url_content(summaries_info):
            """Extract URLs to set as message content."""
            urls = [info['url'] for info in summaries_info]
            return "\n".join(urls)

        await self._process_messages(get_url_content)
        logging.info("Autogram Restore finished.")

    async def update_messages(self):
        """Updates messages by appending the saved summaries."""
        logging.info("Starting Autogram Update...")

        def get_summary_content(summaries_info):
            """Read summary files and return the concatenated summaries."""
            summaries = []
            for info in summaries_info:
                filename = info['filename']
                summary_filepath = os.path.join(self.file_manager.base_dir, filename)
                if not os.path.exists(summary_filepath):
                    logging.warning("Summary file %s not found.", summary_filepath)
                    continue
                with open(summary_filepath, 'r', encoding='utf-8') as f:
                    summaries.append(f.read())
            return "\n".join(summaries)

        await self._process_messages(get_summary_content)
        logging.info("Autogram Update finished.")
