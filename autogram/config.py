# autogram/config.py

import os
import sys
import logging
from dotenv import load_dotenv

class Config:
    """
    Configuration class to load and validate environment variables.
    """

    def __init__(self, load_env=True):
        """
        Initialize the Config class by loading environment variables and validating them.
        :param load_env: Whether to load environment variables from .env file.
        """
        if load_env:
            # Load environment variables from .env file if present
            load_dotenv()

        # Load configuration from environment variables
        self.API_ID = os.getenv('TELEGRAM_API_ID')
        self.API_HASH = os.getenv('TELEGRAM_API_HASH')
        self.CHANNEL_NAME = os.getenv('TELEGRAM_CHANNEL_NAME')
        self.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
        self.LANG = os.getenv('SUMMARY_LANG', 'en').lower()

        # Validate required environment variables
        self.validate()

    def validate(self):
        """
        Validate that all required environment variables are present.
        """
        missing_vars = []

        if not self.API_ID:
            missing_vars.append('TELEGRAM_API_ID')
        if not self.API_HASH:
            missing_vars.append('TELEGRAM_API_HASH')
        if not self.CHANNEL_NAME:
            missing_vars.append('TELEGRAM_CHANNEL_NAME')
        if not self.OPENAI_API_KEY:
            missing_vars.append('OPENAI_API_KEY')

        if missing_vars:
            logging.error("Missing required environment variables: %s", ', '.join(missing_vars))
            sys.exit(1)
