import os
from logging import error
from typing import Optional

from attrs import define, field

from .logging import Logging
from .notify import Notify
from .scrub import Scrub


@define
class Config:
    executable: str = "/usr/bin/snapraid"
    config: str = "/etc/snapraid.conf"
    logging: Optional[Logging] = None
    touch: bool = False
    delete_threshold: Optional[int] = None
    notify: Notify = field(factory=Notify)
    scrub: list[Scrub] = field(factory=list)

    def __attrs_post_init__ (self) -> None:
        if not os.path.isfile(self.executable):
            error_string = f"The configured snapraid executable {self.executable!r} does not exist or is not a file"
            error(error_string)
            raise RuntimeError(error_string)

        if not os.path.isfile(self.config):
            error_string = f"Snapraid config does not exist at {self.config!r}"
            error(error_string)
            raise RuntimeError(error_string)
