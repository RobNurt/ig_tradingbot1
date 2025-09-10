# This file is for centralized logging configuration.
import logging

def setup_logging():
    """
    Sets up a basic logging configuration.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler()
        ]
    )
    logging.info("Logging setup complete.")
