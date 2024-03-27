from unittest import TestCase

from snapraid.runner.models.status import Status
from snapraid.runner.models.status.report import Report
from snapraid.runner.models.status.report.disk import Disk
from snapraid.runner.models.status.scrub_age import ScrubAge


class TestParseStatus(TestCase):
    def test_perfect_state(self) -> None:
        status = Status.parse_status(PERFECT_STATE)
        assert status.warnings == ["With 7 disks it's recommended to use two parity levels."]
        assert status.report == Report(
            [
                Disk(8490, 33, 227, "-", 9967, 1931, "83%", "Meh1"),
                Disk(53519, 102, 638, "-", 15159, 2759, "84%", "Meh2"),
                Disk(8736, 55, 453, "-", 6646, 1287, "83%", "Meh4"),
                Disk(63902, 174, 2855, "-", 15161, 2760, "84%", "Meh5"),
                Disk(7964, 23, 101, "-", 9959, 1929, "83%", "Meh6"),
                Disk(20515, 150, 991, "-", 11630, 2253, "83%", "Meh8"),
                Disk(23690, 447, 7889, 58.9, 17052, 2803, "85%", "Meh9"),
            ],
            Disk(186816, 984, 13154, 58.9, 85576, 15725, "84%")
        )
        assert status.scrub_age == ScrubAge(7, 3, 0)
        assert status.sync_in_progress is False
        assert status.percent_array_scrubbed == 100
        assert status.files_sub_second_timestamp == 0



PERFECT_STATE = [
    "Self test...",
    "Loading state from /var/snapraid.content...",
    "WARNING! With 7 disks it's recommended to use two parity levels.",
    "Using 5637 MiB of memory for the file-system.",
    "SnapRAID status report:",
    "",
    "Files Fragmented Excess  Wasted  Used    Free  Use Name",
    "Files  Fragments  GB      GB      GB",
    "8490      33     227       -    9967    1931  83% Meh1",
    "53519     102     638       -   15159    2759  84% Meh2",
    "8736      55     453       -    6646    1287  83% Meh4",
    "63902     174    2855       -   15161    2760  84% Meh5",
    "7964      23     101       -    9959    1929  83% Meh6",
    "20515     150     991       -   11630    2253  83% Meh8",
    "23690     447    7889    58.9   17052    2803  85% Meh9",
    "--------------------------------------------------------------------------",
    "186816     984   13154    58.9   85576   15725  84%",
    "",
    "",
    "22%|                                *",
       "|                                *",
       "|                                *",
       "|                                *     *",
       "|                                *     *",
       "|                                *     *",
       "|                                *     *",
    "11%|                                *     *",
       "|                                *     *",
       "|*     * *  *         *      *  **     *",
       "|*     * *  *         *      *  **     *",
       "|*     * *  *         *      *  **     *",
       "|*     * *  *         *      *  **     *       *",
       "|*     * *  *         *      *  **     *       *  *",
     "0%|*_____*_*__*_________*______*__**_____*_____*_*__*__*___*__*_*__*_*__*",
        "7                    days ago of the last scrub/sync                 0",
    "",
    "The oldest block was scrubbed 7 days ago, the median 3, the newest 0.",
    "",
    "No sync is in progress.",
    "The full array was scrubbed at least one time.",
    "No file has a zero sub-second timestamp.",
    "No rehash is in progress or needed.",
    "No error detected.",
]
