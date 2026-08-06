from loguru import logger
import sys
from pathlib import Path


def configure_logging():

    Path("log").mkdir(exist_ok=True)

    #remove default logger
    logger.remove()

    # Logger configuration 1 for development 
    logger.add(
        sys.stdout,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level:<8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level> |"
            "<magenta>{extra}</magenta>"
        ),
        level="DEBUG",
        colorize=True
    )
    # Logger configuration 2 for production (filterable with grafana Loki)
    logger.add(
        "log/synapse_{time}.log",
        format="{message}",
        rotation="25 MB",
        compression="zip",
        serialize=True,
        retention="5 days",
        level="INFO",
    )


    # Logger configuration 3 for error handling

    logger.add(
        "log/synapse_error_{time}.log",
        format="{message}",
        rotation="30 MB",
        compression="zip",
        serialize=True,
        retention="15 days",
        level="WARNING",
    )


__all__ = ["logger", "configure_logging"]