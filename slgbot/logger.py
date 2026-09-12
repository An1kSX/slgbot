import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

if not logger.handlers:
	log_path = Path(os.getenv("LOG_FILE", "data/runtime/logs.log"))
	log_path.parent.mkdir(parents=True, exist_ok=True)
	handler = RotatingFileHandler(log_path, maxBytes=5_000_000, backupCount=2, encoding="utf-8")
	handler.setFormatter(formatter)
	logger.addHandler(handler)
	console = logging.StreamHandler()
	console.setFormatter(formatter)
	logger.addHandler(console)
