"""
Date and time utilities.

This module provides functions for date and time formatting and manipulation.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def format_datetime(
    dt_string: str,
    format_str: str = "%d/%m/%Y %H:%M"
) -> str:
    """
    Format a date string to a readable format.

    Args:
        dt_string: Date string in ISO format
        format_str: Desired output format
        
    Returns:
        Formatted date
    """
    try:
        dt = datetime.fromisoformat(dt_string)
        return dt.strftime(format_str)
    except ValueError as e:
        logger.warning(f"Invalid date format: {e}")
        return dt_string
    except Exception as e:
        logger.warning(f"Error formatting date: {e}")
        return dt_string