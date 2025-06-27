"""Input validation utilities and custom validators"""
import re
from typing import Any
from pydantic import validator
import html

# Spotify ID validation pattern
SPOTIFY_ID_PATTERN = re.compile(r'^[0-9A-Za-z]{22}$')

def validate_spotify_id(value: str) -> str:
    """Validate Spotify ID format"""
    if not isinstance(value, str):
        raise ValueError("Spotify ID must be a string")
    
    # Remove any whitespace
    value = value.strip()
    
    if not value:
        raise ValueError("Spotify ID cannot be empty")
    
    if not SPOTIFY_ID_PATTERN.match(value):
        raise ValueError("Invalid Spotify ID format. Must be 22 alphanumeric characters")
    
    return value

def sanitize_search_query(value: str) -> str:
    """Sanitize search query input"""
    if not isinstance(value, str):
        raise ValueError("Search query must be a string")
    
    # Remove any whitespace from start/end
    value = value.strip()
    
    if not value:
        raise ValueError("Search query cannot be empty")
    
    if len(value) > 200:
        raise ValueError("Search query too long (max 200 characters)")
    
    # HTML escape to prevent XSS
    value = html.escape(value)
    
    # Remove potentially dangerous characters for Elasticsearch
    dangerous_chars = ['\\', '/', '"', "'", '<', '>', '&', '\n', '\r', '\t']
    for char in dangerous_chars:
        value = value.replace(char, ' ')
    
    # Collapse multiple spaces
    value = re.sub(r'\s+', ' ', value).strip()
    
    return value

def validate_username(value: str) -> str:
    """Validate username format"""
    if not isinstance(value, str):
        raise ValueError("Username must be a string")
    
    value = value.strip()
    
    if not value:
        raise ValueError("Username cannot be empty")
    
    if len(value) < 3:
        raise ValueError("Username must be at least 3 characters long")
    
    if len(value) > 50:
        raise ValueError("Username too long (max 50 characters)")
    
    # Only allow alphanumeric, underscore, and hyphen
    if not re.match(r'^[a-zA-Z0-9_-]+$', value):
        raise ValueError("Username can only contain letters, numbers, underscore, and hyphen")
    
    return value.lower()

def validate_email(value: str) -> str:
    """Validate email format"""
    if not isinstance(value, str):
        raise ValueError("Email must be a string")
    
    value = value.strip().lower()
    
    if not value:
        raise ValueError("Email cannot be empty")
    
    # Basic email regex (more comprehensive than simple @ check)
    email_pattern = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    if not email_pattern.match(value):
        raise ValueError("Invalid email format")
    
    if len(value) > 255:
        raise ValueError("Email too long (max 255 characters)")
    
    return value

def validate_password(value: str) -> str:
    """Validate password strength"""
    if not isinstance(value, str):
        raise ValueError("Password must be a string")
    
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters long")
    
    if len(value) > 128:
        raise ValueError("Password too long (max 128 characters)")
    
    # Check for at least one uppercase, lowercase, and number
    has_upper = any(c.isupper() for c in value)
    has_lower = any(c.islower() for c in value)
    has_digit = any(c.isdigit() for c in value)
    
    if not (has_upper and has_lower and has_digit):
        raise ValueError("Password must contain at least one uppercase letter, one lowercase letter, and one number")
    
    return value

# Custom Pydantic validators that can be used in schemas
class SpotifyIdValidator:
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, value: Any) -> str:
        return validate_spotify_id(value)

class SearchQueryValidator:
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, value: Any) -> str:
        return sanitize_search_query(value)
