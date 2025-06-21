"""
Configuration module for AI Voice Agent
Re-exports settings from config.settings for backward compatibility
"""

from .config.settings import *  # noqa
from .config.settings import ServiceConfig

# Create a settings instance for easy access
settings = ServiceConfig()
