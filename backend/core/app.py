from backend.utils.logger import logger
from backend.utils.filesystem import ensure_directories
from backend.config.settings import settings


class Application:
    def initialize(self):
        ensure_directories()

        logger.info("====================================")
        logger.info("AI Content Studio")
        logger.info("Application Started")
        logger.info("====================================")

        logger.info(
            f"Theme : {settings.get('application','theme')}"
        )

        logger.info(
            f"Language : {settings.get('application','language')}"
        )

        logger.info(
            "Initialization completed."
        )