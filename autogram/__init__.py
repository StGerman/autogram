"""
Script to extract URLs from a Telegram channel.
The extracted data will then be used to generate a summary using OpenAI's LLM model.
"""

import asyncio
import re
import os
import sys
import requests

from bs4 import BeautifulSoup
from telethon.client import TelegramClient
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Get the environment variables
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
CHANNEL_NAME = os.getenv('TELEGRAM_CHANNEL_NAME')

if not all([API_ID, API_HASH, CHANNEL_NAME]):
    print("One or more environment variables are missing.")
    sys.exit(1)

async def main():
    """Main function to extract URLs from a Telegram channel."""
    # Start the client
    async with TelegramClient('autogram', API_ID, API_HASH) as client:

        # Get the channel's messages
        messages = await client.get_messages(CHANNEL_NAME, limit=100)  # Fetch 100 messages

        urls = []

        # Extract URLs using regex
        url_pattern = re.compile(r'https?://\S+')

        for message in messages:
            if message.message:
                urls_in_message = url_pattern.findall(message.message)
                urls.extend(urls_in_message)

        print(f"Extracted URLs: {urls}")

# Run the main function
asyncio.run(main())
