import re

from attrs import define
from cattrs import structure

SCRUB_AGE_REGEX = r"The oldest block was scrubbed (?P<oldest>\d+) days ago, the median (?P<median>\d+), the newest (?P<newest>\d+)."

@define
class ScrubAge:
    oldest: int
    median: int
    newest: int

    @classmethod
    def parse_scrub_age(cls, scrub_age_string: str) -> "ScrubAge":
        scrub_age_match = re.match(SCRUB_AGE_REGEX, scrub_age_string)
        assert scrub_age_match is not None
        return structure(scrub_age_match.groupdict(), cls)
