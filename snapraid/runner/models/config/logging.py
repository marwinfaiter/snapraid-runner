from attrs import define

@define(frozen=True)
class Logging:
    file: str
    max_size: int
