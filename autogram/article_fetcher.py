# article_fetcher.py

import aiohttp
import asyncio
import logging
import os
import re

log = logging.getLogger(__name__)

class ArticleFetcher:
    """
    Fetches HTML content from URLs.
    """
    async def fetch(self, url):
        """Fetch HTML content from a URL."""
        try:
            filename = re.sub(r'\W+', '_', url) + '.md'
            if os.path.exists(filename):
                logging.info("File %s already exists. Skipping fetch", filename)
                return None

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status != 200:
                        return None
                    return await response.text()
        except aiohttp.ClientError as e:
            log.info("Error fetching %s: %s", url, e)
            return None

    async def fetch_all(self, urls):
        """Fetch HTML content from multiple URLs concurrently."""
        tasks = [self.fetch(url) for url in urls]
        return await asyncio.gather(*tasks)
