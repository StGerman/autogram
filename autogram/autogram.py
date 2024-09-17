"""
Autogram: Telegram Article Summarizer

This module provides the Autogram class, which can be used to extract URLs from a Telegram channel,
fetch and summarize articles from those URLs, and save the summaries to files.

Dependencies:
- telethon
- newspaper3k
- aiohttp
- openai

Usage:
1. Create a Telegram app and obtain the API ID and API hash.
2. Create an OpenAI account and obtain the API key.
3. Instantiate the Autogram class with the API ID, API hash, and OpenAI API key.
4. Call the get_urls_from_channel method to extract URLs from a Telegram channel.
5. Call the fetch_articles method to fetch and parse articles from the URLs.
6. Call the summarize_articles method to generate summaries for the articles.
7. Call the save_summaries method to save the summaries to files.

Example:
```python
from autogram import Autogram

api_id = 'your_api_id'
api_hash = 'your_api_hash'
openai_api_key = 'your_openai_api_key'
channel = 'your_channel_name'
lang = 'en'  # Language for summarization

autogram = Autogram(api_id, api_hash, openai_api_key, lang=lang)
```
"""

import re
import os
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

from telethon import TelegramClient
from newspaper import Article
import aiohttp
from bs4 import BeautifulSoup
import openai
import tiktoken
from openai import OpenAIError

class Autogram:
    """Class to extract URLs from a Telegram channel and summarize articles."""
    def __init__(self, api_id, api_hash, openai_api_key, session_name='autogram', lang='en'):
        self.api_id = api_id
        self.api_hash = api_hash
        self.openai_api_key = openai_api_key
        self.session_name = session_name
        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
        openai.api_key = self.openai_api_key
        self.lang = lang # Language for summarization
        self.system_prompt = f"""
        As an experienced journalist and tech writer, you microblog about lifestyle and cutting-edge technologies,
        topics that are of great interest to your audience of software developers and a engineering managers.
        I need you to provide a concise, business-focused summary blog post in {self.lang} language
        and markdown format based on the following content.
        Additionally, please include a list of tags for the post.
        """
        self.executor = ThreadPoolExecutor(max_workers=5)  # Adjust as needed
        print("Autogram initialized")

    async def start(self):
        """Start the Telegram client."""
        await self.client.start()

    async def stop(self):
        """Disconnect the Telegram client and shutdown the executor."""
        await self.client.disconnect()
        self.executor.shutdown(wait=True)

    async def get_urls_from_channel(self, channel_name, limit=100):
        """Extract URLs from messages in a Telegram channel."""
        if not self.client.is_connected():
            await self.start()

        messages = await self.client.get_messages(channel_name, limit=limit)
        urls = []

        # Regular expression pattern to match URLs
        url_pattern = re.compile(r'https?://\S+')

        for message in messages:
            if message.message:
                found_urls = url_pattern.findall(message.message)
                urls.extend(found_urls)

        return urls

    async def fetch_articles(self, urls):
        """Asynchronously fetch and parse articles from URLs."""
        articles = {}
        async with aiohttp.ClientSession() as session:
            tasks = []
            for url in urls:
                # Generate a valid filename from the URL
                filename = re.sub(r'\W+', '_', url) + '.txt'
                # Skip if the article has already been processed
                if os.path.exists(os.path.join("articles", self.lang, filename)):
                    continue

                task = asyncio.ensure_future(self.fetch_content_async(url, session))
                tasks.append((url, filename, task))

            for url, filename, task in tasks:
                content = await task
                if content:
                    articles[url] = (filename, content)
                # If content is None, silently skip

        return articles

    async def fetch_content_async(self, url, session):
        """Fetch content asynchronously and parse it using newspaper3k."""
        try:
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    return None
                html = await response.text()

            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(self.executor, self.parse_article, url, html)
            return content
        except aiohttp.ClientError as e:
            print(f"Error fetching content from {url}: {e}")
            # Ignore exceptions and return None
            return None
        except asyncio.TimeoutError as e:
            print(f"Timeout error fetching content from {url}: {e}")
            # Ignore exceptions and return None
            return None
        except Exception as e:
            print(f"Error fetching content from {url}: {e}")
            # Ignore exceptions and return None
            return None

    def parse_article(self, url, html):
        """Parse article content from HTML using BeautifulSoup."""
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Attempt to find the main content within <article> tags
            article_tag = soup.find('article')
            if article_tag:
                # Extract text from the article tag
                text = article_tag.get_text(separator=' ', strip=True)
            else:
                # Fallback to extracting text from the body tag
                body_tag = soup.find('body')
                if body_tag:
                    text = body_tag.get_text(separator=' ', strip=True)
                else:
                    # Fallback to the entire soup if body tag is not found
                    text = soup.get_text(separator=' ', strip=True)

            # Optional: Clean up the text
            # Remove extra whitespace
            text = ' '.join(text.split())

            return text
        except Exception as e:
            print(f"Error parsing article from {url}: {e}")
            return None

    def truncate_text(self, text, max_tokens, model_name="gpt-4o"):
        """Truncate text to a maximum number of tokens."""
        encoding = tiktoken.encoding_for_model(model_name)
        tokens = encoding.encode(text)
        if len(tokens) > max_tokens:
            tokens = tokens[:max_tokens]
        return encoding.decode(tokens)

    def summarize_articles(self, articles):
        """Generate summaries for articles using OpenAI's API."""
        summaries = {}
        for url, (filename, content) in articles.items():
            summary = self.summarize_text(content)
            if summary:
                summaries[url] = (filename, summary)
        return summaries

    def summarize_text(self, text, retries=3):
        """Summarize text using OpenAI's API."""
        model_name = "gpt-4o"  # Or "gpt-4" if you have access
        max_total_tokens = 8192 if model_name == "gpt-4o" else 8192  # Adjust based on model
        max_response_tokens = 1024  # Desired maximum length of the summary
        buffer_tokens = 100  # For prompt and other overhead
        max_input_tokens = max_total_tokens - max_response_tokens - buffer_tokens

        text = self.truncate_text(
            text=text,
            max_tokens=max_input_tokens,
            model_name=model_name
        )

        for attempt in range(retries):
            try:
                response = openai.chat.completions.create(
                    model="gpt-4o",  # Use "gpt-4" if you have access
                    messages=[
                        {
                            "role": "system",
                            "content": self.system_prompt,
                        },
                        {
                            "role": "user",
                            "content": text,
                        },
                        {
                            "role": "assistant",
                            "content": "please provide the content in" + self.lang + "language",
                        }
                    ],
                    max_tokens=max_response_tokens,
                    temperature=0.7,
                )
                summary = response.choices[0].message.content.strip()
                return summary
            except (OpenAIError, IndexError):
                print(f"Error summarizing text (attempt {attempt + 1})")
                time.sleep(2 ** attempt)

        return None

    def save_summaries(self, summaries):
        """Save summaries to files in the 'articles' directory."""
        lang_dir = os.path.join("articles", self.lang)
        if not os.path.exists(lang_dir):
            os.makedirs(lang_dir)

        for url, (filename, summary) in summaries.items():
            with open(os.path.join(lang_dir, filename), 'w', encoding='utf-8') as file:
                file.write(summary)
            # Optionally, print a success message
            print(f"Summary for {url} saved to {filename}")
