from typing import Optional, Union

from attrs import define, field


def wasted_gb_converter(value: Union[str, int, float]) -> float:
    return float(value) if value != "-" else 0

@define
class Disk:
    files: int = field(converter=int)
    fragmented_files: int = field(converter=int)
    excess_fragments: int = field(converter=int)
    wasted_gb: Union[float, int, str] = field(converter=wasted_gb_converter)
    used_gb: int = field(converter=int)
    free_gb: int = field(converter=int)
    use: str
    name: Optional[str] = None
