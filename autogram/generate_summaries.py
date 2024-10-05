import asyncio
import aiohttp
import logging
import json
import os
import openai
import tiktoken
import ell
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
LANG = os.getenv('SUMMARY_LANG', 'en').lower()
MODEL_NAME = os.getenv('OPENAI_MODEL_NAME', 'gpt-4')

logging.basicConfig(level=logging.INFO)

class ContentFetcher:
    async def fetch(self, url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, timeout=15) as response:
                    if response.status != 200:
                        logging.warning(f'Failed to fetch {url}, status code: {response.status}')
                        return None
                    return await response.text()
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

class Summarizer:
    """Summarizes text using OpenAI's API."""
    def __init__(self, api_key, lang='en', model_name='gpt-4'):
        openai.api_key = api_key
        self.lang = lang
        self.model_name = model_name
        self.client = OpenAI(api_key=api_key)
        self.system_prompt = f"""
        As a world-class journalist and tech writer, you specialize in microblogging about lifestyle, personal growth, and cutting-edge technologies. Your engaging storytelling captivates an audience eager for both professional and personal development.
        You are tasked with providing concise, business-oriented blog posts in {self.lang} language. Summarize key insights in a couple of paragraphs, using emojis where appropriate to add personality and clarity. Avoid using titles or headings in markdown; instead, utilize bold text, lists, code blocks, or block quotes for formatting to enhance readability.
        Metadata properties like tags and publication date should be included at the bottom of each summary, wrapped by three dashes (---) at the beginning and end. Tags must be comma-separated, camelCase with a leading # symbol, and the publication date must be in ISO 8601 format 📅.
        Incorporate actionable advice and real-world examples to help your readers apply concepts immediately. Encourage community engagement by posing thought-provoking questions or inviting readers to share their experiences.
        """.strip()

    @ell.simple(model="gpt-4o")
    def summary(self, text):
        """
        As a professional content creator, you specialize in microblogging about lifestyle, personal growth, and cutting-edge technologies. Your engaging storytelling captivates an audience eager for both professional and personal development.
        You are tasked with providing concise, business-oriented blog posts in {self.lang} language. Summarize key insights in a couple of paragraphs, using emojis where appropriate to add personality and clarity. Avoid using titles or headings in markdown;
        instead, utilize bold text, lists, code blocks, or block quotes for formatting to enhance readability.
        Incorporate actionable advice and real-world examples to help your readers apply concepts immediately. Encourage community engagement by posing thought-provoking questions or inviting readers to share their experiences.
        """
        return f"Create a post for text: {text}"

    @ell.simple(model="gpt-4o-mini")
    def metadata(self, text):
        """
        You are person who responsible to build cross links, tags, references and enrich texts with a metadata properties.
        All metadata should be wrapped with three dashes (---) at the beginning and end.
        Tags must be comma-separated, camelCase with a leading # symbol,
        and the publication date must be in ISO 8601 format.
        """
        return f"Set metadata to the post: {text}"

    async def summarize(self, text, retries=3):
        max_total_tokens = 4096
        max_response_tokens = 1024
        buffer_tokens = 100
        max_input_tokens = max_total_tokens - max_response_tokens - buffer_tokens

        text = self.truncate_text(text, max_input_tokens)

        for attempt in range(retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": text},
                    ],
                    max_tokens=max_response_tokens,
                    temperature=0.7,
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                logging.error(f"OpenAIError (attempt {attempt + 1}): {e}")
                await asyncio.sleep(2 ** attempt)
        return None

async def process_single_url(fetcher, parser, summarizer, message_id, url):
    logging.info(f'Processing URL: {url}')
    html = await fetcher.fetch(url)
    if not html:
        return None
    content = parser.parse(html)
    if not content:
        return None
    summary = await summarizer.summarize(content)
    if not summary:
        return None
    return {
        'message_id': message_id,
        'url': url,
        'summary': summary
    }

async def process_urls(url_data):
    fetcher = ContentFetcher()
    parser = ContentParser()
    summarizer = Summarizer(OPENAI_API_KEY, lang=LANG, model_name=MODEL_NAME)

    tasks = []
    for item in url_data:
        message_id = item['message_id']
        for url in item['urls']:
            tasks.append(process_single_url(fetcher, parser, summarizer, message_id, url))

    results = await asyncio.gather(*tasks)
    results = [result for result in results if result is not None]
    return results

async def process_urls(url_data):
    fetcher = ContentFetcher()
    parser = ContentParser()
    summarizer = Summarizer(OPENAI_API_KEY, lang=LANG, model_name=MODEL_NAME)

    results = []
    for item in url_data:
        message_id = item['message_id']
        for url in item['urls']:
            logging.info(f'Processing URL: {url}')
            html = await fetcher.fetch(url)
            if not html:
                continue
            content = parser.parse(html)
            if not content:
                continue
            summary = await summarizer.summarize(content)
            if not summary:
                continue
            results.append({
                'message_id': message_id,
                'url': url,
                'summary': summary
            })
    return results

if __name__ == '__main__':
    with open('urls.json', 'r', encoding='utf-8') as f:
        url_data = json.load(f)

    summaries = asyncio.run(process_urls(url_data))

    with open('summaries.json', 'w', encoding='utf-8') as f:
        json.dump(summaries, f, ensure_ascii=False, indent=4)

    logging.info('Summaries saved to summaries.json')
