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
        As an world-class journalist and tech writer, you specialize in microblogging about lifestyle, personal-growth and cutting-edge technologies,
        topics that are of great interest to your audience of software developers and engineering managers.
        You are tasked provide a concise, business-oriented blog post in {self.lang} language based on the content,
        with summarizing in couple paragraphs of text with emojis when they are appropriate and necessary.
        Pleasse don't use titles or headings in markdown use only bold, lists, codeblocks or blockquotes for formatting.
        Metadata properties like tags, publication date etc if any available must be included to the bottom of summary and wrapped by --- (three dashes) at the beginning and end of the metadata.
        Tags must be comma separated, camelCase with leading # symbol and publication date must be in ISO 8601 format.
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
