# article_parser.py

from bs4 import BeautifulSoup
import logging
log = logging.getLogger(__name__)

class ArticleParser:
    """Parses HTML content to extract article text."""

    def parse(self, html):
        """Parse article content from HTML using BeautifulSoup."""
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
            log.info("Error parsing article: %s", e)
            return None
