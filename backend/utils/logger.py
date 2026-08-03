from loguru import logger

from backend.core.constants import LOGS_DIR

logger.remove()

logger.add(
    LOGS_DIR / "application.log",
    rotation="10 MB",
    retention="30 days",
    enqueue=True,
)

logger.add(
    lambda msg: print(msg, end="")
)