from typing import Any, Optional

from attrs import define


@define
class Scrub:
    plan: Any
    older_than: Optional[int] = None
