import logging
import yaml
import os

log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

with open("config/logging.yaml", "r") as file:
    config = yaml.safe_load(file)

logging.basicConfig(
    level=getattr(logging, config["loggers"]["deep_research"]["level"]),
    format=config["formatters"]["simple"]["format"],
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config["handlers"]["file"]["filename"])
    ]
)

logger = logging.getLogger("deep_research")

logger.debug("This is a DEBUG message")
logger.info("This is an INFO message")
logger.warning("This is a WARNING message")
logger.error("This is an ERROR message")
logger.critical("This is a CRITICAL message")

print("✅ Logging test completed. Check logs/deep_research.log")
