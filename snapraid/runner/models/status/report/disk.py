from typing import Optional, Union

from attrs import define, field


def wasted_gb_converter(value: str) -> Union[int,float,str]:
    return float(value) if value != "-" else value

@define
class Disk:
    files: int = field(converter=int)
    fragmented_files: int = field(converter=int)
    excess_fragments: int = field(converter=int)
    wasted_gb: Union[int,float,str] = field(converter=wasted_gb_converter)
    used_gb: int = field(converter=int)
    free_gb: int = field(converter=int)
    use: str
    name: Optional[str] = None
