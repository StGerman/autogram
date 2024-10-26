"""
Build a list of relevant URLs based on the media plan.

This script reads the media plan from a JSON file, searches for relevant URLs using duckduckgo_search,
and saves them to a JSON file.
"""

import os
import json
import logging
from duckduckgo_search import DDGS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
INPUT_FILE = 'media_plan.json'
OUTPUT_FILE = 'urls.json'
NUM_SOURCES = int(os.getenv('NUM_SOURCES', '3'))  # Number of sources to retrieve per topic
SUMMARY_LANG = os.getenv('SUMMARY_LANG', 'en').lower()

logging.basicConfig(level=logging.INFO)

def search_relevant_urls(query, num_results=3):
    """Searches for relevant URLs using duckduckgo_search."""
    logging.info(f"Searching for relevant URLs for query: {query}")
    urls = []
    with DDGS() as ddgs:
        results = ddgs.text(query, region=SUMMARY_LANG, safesearch='Moderate')
        for result in results:
            urls.append(result['href'])
            if len(urls) >= num_results:
                break
    return urls

def main():
    """Main function to build a list of URLs based on the media plan."""
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        media_plan = json.load(f)

    # Adjusted to handle different possible structures
    if isinstance(media_plan, dict) and 'media_plan' in media_plan:
        media_plan = media_plan['media_plan']
    elif isinstance(media_plan, list):
        pass
    else:
        logging.error(f"Unexpected format in {INPUT_FILE}")
        return

    url_data = []

    for idx, item in enumerate(media_plan):
        logging.info(media_plan)
        if not isinstance(item, dict):
            logging.warning(f'Item at index {idx} is not a dictionary, skipping.')
            continue
        topic = item.get('content_topic')
        key_messages = item.get('key_messages')
        item_id = item.get('item_id')
        if not topic or not key_messages:
            logging.warning(f'Missing data in media plan item {idx}, skipping.')
            continue
        # Construct the search query
        query = f"{topic} {key_messages}"
        # Search for relevant URLs
        urls = search_relevant_urls(query, num_results=NUM_SOURCES)
        if not urls:
            logging.warning(f"No relevant URLs found for topic: {topic}")
            continue
        url_data.append({
            'item_id': item_id,
            'topic': topic,
            'urls': urls
        })

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(url_data, f, ensure_ascii=False, indent=4)

    logging.info(f'URLs saved to {OUTPUT_FILE}')

if __name__ == '__main__':
    main()
