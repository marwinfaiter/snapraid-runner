from typing import Optional
from tap import Tap

class CLIArgs(Tap):
    config: str = "/etc/snapraid-runner.yml"
    scrub: Optional[bool] = None
    ignore_delete_threshold: bool = False
