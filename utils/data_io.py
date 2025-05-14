"""
Data input/output utilities.

This module provides functions for saving and loading data from files.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def save_json_data(data: Dict[str, Any], filename: str) -> bool:
    """
    Save data to a JSON file.

    Args:
        data: Data to save
        filename: File path

    Returns:
        Boolean indicating success of the operation
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        # Write data to file with proper formatting
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Data successfully saved to {filename}")
        return True
    except Exception as e:
        logger.error(f"Error saving data to {filename}: {e}")
        return False


def load_json_data(filename: str) -> Optional[Dict[str, Any]]:
    """
    Load data from a JSON file.

    Args:
        filename: File path

    Returns:
        Loaded data or None if there's an error
    """
    # Check if file exists
    if not os.path.exists(filename):
        logger.warning(f"File not found: {filename}")
        return None

    try:
        # Read and parse JSON data
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)

        logger.info(f"Data successfully loaded from {filename}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error in {filename}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading data from {filename}: {e}")
        return None
