"""
Date utility functions for PyCommerce.

This module provides helper functions for date and time operations
commonly used across the application.
"""
import logging
import datetime
from typing import List, Optional
from dateutil.parser import parse as parse_date
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)

def parse_iso_date(date_str: str) -> Optional[datetime.datetime]:
    """
    Parse an ISO format date string into a datetime object.
    
    Args:
        date_str: Date string in ISO format (YYYY-MM-DD)
        
    Returns:
        Datetime object or None if parsing fails
    """
    try:
        return parse_date(date_str)
    except Exception as e:
        logger.error(f"Error parsing date '{date_str}': {str(e)}")
        return None

def format_date(date_obj: datetime.datetime, format_str: str = "%Y-%m-%d") -> str:
    """
    Format a datetime object as a string.
    
    Args:
        date_obj: Datetime object to format
        format_str: Format string for the output
        
    Returns:
        Formatted date string
    """
    try:
        return date_obj.strftime(format_str)
    except Exception as e:
        logger.error(f"Error formatting date: {str(e)}")
        return ""

def get_date_range(start_date: str, end_date: str) -> List[str]:
    """
    Get a list of dates between start_date and end_date, inclusive.
    
    Args:
        start_date: Start date in ISO format (YYYY-MM-DD)
        end_date: End date in ISO format (YYYY-MM-DD)
        
    Returns:
        List of date strings in ISO format
    """
    try:
        start = parse_iso_date(start_date)
        end = parse_iso_date(end_date)
        
        if not start or not end:
            logger.error("Invalid start or end date")
            return []
        
        if start > end:
            logger.error("Start date cannot be after end date")
            return []
        
        date_list = []
        current = start
        
        while current <= end:
            date_list.append(current.strftime("%Y-%m-%d"))
            current += datetime.timedelta(days=1)
        
        return date_list
    except Exception as e:
        logger.error(f"Error generating date range: {str(e)}")
        return []

def get_start_of_period(period: str) -> datetime.datetime:
    """
    Get the start date for a time period relative to now.
    
    Args:
        period: Time period name ('day', 'week', 'month', 'quarter', 'year')
        
    Returns:
        Datetime object for the start of the specified period
    """
    now = datetime.datetime.now()
    
    if period == 'day':
        return datetime.datetime(now.year, now.month, now.day, 0, 0, 0)
    elif period == 'week':
        return now - datetime.timedelta(days=now.weekday())
    elif period == 'month':
        return datetime.datetime(now.year, now.month, 1)
    elif period == 'quarter':
        quarter_month = ((now.month - 1) // 3) * 3 + 1
        return datetime.datetime(now.year, quarter_month, 1)
    elif period == 'year':
        return datetime.datetime(now.year, 1, 1)
    else:
        # Default to today
        return datetime.datetime(now.year, now.month, now.day, 0, 0, 0)

def get_relative_period(base_date: datetime.datetime, periods_back: int, period_type: str) -> datetime.datetime:
    """
    Get a date that is a number of periods back from a base date.
    
    Args:
        base_date: The base date to calculate from
        periods_back: Number of periods to go back
        period_type: Type of period ('day', 'week', 'month', 'quarter', 'year')
        
    Returns:
        Datetime object for the calculated date
    """
    if period_type == 'day':
        return base_date - datetime.timedelta(days=periods_back)
    elif period_type == 'week':
        return base_date - datetime.timedelta(weeks=periods_back)
    elif period_type == 'month':
        return base_date - relativedelta(months=periods_back)
    elif period_type == 'quarter':
        return base_date - relativedelta(months=periods_back * 3)
    elif period_type == 'year':
        return base_date - relativedelta(years=periods_back)
    else:
        # Default to days
        return base_date - datetime.timedelta(days=periods_back)