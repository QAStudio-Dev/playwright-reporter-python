"""
QAStudio pytest plugin for test management integration.

This plugin automatically reports pytest test results to QAStudio.dev platform.
"""

__version__ = "1.0.5"
__author__ = "QAStudio"
__email__ = "support@qastudio.dev"

from .plugin import QAStudioPlugin

__all__ = ["QAStudioPlugin"]
