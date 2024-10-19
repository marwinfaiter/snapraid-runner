#!/usr/bin/env python3
import logging
import re
import smtplib
import subprocess
from email import charset
from email.mime.text import MIMEText
from io import StringIO, TextIOWrapper
from typing import Optional

import yaml
from cattrs import structure
from discord import Colour, Embed

from .models.cli_args import CLIArgs
from .models.command import Command
from .models.config import Config
from .models.config.discord_config import DiscordConfig
from .models.config.email import EmailConfig
from .models.config.scrub import Scrub
from .models.diff import Diff
from .models.log_levels import OUTPUT
from .models.loggers import Loggers
from .models.state import State
from .models.status import Status


class SnapraidRunner:
    def __init__(self) -> None:
        self.cli_args = CLIArgs().parse_args()
        self.config = self._get_config()
        self.loggers = Loggers.create_loggers(self.config)
        self.state = State.SUCCESS
        self.diff_output: Optional[Diff] = None
        self.status_output: Optional[Status] = None
        self.error: Optional[str] = None

    def _get_config(self) -> Config:
        with open(self.cli_args.config, encoding="utf-8") as f:
            config_dict = yaml.full_load(f) or {}
            config = structure(config_dict, Config)
            if self.cli_args.scrub is True and not config.scrub:
                config.scrub = [Scrub(plan=8, older_than=10)]
            return config

    def touch(self) -> list[str]:
        return self.run_snapraid(Command.TOUCH)

    def sync(self) -> list[str]:
        return self.run_snapraid(Command.SYNC)

    def scrub(self, scrub_args: Scrub) -> list[str]:
        return self.run_snapraid(Command.SCRUB, scrub_args)

    def status(self) -> Status:
        return Status.parse_status(self.run_snapraid(Command.STATUS))

    def diff(self) -> Diff:
        output = self.run_snapraid(Command.DIFF)
        diff_dict = {}
        for line in output:
            if match := re.match(r"\s+(\d+) (equal|added|removed|updated|moved|copied|restored)", line):
                diff_dict[match.group(2)] = int(match.group(1))

        self.diff_output = structure(diff_dict, Diff)

        if self.config.delete_threshold is None or self.cli_args.ignore_delete_threshold is True:
            return self.diff_output

        if self.diff_output.removed > self.config.delete_threshold:
            raise ValueError(
                f"""Deleted files exceed delete threshold of {self.config.delete_threshold}
                Run again with --ignore_delete_threshold to ignore"""
            )

        return self.diff_output

    def run_snapraid(self, command: Command, scrub_args: Optional[Scrub]=None) -> list[str]:
        logging.info("Running %s...", command.value)
        args = [
            "snapraid",
            command.value
        ]

        if command == Command.SCRUB:
            assert isinstance(scrub_args, Scrub)
            args.extend(["--plan", str(scrub_args.plan)])
            if scrub_args.older_than:
                args.extend(["--older-than", str(scrub_args.older_than)])

        with subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            encoding="utf-8", errors="replace"
        ) as process:
            try:
                stdout = []
                assert isinstance(process.stdout, TextIOWrapper)
                for line in iter(process.stdout.readline, ""):
                    logging.log(OUTPUT, line.rstrip())
                    stdout.append(line.rstrip())

                # assert isinstance(process.stderr, TextIOWrapper)
                # for line in iter(process.stderr.readline, ""):
                #     logging.log(OUTERR, line.rstrip())
                logging.info("*" * 60)
                return stdout
            except KeyboardInterrupt:
                process.terminate()
                process.wait()
                raise

    def notify(self) -> None:
        if self.config.notify.email:
            self.notify_email()
        if self.config.notify.discord:
            self.notify_discord()

    def notify_email(self) -> None:
        assert isinstance(self.config.notify.email, EmailConfig)
        # use quoted-printable instead of the default base64
        charset.add_charset("utf-8", charset.SHORTEST, charset.QP)

        assert isinstance(self.loggers.email_logger, logging.StreamHandler)
        assert isinstance(self.loggers.email_logger.stream, StringIO)
        body = self.loggers.email_logger.stream.getvalue()
        maxsize = self.config.notify.email.max_size * 1024
        if maxsize and len(body) > maxsize:
            cut_lines = body.count("\n", maxsize // 2, -maxsize // 2)
            body = (
                "NOTE: Log was too big for email and was shortened\n\n"
                f"{body[:maxsize // 2]}"
                f"[...]\n\n\n --- LOG WAS TOO BIG - {cut_lines} LINES REMOVED --\n\n\n[...]"
                f"{body[-maxsize // 2:]}"
            )

        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = f"self.config.notify.email.subject: {self.state.name.title()}"
        msg["From"] = self.config.notify.email.from_email
        msg["To"] = self.config.notify.email.to_email
        server: smtplib.SMTP_SSL | smtplib.SMTP
        if self.config.notify.email.smtp.ssl:
            server = smtplib.SMTP_SSL(
                host=self.config.notify.email.smtp.host,
                port=self.config.notify.email.smtp.port or 0,
                timeout=5
            )
        else:
            server = smtplib.SMTP(
                host=self.config.notify.email.smtp.host,
                port=self.config.notify.email.smtp.port or 0,
                timeout=5
            )
            if self.config.notify.email.smtp.tls:
                server.starttls()
        if self.config.notify.email.smtp.user:
            server.login(self.config.notify.email.smtp.user, self.config.notify.email.smtp.password)
        server.sendmail(
            self.config.notify.email.from_email,
            [self.config.notify.email.to_email],
            msg.as_string())
        server.quit()

    def notify_discord(self) -> None:
        assert isinstance(self.config.notify.discord, DiscordConfig)
        embed = Embed(
            color=Colour.green() if self.state == State.SUCCESS else Colour.red(),
            title=f"Snapraid summary: {self.state.name.title()}",
        )
        if self.diff_output:
            embed.add_field(name="Diff", value="No changes" if not self.diff_output.changes else "", inline=False)
            if self.diff_output.changes:
                embed.add_field(name="Added", value=self.diff_output.added)
                embed.add_field(name="Removed", value=self.diff_output.removed)
                embed.add_field(name="", value="", inline=False)
                embed.add_field(name="Moved", value=self.diff_output.moved)
                embed.add_field(name="Updated", value=self.diff_output.updated)
        if self.error:
            embed.description = self.error
        elif self.status_output:
            embed.description = str(self.status_output)

        self.config.notify.discord.webhook.send(embed=embed)

def main() -> None:
    snapraid_runner = SnapraidRunner()
    try:
        logging.info("=" * 60)
        logging.info("Run started")
        logging.info("=" * 60)
        diff = snapraid_runner.diff()
        if diff.changes:
            snapraid_runner.sync()
        else:
            logging.info("No changes detected, no sync required")

        snapraid_runner.status_output = snapraid_runner.status()
        if snapraid_runner.config.touch and snapraid_runner.status_output.files_sub_second_timestamp:
            snapraid_runner.touch()

        if snapraid_runner.config.scrub:
            for scrub in snapraid_runner.config.scrub:
                snapraid_runner.scrub(scrub)

        snapraid_runner.status_output = snapraid_runner.status()

        logging.info("All done")
        logging.info(snapraid_runner.state.value)
    except Exception as e_string: # pylint: disable=broad-exception-caught
        logging.exception("Run failed due to unexpected exception: %s", e_string)
        snapraid_runner.error = str(e_string)
        snapraid_runner.state = State.FAILED
        logging.error(snapraid_runner.state.value)
    except KeyboardInterrupt:
        snapraid_runner.state = State.KEYBOARD_INTERRUPT
        logging.error(snapraid_runner.state.value)
    finally:
        snapraid_runner.notify()

if __name__ == "__main__":
    main()
