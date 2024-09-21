"""
MessageProcessor class handles the processing of messages containing URLs.
It fetches the content from the URLs, parses the content, generates summaries,
and saves the summaries to files.

Attributes:
    config (Config): Configuration object containing API keys and settings.
    file_manager (FileManager): Manages file operations for saving summaries.
    fetcher (ArticleFetcher): Fetches article content from URLs.
    parser (ArticleParser): Parses HTML content to extract article text.
    summarizer (Summarizer): Generates summaries for articles using OpenAI's API.

Methods:
    process_messages(messages_with_urls): Asynchronously processes a list of messages with URLs.
    process_url(message_id, url): Asynchronously processes a single URL,
      fetching, parsing, summarizing, and saving the content.
    generate_filename(message_id, url): Generates a sanitized filename for the summary file
      based on the message ID and URL.
"""

import logging
import re
from .article_fetcher import ArticleFetcher
from .article_parser import ArticleParser
from .summarizer import Summarizer

class MessageProcessor:
    """
    MessageProcessor class handles the processing of messages containing URLs.
    It fetches the content from the URLs, parses the content, generates summaries,
    and saves the summaries to files.

    Attributes:
        config (Config): Configuration object containing API keys and settings.
        file_manager (FileManager): Manages file operations for saving summaries.
        fetcher (ArticleFetcher): Fetches article content from URLs.
        parser (ArticleParser): Parses HTML content to extract article text.
        summarizer (Summarizer): Generates summaries for articles using OpenAI's API.
    """
    def __init__(self, config, file_manager):
        """
        Initializes the MessageProcessor with the given configuration and file manager.

        Args:
            config (Config): Configuration object containing API keys and settings.
            file_manager (FileManager): Manages file operations for saving summaries.
        """
        self.config = config
        self.file_manager = file_manager
        self.fetcher = ArticleFetcher()
        self.parser = ArticleParser()
        self.summarizer = Summarizer(config.OPENAI_API_KEY, lang=config.LANG)

    async def process_messages(self, messages_with_urls):
        """
        Asynchronously processes a list of messages with URLs.

        Args:
            messages_with_urls (list): A list of tuples where
            each tuple contains a message and a list of URLs.

        Returns:
            dict: A mapping of message IDs to a list of summary information dictionaries.
        """
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
        """
        Asynchronously processes a single URL, fetching,
        parsing, summarizing, and saving the content.

        Args:
            message_id (int): The ID of the message containing the URL.
            url (str): The URL to be processed.

        Returns:
            dict: A dictionary containing the URL and the filename of the saved summary,
            or None if processing failed.
        """
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
        """
        Generates a sanitized filename for the summary file based on the message ID and URL.

        Args:
            message_id (int): The ID of the message containing the URL.
            url (str): The URL to be processed.

        Returns:
            str: A sanitized filename for the summary file.
        """
        sanitized_url = re.sub(r'\W+', '_', url)
        return f"{message_id}_{sanitized_url}.md"
