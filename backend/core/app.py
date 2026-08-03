"""
Main application class.
"""

from backend.utils.filesystem import ensure_directories
from backend.utils.logger import logger


class Application:

    def initialize(self):

        ensure_directories()

        logger.info("Application initialized.")