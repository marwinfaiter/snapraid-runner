from attrs import define
from io import StringIO
import logging
import sys
from typing import Optional

from .config import Config


@define(frozen=True)
class Loggers:
    root_logger: logging.Logger
    console_logger: logging.StreamHandler
    file_logger: Optional[logging.Logger] = None
    email_logger: Optional[logging.StreamHandler] = None

    @classmethod
    def create_loggers(cls, config: Config) -> "Loggers":
        log_format = logging.Formatter("%(asctime)s [%(levelname)-6.6s] %(message)s")
        root_logger = logging.getLogger()
        logging.OUTPUT = 15
        logging.addLevelName(logging.OUTPUT, "OUTPUT")
        logging.OUTERR = 25
        logging.addLevelName(logging.OUTERR, "OUTERR")
        root_logger.setLevel(logging.OUTPUT)

        console_logger = logging.StreamHandler(sys.stdout)
        console_logger.setFormatter(log_format)

        root_logger.addHandler(console_logger)

        file_logger = None
        email_logger = None

        if config.logging:
            file_logger = logging.handlers.RotatingFileHandler(
                config.logging.file,
                maxBytes=max(config.logging.max_size, 0) * 1024,
                backupCount=9)
            file_logger.setFormatter(log_format)
            root_logger.addHandler(file_logger)

        if config.notify.email:
            email_logger = logging.StreamHandler(StringIO())
            email_logger.setFormatter(log_format)
            if config.notify.email.short:
                # Don't send programm stdout in email
                email_logger.setLevel(logging.INFO)
            root_logger.addHandler(email_logger)

        return cls(
            root_logger,
            console_logger,
            file_logger,
            email_logger,
        )
