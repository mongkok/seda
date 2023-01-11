import logging
import sys
import typing as t
from copy import copy

import click

if sys.version_info < (3, 8):  # pragma: no cover
    from typing_extensions import Literal
else:  # pragma: no cover
    from typing import Literal


LOGGING_CONFIG: t.Dict[str, t.Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "seda.logging.DefaultFormatter",
            "fmt": "%(level)s %(message)s",
            "use_colors": True,
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
    },
    "loggers": {
        "seda": {"handlers": ["default"], "level": "INFO", "propagate": False},
    },
}


class DefaultFormatter(logging.Formatter):
    colors = {
        logging.DEBUG: lambda level: click.style(str(level), fg="cyan"),
        logging.INFO: lambda level: click.style(str(level), fg="green"),
        logging.WARNING: lambda level: click.style(str(level), fg="yellow"),
        logging.ERROR: lambda level: click.style(str(level), fg="red"),
        logging.CRITICAL: lambda level: click.style(str(level), fg="bright_red"),
    }

    def __init__(
        self,
        fmt: t.Optional[str] = None,
        datefmt: t.Optional[str] = None,
        style: Literal["%", "{", "$"] = "%",
        use_colors: t.Optional[bool] = None,
    ):
        if use_colors is None:
            use_colors = sys.stdout.isatty()
        self.use_colors = use_colors
        super().__init__(fmt=fmt, datefmt=datefmt, style=style)

    def formatMessage(self, record: logging.LogRecord) -> str:
        rec = copy(record)
        levelname = rec.levelname
        if self.use_colors:
            levelname = self.colors.get(rec.levelno, str)(levelname)
        rec.__dict__["level"] = f"{levelname}:{' ' * (8 - len(rec.levelname))}"
        return super().formatMessage(rec)
