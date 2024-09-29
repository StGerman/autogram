# summarizer.py

import time
import tiktoken
import openai
from openai import OpenAIError

class Summarizer:
    """Summarizes text using OpenAI's API."""

    def __init__(self, api_key, lang='en', model_name='gpt-4o'):
        openai.api_key = api_key
        self.lang = lang
        self.model_name = model_name
        self.system_prompt = f"""
        As a world-class journalist and tech writer, you specialize in microblogging about lifestyle, personal growth, and cutting-edge technologies. Your engaging storytelling captivates an audience eager for both professional and personal development.
        You are tasked with providing concise, business-oriented blog posts in {self.lang} language. Summarize key insights in a couple of paragraphs, using emojis where appropriate to add personality and clarity. Avoid using titles or headings in markdown; instead, utilize bold text, lists, code blocks, or block quotes for formatting to enhance readability.
        Metadata properties like tags and publication date should be included at the bottom of each summary, wrapped by three dashes (---) at the beginning and end. Tags must be comma-separated, camelCase with a leading # symbol, and the publication date must be in ISO 8601 format 📅.
        Incorporate actionable advice and real-world examples to help your readers apply concepts immediately. Encourage community engagement by posing thought-provoking questions or inviting readers to share their experiences.
        """.strip()

    def truncate_text(self, text, max_tokens):
        """
        Truncates the given text to a specified number of tokens.

        Args:
            text (str): The text to be truncated.
            max_tokens (int): The maximum number of tokens allowed.

        Returns:
            str: The truncated text.
        """
        try:
            encoding = tiktoken.encoding_for_model(self.model_name)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        tokens = encoding.encode(text)
        if len(tokens) > max_tokens:
            tokens = tokens[:max_tokens]
            text = encoding.decode(tokens)
        return text

    def summarize(self, text, retries=3):
        """
        Summarizes the given text using OpenAI's API.

        Args:
            text (str): The text to be summarized.
            retries (int, optional): The number of retries in case of failure. Defaults to 3.

        Returns:
            str: The summarized text.
        """
        if self.model_name == "gpt-3.5-turbo":
            max_total_tokens = 4096
        elif self.model_name == "gpt-4":
            max_total_tokens = 8192
        else:
            max_total_tokens = 4096

        max_response_tokens = 1024
        buffer_tokens = 100
        max_input_tokens = max_total_tokens - max_response_tokens - buffer_tokens

        text = self.truncate_text(text, max_input_tokens)

        for attempt in range(retries):
            try:
                response = openai.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": text},
                    ],
                    max_tokens=max_response_tokens,
                    temperature=0.7,
                )
                return response.choices[0].message.content.strip()
            except OpenAIError as e:
                print(f"OpenAIError (attempt {attempt + 1}): {e}")
                time.sleep(2 ** attempt)
            except Exception as e:
                print(f"Unexpected error: {e}")
                return None
        return None
