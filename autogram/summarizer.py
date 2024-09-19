# summarizer.py

import openai
import tiktoken
import time
from openai import OpenAIError

class Summarizer:
    """Summarizes text using OpenAI's API."""

    def __init__(self, api_key, lang='en', model_name='gpt-4'):
        openai.api_key = api_key
        self.lang = lang
        self.model_name = model_name
        self.system_prompt = f"""
As an experienced journalist and tech writer, you microblog about lifestyle and cutting-edge technologies,
topics that are of great interest to your audience of software developers and engineering managers.
Provide a concise, business-focused summary blog post in {self.lang} language based on the following content.
Additionally, please include metainformation such as author, tags, publication date and source URL if available. Separete the metainformation from the content with --- (three dashes).
""".strip()

    def truncate_text(self, text, max_tokens):
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
