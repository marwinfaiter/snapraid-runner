from typing import Optional
from attrs import define

@define(frozen=True)
class SMTP:
    host: str
    port: Optional[int]
    user: str
    password: str
    ssl: bool = False
    tls: bool = False
