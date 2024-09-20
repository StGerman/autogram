"""
Autogram is a Python library for extracting URLs from a Telegram channel,
fetching content from the URLs, summarizing the content using OpenAI's GPT-4,
and saving the summaries to files.

Usage:
1. Create a Telegram channel and add some URLs to it.
2. Create a .env file in the root directory of your project and
    add the following environment variables:
    TELEGRAM_API_ID=<Your Telegram API ID>
    TELEGRAM_API_HASH=<Your Telegram API hash>
    TELEGRAM_CHANNEL_NAME=<Name of the Telegram channel>
    OPENAI_API_KEY=<Your OpenAI API key>
    SUMMARY_LANG=<Language for summarization (default: en)>
3. Create a main.py file in the root directory of your project and add the following code:
    ```
    import asyncio
    import os
    import sys
    from dotenv import load_dotenv
    from autogram import Autogram

    async def main():
        # Load environment variables from the .env file
        load_dotenv()

        # Get the environment variables
        API_ID = os.getenv('TELEGRAM_API_ID')
        API_HASH = os.getenv('TELEGRAM_API_HASH')
        CHANNEL_NAME = os.getenv('TELEGRAM_CHANNEL_NAME')
        OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

        if not all([API_ID, API_HASH, CHANNEL_NAME, OPENAI_API_KEY]):
            print("One or more environment variables are missing.")
            sys.exit(1)

        # Create an instance of the Autogram class
        authogram = Autogram(API_ID, API_HASH, OPENAI_API_KEY)

        try:
            # Extract URLs from the Telegram channel
            urls = await autogram.get_urls_from_channel(CHANNEL_NAME, limit=100)

            # Fetch and parse articles from the URLs
            articles = await autogram.fetch_articles(urls)

            # Generate summaries for the articles
            summaries = autogram.summarize_articles(articles)

            # Save the summaries to files
            autogram.save_summaries(summaries)
        finally:
            # Ensure resources are properly closed
            await autogram.stop()
    ```
"""

import asyncio
import os
import sys
import re
import logging

from dotenv import load_dotenv

from .telegram_client_handler import TelegramClientHandler
from .article_fetcher import ArticleFetcher
from .article_parser import ArticleParser
from .summarizer import Summarizer
from .file_manager import FileManager

async def main():
    """
    Main function to extract URLs from a Telegram channel,
    fetch and summarize articles,
    and save the summaries to files.
    """

    # Load environment variables from the .env file
    load_dotenv()

    # Load environment variables
    API_ID = os.getenv('TELEGRAM_API_ID')
    API_HASH = os.getenv('TELEGRAM_API_HASH')
    CHANNEL_NAME = os.getenv('TELEGRAM_CHANNEL_NAME')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    LANG = os.getenv('SUMMARY_LANG', 'en').lower()

    logging.basicConfig(level=logging.INFO)
    logging.info("Starting Autogram...")
    logging.info("API_ID: %s", API_ID)
    logging.info("API_HASH: %s", {API_HASH})
    logging.info("CHANNEL_NAME: %s", CHANNEL_NAME)
    logging.info("OPENAI_API_KEY: %s", OPENAI_API_KEY)
    logging.info("LANG: %s", LANG)

    if not all([API_ID, API_HASH, CHANNEL_NAME, OPENAI_API_KEY]):
        print("One or more environment variables are missing.")
        sys.exit(1)

    # Initialize components
    logging.info("Initializing components...")
    telegram_handler = TelegramClientHandler(API_ID, API_HASH)
    fetcher = ArticleFetcher()
    parser = ArticleParser()
    summarizer = Summarizer(OPENAI_API_KEY, lang=LANG)
    file_manager = FileManager(lang=LANG)

    try:
        # Extract URLs from Telegram channel
        urls = await telegram_handler.get_urls_from_channel(CHANNEL_NAME)


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



def run():
    """Run the main function."""
    asyncio.run(main())
    print("Done!")

if __name__ == "__main__":
    run()
