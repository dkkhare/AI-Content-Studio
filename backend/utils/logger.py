from pathlib import Path
from loguru import logger

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logger.remove()

logger.add(
    LOG_DIR / "studio.log",
    rotation="10 MB",
    retention="30 days",
    level="INFO",
    enqueue=True,
)

logger.add(
    lambda msg: print(msg, end=""),
    level="INFO",
)