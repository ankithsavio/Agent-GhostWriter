import logging
import asyncio
from logging.handlers import QueueHandler

log_queue = asyncio.Queue()

queue_handler = QueueHandler(log_queue)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(queue_handler)
