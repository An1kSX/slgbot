import logging
import os
from logging.handlers import RotatingFileHandler


logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

handler = RotatingFileHandler(
	os.getenv("LOG_FILE", "logs.log"),
	maxBytes=5_000_000,
	backupCount=2,
)
handler.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

if not logger.handlers:
	logger.addHandler(handler)
