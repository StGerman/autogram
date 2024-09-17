"""
Autogram is a Python library for extracting URLs from a Telegram channel, fetching content from the URLs,
summarizing the content using OpenAI's GPT-4, and saving the summaries to files.

Usage:
1. Create a Telegram channel and add some URLs to it.
2. Create a .env file in the root directory of your project and add the following environment variables:
    TELEGRAM_API_ID=<Your Telegram API ID>
    TELEGRAM_API_HASH=<Your Telegram API hash>
    TELEGRAM_CHANNEL_NAME=<Name of the Telegram channel>
    OPENAI_API_KEY=<Your OpenAI API key>
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
"""
import asyncio
import os
import shutil

from .autogram import Autogram

__all__ = ['Autogram']

async def main():
    """Main function to extract URLs, fetch content, summarize, and save summaries."""
    import os
    import sys
    from dotenv import load_dotenv
    from autogram import Autogram


    # Load environment variables from the .env file
    load_dotenv()

    # Get the environment variables
    API_ID = os.getenv('TELEGRAM_API_ID')
    API_HASH = os.getenv('TELEGRAM_API_HASH')
    CHANNEL_NAME = os.getenv('TELEGRAM_CHANNEL_NAME')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    lang = os.getenv('SUMMARY_LANG')

    if not all([API_ID, API_HASH, CHANNEL_NAME, OPENAI_API_KEY]):
        print("One or more environment variables are missing.")
        sys.exit(1)

    print("Starting Autogram...")
    # Create an instance of the Autogram class
    autogram = Autogram(API_ID, API_HASH, OPENAI_API_KEY, session_name='autogram', lang=lang)

    try:
        # Extract URLs from the Telegram channel
        print("Extracting URLs from the Telegram channel...")
        urls = await autogram.get_urls_from_channel(CHANNEL_NAME, limit=100)
        print(urls)
        # Fetch and parse articles from the URLs
        print("Fetching and parsing articles...")
        articles = await autogram.fetch_articles(urls)
        # Generate summaries for the articles
        print("Generating summaries...")
        summaries = autogram.summarize_articles(articles)
        # Save the summaries to files
        print("Saving summaries...")
        autogram.save_summaries(summaries)
        print("Summaries saved!")
    finally:
        # Ensure resources are properly closed
        await autogram.stop()

def run():
    """Run the main function."""
    asyncio.run(main())
    print("Done!")

if __name__ == "__main__":
    run()

def remove_all_contents_in_directory(directory_path):
    """
    Remove all contents within the specified directory, including files and subdirectories.

    Args:
        directory_path (str): The path to the directory to empty.
    """
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.remove(file_path)
                print(f"Deleted file: {file_path}")
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
                print(f"Deleted directory and its contents: {file_path}")
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")

def clean():
    """Clean up the environment."""
    remove_all_contents_in_directory("articles")
    print("Environment cleaned up!")
