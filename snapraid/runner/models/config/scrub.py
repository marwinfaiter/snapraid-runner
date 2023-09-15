from attrs import define

@define
class Scrub:
    plan: int = 8
    older_than: int = 10
