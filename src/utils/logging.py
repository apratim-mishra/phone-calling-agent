import sys
from pathlib import Path

from loguru import logger

from src.config import settings


def setup_logging() -> None:
    """Configure loguru for the application."""
    logger.remove()

    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    logger.add(
        sys.stderr,
        format=log_format,
        level=settings.log_level,
        colorize=True,
    )

    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    logger.add(
        log_dir / "app.log",
        format=log_format,
        level=settings.log_level,
        rotation="10 MB",
        retention="7 days",
        compression="zip",
    )

    logger.add(
        log_dir / "error.log",
        format=log_format,
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
    )


def get_logger(name: str):
    """Get a logger instance with the given name."""
    return logger.bind(name=name)

