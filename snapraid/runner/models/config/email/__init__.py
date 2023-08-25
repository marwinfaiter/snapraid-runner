from attrs import define

from .smtp import SMTP

@define(frozen=True)
class EmailConfig:
    from_email: str
    to_email: str
    subject: str
    smtp: SMTP
    short: bool = False
    max_size: int = 500
