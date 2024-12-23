"""
Summarize content from URLs.

This script reads URLs from a JSON file, fetches and parses the content,
summarizes it using OpenAI's API via the Ell framework, generates metadata,
and saves the summaries to a JSON file.
"""

import os
import json
import logging
import requests
import openai
import tiktoken
import ell
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL_NAME = os.getenv('OPENAI_MODEL_NAME', 'gpt-4o')
SUMMARY_LANG = os.getenv('SUMMARY_LANG', 'Russian')
INPUT_FILE = 'urls.json'
OUTPUT_FILE = 'summaries.json'

logging.basicConfig(level=logging.INFO)

# Initialize Ell framework
ell.init(store='./logdir', autocommit=True, verbose=True)

def fetch_content(url):
    """Fetches the content from the given URL."""
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logging.error(f'Error fetching {url}: {e}')
        return None

def parse_content(html):
    """Parses the HTML content and extracts the text."""
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
        logging.error(f'Error parsing content: {e}')
        return None

def truncate_text(text, max_tokens=4096):
    """
    Truncates text to a maximum number of tokens using tiktoken.

    Args:
        text (str): The text to truncate.
        max_tokens (int): The maximum number of tokens allowed.

    Returns:
        str: The truncated text.
    """
    try:
        # Get the encoding for the specified model
        encoding = tiktoken.encoding_for_model(OPENAI_MODEL_NAME)
    except KeyError:
        # Fallback encoding if model not found
        encoding = tiktoken.get_encoding("cl100k_base")
    # Encode the text into tokens
    tokens = encoding.encode(text)
    # Truncate tokens if necessary
    if len(tokens) > max_tokens:
        tokens = tokens[:max_tokens]
    # Decode tokens back into text
    truncated_text = encoding.decode(tokens)
    return truncated_text


@ell.simple(model=OPENAI_MODEL_NAME, temperature=0.1)
def summarize_text(text):
    """Summarizes the given text using a custom prompt."""
    prompt = f"""
As a professional content creator, you specialize in microblogging about lifestyle, personal growth, and cutting-edge technologies. Your engaging storytelling captivates an audience eager for both professional and personal development.
You are tasked with providing concise, business-oriented blog posts. Summarize key insights in the {SUMMARY_LANG} language in a couple of paragraphs.
Using emojis where appropriate to add casuality and clarity to {SUMMARY_LANG} text. Avoid using titles or headings in markdown;
instead, utilize bold text, lists, code blocks, or block quotes for formatting to enhance readability.
Incorporate actionable advice and real-world examples to help your readers apply concepts immediately.
""".strip()
    return [
        ell.system(prompt),
        ell.user(f"Write a post based the text below: \n\n {text}")
    ]

@ell.simple(model='gpt-4o-mini', temperature=1.0)
def generate_metadata(text):
    """Extracts metadata from the given text."""
    prompt = [
        ell.system("""
You are a person who is responsible for building cross-links, tags, references, and enriching texts with metadata properties.
All available metadata should be wrapped with three dashes (---) at the beginning and end.
Tags must be comma-separated, camelCase with a leading # symbol.
Publication date must be in ISO 8601 format.
""".strip()),
        ell.user(f"Return metadata ONLY for the text below: {text}")
    ]
    return prompt

def process_url(message_id, url):
    """Processes a single URL: fetches content, parses it, and generates a summary and metadata."""
    logging.info(f'Processing URL: {url}')
    html = fetch_content(url)
    if not html:
        return None
    content = parse_content(html)
    if not content:
        return None
    text = truncate_text(content)
    summary = summarize_text(text)
    if not summary:
        logging.error(f'Failed to generate summary for {url}')
        return None
    metadata = generate_metadata(summary)
    if not metadata:
        logging.error(f'Failed to generate metadata for {url}')
        return None
    return {
        'message_id': message_id,
        'url': url,
        'summary': summary,
        'metadata': metadata
    }

def main():
    """Main function to process URLs and generate summaries."""
    openai.api_key = OPENAI_API_KEY

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        url_data = json.load(f)

    summaries = []

    for item in url_data:
        message_id = item['message_id']
        for url in item['urls']:
            result = process_url(message_id, url)
            if result:
                summaries.append(result)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(summaries, f, ensure_ascii=False, indent=4)

    logging.info(f'Summaries saved to {OUTPUT_FILE}')

if __name__ == '__main__':
    main()
