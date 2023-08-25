from attrs import define

@define(frozen=True)
class Scrub:
    plan: int = 8
    older_than: int = 10
