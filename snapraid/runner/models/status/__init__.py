import re

from attrs import define

from .report import Report
from .scrub_age import ScrubAge


@define
class Status:
    warnings: list[str]
    report: Report
    scrub_age: ScrubAge
    sync_in_progress: bool

    percent_array_scrubbed: int
    files_sub_second_timestamp: int
    rehash_needed: bool
    error: bool

    @classmethod
    def parse_status(cls, status: list[str]) -> "Status":
        percent_array_scrubbed = 100
        files_sub_second_timestamp = 0
        for line in status:
            if array_scrubbed_match := re.search(r"The (\d+)% of the array is not scrubbed\.", line):
                percent_array_scrubbed = 100 - int(array_scrubbed_match.group(1))

            if files_sub_second_timestamp_match := re.search(r"You have (\d+) files with zero sub-second timestamp\.", line):
                files_sub_second_timestamp = int(files_sub_second_timestamp_match.group(1))

        return cls(
            warnings=[warning.removeprefix("WARNING! ") for warning in filter(lambda l: re.search(r"^WARNING!.*", l), status)],
            report=Report.parse_report("\n".join(status).split("\n\n")[1]),
            scrub_age=ScrubAge.parse_scrub_age("\n".join(status).split("\n\n")[3]),
            sync_in_progress="No sync is in progress." not in status,
            percent_array_scrubbed=percent_array_scrubbed,
            files_sub_second_timestamp=files_sub_second_timestamp,
            rehash_needed="No rehash is in progress or needed." not in status,
            error="No error detected." not in status
        )

    def __str__(self) -> str:
        return (
            f"The oldest block was scrubbed {self.scrub_age.oldest}, the median {self.scrub_age.median}, the newest {self.scrub_age.newest}\n\n"
            f"Sync in progress: {self.sync_in_progress}\n"
            f"Percent of array scrubbed {self.percent_array_scrubbed}%\n"
            f"Files with zero sub-second timestamp: {self.files_sub_second_timestamp}\n"
            f"Rehash needed: {self.rehash_needed}\n"
            f"Error: {self.error}\n"
        )
