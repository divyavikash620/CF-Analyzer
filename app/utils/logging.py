import logging

from pythonjsonlogger import jsonlogger

from app.core.config import get_settings


def setup_logging() -> None:
    """Configure a JSON-style structured logger for the app."""
    settings = get_settings()
    handler = logging.StreamHandler()
    fmt = jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    handler.setFormatter(fmt)

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
