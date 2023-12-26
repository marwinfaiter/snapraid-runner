import re

from attrs import define
from cattrs import structure

from .disk import Disk

DISK_REGEX = r"^\s*(?P<files>\d+)\s+(?P<fragmented_files>\d+)\s+(?P<excess_fragments>\d+)\s+(?P<wasted_gb>[\d\.-]+)\s+(?P<used_gb>\d+)\s+(?P<free_gb>\d+)\s+(?P<use>\d+%)(?:$|\s+(?P<name>\w+$))"

@define
class Report:
    disks: list[Disk]
    total: Disk

    @classmethod
    def parse_report(cls, report_string: str) -> "Report":
        disks = []
        for line in report_string.split("\n"):
            if disk_match := re.match(DISK_REGEX, line):
                disks.append(structure(disk_match.groupdict(), Disk))

        return cls(
            total=disks.pop(-1),
            disks=disks
        )
