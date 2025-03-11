import logging
import logging.handlers
import os
import sys
from datetime import datetime

# Create logs directory if it doesn't exist
logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)


# Set up logging
def setup_logger() -> logging.Logger:
    """
    Set up a logger with a memory handler to store recent logs and a file handler to save logs to a file.
    Returns:
        logging.Logger: The configured logger.
    """
    logger = logging.getLogger("chess_divergence")
    logger.setLevel(logging.DEBUG)

    # Memory handler to store recent logs
    memory_handler = logging.handlers.MemoryHandler(capacity=100)  # Store last 100 log records
    memory_handler.setLevel(logging.DEBUG)
    memory_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    memory_handler.setFormatter(memory_format)
    logger.addHandler(memory_handler)

    # File handler for debug and above
    log_filename = os.path.join(logs_dir, f'chess_divergence_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(file_format)

    # Console handler for info and above
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_format)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# Create and export logger
logger = setup_logger()
