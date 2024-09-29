import json
import logging
import os


class MappingManager:
    """
    A class that manages the mapping of message summaries.

    Args:
      file_manager (FileManager): The file manager object.

    Attributes:
      file_manager (FileManager): The file manager object.
      mapping_file (str): The path to the mapping file.

    Methods:
      save_mapping: Saves the mapping to the mapping file.
      load_mapping: Loads the mapping from the mapping file.
    """
    def __init__(self, file_manager):
        self.file_manager = file_manager
        self.mapping_file = os.path.join(file_manager.base_dir, 'message_summary_mapping.json')

    def save_mapping(self, mapping):
        """
        Save the given mapping to a file.

        Args:
          mapping (dict): The mapping to be saved.

        Returns:
          None

        Raises:
          None
        """
        with open(self.mapping_file, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, ensure_ascii=False, indent=4)
        logging.info("Mapping saved to %s", self.mapping_file)

    def load_mapping(self):
        """
        Loads the mapping from the specified file.

        Returns:
          dict: The loaded mapping.
        """
        if not os.path.exists(self.mapping_file):
            logging.error("Mapping file %s does not exist.", self.mapping_file)
            return None
        with open(self.mapping_file, 'r', encoding='utf-8') as f:
            mapping = json.load(f)
        logging.info("Mapping loaded from %s", self.mapping_file)
        return mapping
