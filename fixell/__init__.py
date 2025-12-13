"""Fixell - Zdalna naprawa systemu Linux z AI"""
__version__ = "0.1.0"
__author__ = "wronai"

from .server import FixellServer, DEFAULT_PORT, DEFAULT_MODEL, SYSTEM_PROMPT
from .client import FixellClient, parse_address
from .utils import extract_commands, is_dangerous_command
