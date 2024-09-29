import logging
from telethon.errors import MessageNotModifiedError

class MessageUpdater:
    """
    A class to update messages with new content.

    Attributes:
    - telegram_handler (TelegramClientHandler): The Telegram client handler.
    - file_manager (FileManager): The file manager object.

    Methods:
    - update_messages: Update messages based on the provided mapping and content function.
    - edit_message: Edit a message with the given message_id to have the new_content.
    """
    def __init__(self, telegram_handler, file_manager, channel_name):
        self.telegram_handler = telegram_handler
        self.file_manager = file_manager
        self.channel_name = channel_name

    async def update_messages(self, mapping, content_func):
        """
        Update messages based on the provided mapping and content function.

        Parameters:
        - mapping (dict): The mapping of message IDs to summary information.
        - content_func (function): A function that takes the message and summary information
          as arguments and returns the new message content.

        Returns:
        - None
        """
        for message_id_str, summaries_info in mapping.items():
            message_id = int(message_id_str)
            logging.info("Updating message %s...", message_id)
            message = await self.telegram_handler.get_message(self.channel_name, message_id)
            if not message:
                logging.warning("Message with ID %s not found in %s", message_id, self.channel_name)
                continue

            new_content = content_func(message, summaries_info)
            await self.edit_message(message_id, new_content)

    async def edit_message(self, message_id, new_content):
        """
        Edit a message with the given message_id to have the new_content.

        Parameters:
        - message_id (int): The ID of the message to be edited.
        - new_content (str): The new content of the message.

        Raises:
        - MessageNotModifiedError: If the new_content is the same as the existing content of the message.
        - Exception: If an error occurs while updating the message.

        Returns:
        - None
        """
        try:
            await self.telegram_handler.edit_message(self.channel_name, message_id, new_content)
            logging.info("Message %s updated.", message_id)
        except MessageNotModifiedError:
            logging.warning("Message %s not modified. Skipping.", message_id)
