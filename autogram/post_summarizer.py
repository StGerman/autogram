# autogram/post_summarizer.py
"""
Post Summarizer module for Autogram.
"""

import os
import logging
import json

import requests
import openai
import tiktoken
import ell
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
LANG = os.getenv('SUMMARY_LANG', 'en').lower()
MODEL_NAME = os.getenv('OPENAI_MODEL_NAME', 'gpt-4')

logging.basicConfig(level=logging.INFO)

class ContentFetcher:
    def fetch(self, url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                logging.warning(f'Failed to fetch {url}, status code: {response.status_code}')
                return None
            return response.text
        except Exception as e:
            logging.error(f'Error fetching {url}: {e}')
            return None

class ContentParser:
    def parse(self, html):
        try:
            soup = BeautifulSoup(html, 'html.parser')
            article_tag = soup.find('article')
            if article_tag:
                text = article_tag.get_text(separator=' ', strip=True)
            else:
                body_tag = soup.find('body')
                if body_tag:
                    text = body_tag.get_text(separator=' ', strip=True)
                else:
                    text = soup.get_text(separator=' ', strip=True)

            text = ' '.join(text.split())
            return text
        except Exception as e:
            logging.error(f'Error parsing HTML: {e}')
            return None

class PostSummarizer:
    """Summarizes text using OpenAI's API via the Ell framework."""

    def __init__(self, api_key, lang='en'):
        openai.api_key = api_key
        self.lang = lang

    def truncate_text(self, text, max_tokens):
        """Truncates text to a maximum number of tokens."""
        try:
            encoding = tiktoken.encoding_for_model(MODEL_NAME)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        tokens = encoding.encode(text)
        if len(tokens) > max_tokens:
            tokens = tokens[:max_tokens]
            text = encoding.decode(tokens)
        return text

    @ell.simple(model=MODEL_NAME)
    def summary(self, text):
        """
        As a professional content creator, you specialize in microblogging about lifestyle, personal growth, and cutting-edge technologies. Your engaging storytelling captivates an audience eager for both professional and personal development.
        You are tasked with providing concise, business-oriented blog posts in {self.lang} language. Summarize key insights in a couple of paragraphs, using emojis where appropriate to add personality and clarity. Avoid using titles or headings in markdown;
        instead, utilize bold text, lists, code blocks, or block quotes for formatting to enhance readability.
        Incorporate actionable advice and real-world examples to help your readers apply concepts immediately. Encourage community engagement by posing thought-provoking questions or inviting readers to share their experiences.
        """.strip()
        return f"Create a post for text: {text}"

    @ell.simple(model=MODEL_NAME)
    def metadata(self, text):
        """
        You are a person who is responsible for building cross-links, tags, references, and enriching texts with metadata properties.
        All metadata should be wrapped with three dashes (---) at the beginning and end.
        Tags must be comma-separated, camelCase with a leading # symbol,
        and the publication date must be in ISO 8601 format.
        """.strip()
        return f"Add metadata to post: {text}"

    def summarize(self, text):
        """
        Summarizes the given text by first generating a summary and then adding metadata.
        """
        try:
            truncated_text = self.truncate_text(text, 4096)
            # Generate the summary
            summary_text = self.summary(truncated_text)
            if not summary_text:
                logging.error("Failed to generate summary.")
                return None

            # Add metadata to the summary
            final_text = self.metadata(summary_text)
            if not final_text:
                logging.error("Failed to add metadata.")
                return None

            return final_text
        except Exception as e:
            logging.error(f"Error during summarization: {e}")
            return None

def process_single_url(fetcher, parser, summarizer, message_id, url):
    logging.info(f'Processing URL: {url}')
    html = fetcher.fetch(url)
    if not html:
        return None
    content = parser.parse(html)
    if not content:
        return None
    summary = summarizer.summarize(content)
    metadata = summarizer.metadata(summary)
    if not summary:
        return None
    return {
        'message_id': message_id,
        'url': url,
        'summary': summary,
        'metadata': metadata
    }

def process_urls(url_data):
    fetcher = ContentFetcher()
    parser = ContentParser()
    summarizer = PostSummarizer(OPENAI_API_KEY, lang=LANG)

    results = []
    for item in url_data:
        message_id = item['message_id']
        for url in item['urls']:
            result = process_single_url(fetcher, parser, summarizer, message_id, url)
            if result:
                results.append(result)
    return results

if __name__ == '__main__':
    with open('urls.json', 'r', encoding='utf-8') as f:
        url_data = json.load(f)

    summaries = process_urls(url_data)

    with open('summaries.json', 'w', encoding='utf-8') as f:
        json.dump(summaries, f, ensure_ascii=False, indent=4)

    logging.info('Summaries saved to summaries.json')
