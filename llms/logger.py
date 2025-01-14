import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger("AgenticAI")
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
file_handler = RotatingFileHandler(
    "agentic_ai.log", maxBytes=5 * 1024 * 1024, backupCount=3
)

console_handler.setLevel(logging.INFO)
file_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)
