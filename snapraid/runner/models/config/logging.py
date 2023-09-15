from attrs import define

@define
class Logging:
    file: str
    max_size: int
