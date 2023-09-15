from attrs import define
from typing import Optional

from .email import EmailConfig
from .discord_config import DiscordConfig

@define
class Notify:
    email: Optional[EmailConfig] = None
    discord: Optional[DiscordConfig] = None
