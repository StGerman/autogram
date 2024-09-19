# file_manager.py

import os
import logging

logger = logging.getLogger(__name__)

class FileManager:
    """Manages file operations."""

    def __init__(self, lang='en'):
        self.lang = lang
        self.base_dir = os.path.join('articles', self.lang)
        os.makedirs(self.base_dir, exist_ok=True)

    def check_file_exists(self, filename):
        """Check if a file exists in the base directory."""
        filepath = os.path.join(self.base_dir, filename)
        return os.path.exists(filepath)

    def save_summary(self, filename, summary):
        try:
            filepath = os.path.join(self.base_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(summary)
            logger.info(f"Summary saved to {filepath}")
        except Exception as e:
            logger.info(f"Error saving summary: {e}")
