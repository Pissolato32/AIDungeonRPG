"""
Data input/output utilities.

This module provides functions for saving and loading data from files.
"""

import json
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def save_data(data: Dict[str, Any], filename: str) -> bool:
    """
    Save data to a JSON file.

    Args:
        data: The dictionary data to save.
        filename: The name of the file (e.g., "my_data.json").
                  The function will save it within the project's "data" directory.

    Returns: True if the data was saved successfully, False otherwise.
    """
    try:
        # Ensure we have a valid path with data directory
        if not os.path.isabs(filename):
            # If relative path, prepend the data directory
            data_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"
            )
            os.makedirs(data_dir, exist_ok=True)
            filename = os.path.join(data_dir, filename)

        # Create directory if it doesn't exist
        directory = os.path.dirname(filename)
        if directory:  # Check if directory is not empty
            os.makedirs(directory, exist_ok=True)

        # Write data to file with proper formatting
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Data successfully saved to {filename}")
        return True
    except Exception as e:
        logger.error(f"Error saving data to {filename}: {e}")
        return False


def load_data(filename: str) -> Optional[Dict[str, Any]]:
    """
    Load data from a JSON file.

    Args:
        filename: The name of the file to load (e.g., "my_data.json").
                  The function will look for it within the project's "data" directory.

    Returns:
        A dictionary containing the loaded data, or None if the file is not found
        or an error occurs during loading/parsing.
    """
    try:
        # Ensure we have a valid path with data directory
        if not os.path.isabs(filename):
            # If relative path, prepend the data directory
            data_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"
            )
            filename = os.path.join(data_dir, filename)

        # Check if file exists
        if not os.path.exists(filename):
            logger.warning(f"File not found: {filename}")
            return None

        # Read and parse JSON data
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)

        logger.info(f"Data successfully loaded from {filename}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error in {filename}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading data from {filename}: {e}")
        return None
