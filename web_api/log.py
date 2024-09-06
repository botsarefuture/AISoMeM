import logging

# Set up logging configuration
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("AISoMeM")
logger.setLevel(logging.DEBUG)  # Set the logging level to DEBUG
