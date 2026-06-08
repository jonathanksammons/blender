"""Structured, file-based logging for the add-on.

Logs go to a predictable per-user directory. We deliberately log *operations*
and *metadata* only -- never image binary data and never the contents of
portraits. The logger degrades gracefully when Blender is unavailable so it can
be imported by tests.
"""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path
from typing import Optional

from ..addon_info import ADDON_PACKAGE, addon_version_string

_LOGGER_NAME = "portrait_mesh_generator"
_configured = False


def _log_directory() -> Path:
    """Return (and create) the directory where log files live."""
    base: Optional[Path] = None
    try:  # Prefer Blender's user resource path when running inside Blender.
        import bpy  # type: ignore

        base = Path(bpy.utils.user_resource("CONFIG", path=ADDON_PACKAGE, create=True))
    except Exception:
        base = Path.home() / ".portrait_mesh_generator"
    log_dir = base / "logs"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        log_dir = Path.home() / ".portrait_mesh_generator" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def get_log_file() -> Path:
    return _log_directory() / "portrait_mesh_generator.log"


def configure(level: int = logging.INFO) -> logging.Logger:
    """Configure and return the package logger. Idempotent."""
    global _configured
    logger = logging.getLogger(_LOGGER_NAME)
    if _configured:
        logger.setLevel(level)
        return logger

    logger.setLevel(level)
    logger.propagate = False

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    try:
        file_handler = logging.handlers.RotatingFileHandler(
            get_log_file(), maxBytes=512 * 1024, backupCount=3, encoding="utf-8"
        )
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)
    except OSError:
        pass  # File logging unavailable; console handler still works.

    console = logging.StreamHandler()
    console.setFormatter(fmt)
    logger.addHandler(console)

    logger.info("Logging configured for %s v%s", ADDON_PACKAGE, addon_version_string())
    _configured = True
    return logger


def get_logger(child: Optional[str] = None) -> logging.Logger:
    base = logging.getLogger(_LOGGER_NAME)
    if not _configured:
        configure()
    return base.getChild(child) if child else base


def shutdown() -> None:
    """Detach handlers cleanly on add-on unregister."""
    global _configured
    logger = logging.getLogger(_LOGGER_NAME)
    for handler in list(logger.handlers):
        try:
            handler.flush()
            handler.close()
        finally:
            logger.removeHandler(handler)
    _configured = False
