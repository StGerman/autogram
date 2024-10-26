"""
Generate content posts based on the media plan and URLs.

This script reads the media plan from a JSON file, matches it with URLs from another JSON file,
fetches and parses the content, generates summaries using OpenAI's API via the Ell framework,
and saves the content posts to a JSON file.

Summaries (content posts) take into account:
- Goal
- Content Topic
- Target Audience
- Key Messages
- Parsed content from URLs matched by topic

Token limits are considered during processing to comply with model constraints.
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
SUMMARY_LANG = os.getenv('SUMMARY_LANG', 'en').lower()
MEDIA_PLAN_FILE = 'media_plan.json'
URLS_FILE = 'urls.json'
OUTPUT_FILE = 'summaries.json'
MAX_TOKENS = 4096  # Adjust based on model's context length

logging.basicConfig(level=logging.INFO)

# Initialize Ell framework
ell.init(store='./logdir', autocommit=True, verbose=True)
openai.api_key = OPENAI_API_KEY

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

@ell.simple(model='gpt-4o', temperature=0.1)
def editor(text):
    prompt = """
    Ты — главный "котан" и редактор персонального блога.
    Отредактируй текст, чтобы он был более личным и написан от первого лица для создания уютной атмосферы.
    При редактировании следуй принципам из книги "Пиши, сокращай":
    - убери лишние слова
    - делай текст простым и понятным
    - используй активный залог
    - будь конкретен
    - избегай "воды"
    - сфокусируйся на интересах читателя и решении его проблем
    - всегда используй профессиональный термины на английском языке такие как "embeddings", "metadata", "API", "LLM" и т.д.
    """.strip()
    return [
        ell.system(prompt),
        ell.user(f"Проведи редактуру текста и предоставть финальный вариант. text: \n\n {text}")
    ]

@ell.simple(model="gpt-4o", temperature=0.3)
def generate_content_post(goal, content_topic, target_audience, key_messages, source_content):
    """Generates a content post based on provided parameters and source content."""
    prompt = f"""
You are a professional content creator writing in {SUMMARY_LANG}.

Goal: "{goal}"
Content Topic: "{content_topic}"
Target Audience: "{target_audience}"
Key Messages: "{key_messages}"

Based on the following source material, write an engaging and informative blog post that aligns with the goal and resonates with the target audience. Incorporate the key messages and ensure the content is relevant to the content topic. Use a conversational tone, include real-world examples, and encourage reader engagement. Use formatting elements like bold text, lists, code blocks, or block quotes to enhance readability.

Do not include any titles or headings in Markdown format.

Source Material:
{source_content}
""".strip()
    return prompt

@ell.simple(model="gpt-4o", temperature=0.1)
def summarize_text(text):
    """Summarizes the given text using a custom prompt."""
    prompt = f"""
As a professional content creator, you specialize in microblogging about lifestyle, personal growth, and cutting-edge technologies. Your engaging storytelling captivates an audience eager for both professional and personal development.
You are tasked with providing concise, business-oriented blog posts in {SUMMARY_LANG} language. Summarize key insights in a couple of paragraphs, using emojis where appropriate to add personality and clarity. Avoid using titles or headings in markdown;
instead, utilize bold text, lists, code blocks, or block quotes for formatting to enhance readability.
Incorporate actionable advice and real-world examples to help your readers apply concepts immediately. Encourage community engagement by posing thought-provoking questions or inviting readers to share their experiences.
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
You are responsible for generating metadata for content.
Provide the metadata in the JSON.
Using Markdown format strictly forbiden.
Ensure the JSON is properly formatted and parsable.
""".strip()),
        ell.user(f"Return metadata ONLY for the text below: {text}")
    ]
    return prompt

def process_item(item):
    """Processes a single media plan item: fetches content from URLs, generates content post and metadata."""
    item_id = item['item_id']
    goal = item.get('goal')
    content_topic = item.get('content_topic')
    target_audience = item.get('target_audience')
    key_messages = item.get('key_messages')
    urls = item.get('urls', [])

    logging.info(f'Processing item: {content_topic}')

    if not content_topic or not key_messages or not target_audience or not goal:
        logging.warning(f'Missing data in media plan item {item_id}, skipping.')
        return None

    # Fetch and parse content from URLs
    source_contents = []
    for url in urls:
        html = fetch_content(url)
        if not html:
            continue
        content = parse_content(html)
        if content:
            source_contents.append(content)

    if not source_contents:
        logging.warning(f"No content could be extracted from URLs for topic: {content_topic}")
        source_content = ""
    else:
        # Concatenate and truncate source contents to fit within token limits
        concatenated_content = "\n\n".join(source_contents)
        # Reserve tokens for the prompt and assistant's response
        max_content_tokens = MAX_TOKENS - 1000  # Adjust based on prompt size
        source_content = truncate_text(concatenated_content, max_tokens=max_content_tokens)

    # Generate the content post
    content_post = generate_content_post(goal, content_topic, target_audience, key_messages, source_content)
    if not content_post:
        logging.error(f'Failed to generate content post for topic: {content_topic}')
        return None

    final_content_post = editor(content_post)
    if not final_content_post:
        logging.error(f'Failed to edit content post for topic: {content_topic}')

    # Generate metadata
    metadata_response = generate_metadata(final_content_post)
    try:
        metadata = json.loads(metadata_response)
    except json.JSONDecodeError as e:
        logging.error(f'Failed to parse metadata as JSON: {e}')
        metadata = {}
    return {
        'item_id': item_id,
        'content_topic': content_topic,
        'content_post': final_content_post,
        'metadata': metadata,
        'source_urls': urls  # Include the URLs used
    }

def main():
    """Main function to process the media plan and generate content posts."""
    # Load media plan
    with open(MEDIA_PLAN_FILE, 'r', encoding='utf-8') as f:
        media_plan_data = json.load(f)

    # Adjust if media_plan_data is a list or dict
    if isinstance(media_plan_data, dict) and 'media_plan' in media_plan_data:
        media_plan = media_plan_data['media_plan']
    elif isinstance(media_plan_data, list):
        media_plan = media_plan_data
    else:
        logging.error(f"Unexpected format in {MEDIA_PLAN_FILE}")
        return

    # Load URLs data
    with open(URLS_FILE, 'r', encoding='utf-8') as f:
        urls_data = json.load(f)
        logging.debug("URLs data %s", urls_data)

    # Create a mapping from item_id to URLs
    urls_mapping = {item['item_id']: item['urls'] for item in urls_data}
    logging.debug("URLs mappings %s", urls_mapping)

    content_posts = []

    for _, item in enumerate(media_plan):
        item_id = item.get('item_id')
        # Add goal from media plan if not present in item
        item['goal'] = item.get('goal')

        # Get URLs for this item
        item['urls'] = urls_mapping.get(item_id, [])
        if not item['urls']:
            logging.error(f"No URLs found for item {item_id} ({item.get('content_topic')})")
            raise ValueError("No URLs found for item")

        result = process_item(item)
        if result:
            content_posts.append(result)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(content_posts, f, ensure_ascii=False, indent=4)

    logging.info(f'Content posts saved to {OUTPUT_FILE}')

if __name__ == '__main__':
    main()
