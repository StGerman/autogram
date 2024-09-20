"""
Main script to run the Autogram application.

This script orchestrates the extraction of URLs from a Telegram channel,
fetches content from those URLs, summarizes the content using OpenAI's GPT-4,
and saves the summaries to files.

Usage:
- Ensure all environment variables are set, either via a .env file or directly in the environment.
- Run this script directly: `python main.py`

Important:
- Do not log sensitive information such as API keys or hashes.
"""

import asyncio
import re
import logging

from autogram.config import Config
from autogram.telegram_client_handler import TelegramClientHandler
from autogram.article_fetcher import ArticleFetcher
from autogram.article_parser import ArticleParser
from autogram.summarizer import Summarizer
from autogram.file_manager import FileManager

def run():
    """Run the main asynchronous function."""
    asyncio.run(main())
    logging.info("Done!")

async def main():
    """
    Main function to extract URLs from a Telegram channel,
    fetch and summarize articles,
    and save the summaries to files.
    """
    # Initialize configuration
    config = Config()

    # Configure logging with timestamps and log levels
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    logging.info("Starting Autogram...")
    logging.info("API_ID: %s", config.API_ID)
    logging.info("CHANNEL_NAME: %s", config.CHANNEL_NAME)
    logging.info("LANG: %s", config.LANG)

    # Note: Avoid logging sensitive information like API_HASH and OPENAI_API_KEY

    # Initialize components for handling different parts of the process
    logging.info("Initializing components...")

    # Create instances of the components, passing configuration as needed
    telegram_handler = TelegramClientHandler(config.API_ID, config.API_HASH)
    fetcher = ArticleFetcher()
    parser = ArticleParser()
    summarizer = Summarizer(config.OPENAI_API_KEY, lang=config.LANG)
    file_manager = FileManager(lang=config.LANG)

    try:
        # Extract URLs from Telegram channel
        urls = await telegram_handler.get_urls_from_channel(config.CHANNEL_NAME)


        # Fetch articles
        html_contents = await fetcher.fetch_all(urls)

        # Parse and summarize articles
        for url, html in zip(urls, html_contents):
            filename = re.sub(r'\W+', '_', url) + '.md'
            if file_manager.check_file_exists(filename):
                logging.info("File %s already exists. Skipping summarize.", filename)
                continue
            if html:
                content = parser.parse(html)
                if content:
                    summary = summarizer.summarize("content: %s, url: %s" % (content, url))
                    if summary:
                        filename = re.sub(r'\W+', '_', url) + '.md'
                        file_manager.save_summary(filename, summary)
    finally:
        await telegram_handler.stop()
