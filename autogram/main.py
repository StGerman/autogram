# autogram/main.py

"""
Main script to run the Autogram application.

This script now utilizes the Autogram class to handle the main functionality.
"""

import asyncio
import logging

from autogram.autogram import Autogram

def save():
    """Run the save function to fetch and save summaries."""
    asyncio.run(save_summaries())
    logging.info("Done saving summaries.")

def update():
    """Run the update function to update Telegram messages with summaries."""
    asyncio.run(update_messages())
    logging.info("Done updating messages.")

async def restore_messages():
    """Run the restore_messages method of Autogram."""
    autogram = Autogram()
    await autogram.restore_messages()

def restore():
    """Run the restore function to restore Telegram messages with summaries."""
    asyncio.run(restore_messages())
    logging.info("Done restoring messages.")

async def main():
    """Main function that runs both save and update."""
    autogram = Autogram()
    await autogram.save_summaries()
    await autogram.update_messages()

async def save_summaries():
    """Run the save_summaries method of Autogram."""
    autogram = Autogram()
    await autogram.save_summaries()

async def update_messages():
    """Run the update_messages method of Autogram."""
    autogram = Autogram()
    await autogram.update_messages()
