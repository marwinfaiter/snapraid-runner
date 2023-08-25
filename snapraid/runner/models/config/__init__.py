from attrs import define, field
from typing import Optional
import os
from logging import error

from .notify import Notify
from .scrub import Scrub
from .logging import Logging

@define(frozen=True)
class Config:
    executable: str = "/usr/bin/snapraid"
    config: str = "/etc/snapraid.conf"
    logging: Optional[Logging] = None
    touch: bool = False
    delete_threshold: Optional[int] = None
    notify: Notify = field(factory=Notify)
    scrub: Optional[Scrub] = None

    def __attrs_post_init__ (self) -> None:
        if not os.path.isfile(self.executable):
            error_string = f"The configured snapraid executable {self.executable!r} does not exist or is not a file"
            error(error_string)
            raise RuntimeError(error_string)

        if not os.path.isfile(self.config):
            error_string = f"Snapraid config does not exist at {self.config!r}"
            error(error_string)
            raise RuntimeError(error_string)
