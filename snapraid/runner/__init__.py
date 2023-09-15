#!/usr/bin/env python3
import logging
import subprocess
import re
import smtplib
from email.mime.text import MIMEText
from email import charset
from io import TextIOWrapper, StringIO

import yaml
from cattrs import structure
from discord import Embed, Colour


from .models.cli_args import CLIArgs
from .models.config import Config
from .models.loggers import Loggers
from .models.diff import Diff
from .models.command import Command
from .models.status import Status
from .models.config.scrub import Scrub
from .models.log_levels import OUTPUT, OUTERR
from .models.config.email import EmailConfig
from .models.config.discord_config import DiscordConfig

class SnapraidRunner:
    def __init__(self) -> None:
        self.cli_args = CLIArgs().parse_args()
        self.config = self._get_config()
        self.loggers = Loggers.create_loggers(self.config)
        self.status = Status.SUCCESS
        self.diff_output: Diff

    def _get_config(self) -> Config:
        with open(self.cli_args.config, encoding="utf-8") as f:
            config_dict = yaml.full_load(f) or {}
            config = structure(config_dict, Config)
            if self.cli_args.scrub is not None:
                if self.cli_args.scrub is False:
                    config.scrub = None
                elif self.cli_args.scrub is True and not config.scrub:
                    config.scrub = Scrub()
            return config

    def touch(self) -> None:
        self.run_snapraid(Command.TOUCH)

    def sync(self) -> None:
        self.run_snapraid(Command.SYNC)

    def scrub(self) -> None:
        self.run_snapraid(Command.SCRUB)

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

    def run_snapraid(self, command: Command) -> list[str]:
        logging.info("Running %s...", command.value)
        args = [
            "snapraid",
            command.value,
        ]
        if all([command == Command.SCRUB, self.config.scrub]):
            assert isinstance(self.config.scrub, Scrub)
            args.extend([
                "--plan", str(self.config.scrub.plan),
                "--older-than", str(self.config.scrub.older_than)
            ])

        with subprocess.Popen(
            args,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            encoding="utf-8", errors="replace"
        ) as process:
            stdout = []
            assert isinstance(process.stdout, TextIOWrapper)
            for line in iter(process.stdout.readline, ""):
                logging.log(OUTPUT, line.rstrip())
                stdout.append(line)

            assert isinstance(process.stderr, TextIOWrapper)
            for line in iter(process.stderr.readline, ""):
                logging.log(OUTERR, line.rstrip())
            logging.info("*" * 60)
            return stdout

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
        msg["Subject"] = f"self.config.notify.email.subject: {self.status.name.title()}"
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
            color=Colour.green() if self.status == Status.SUCCESS else Colour.red(),
            title=f"Snapraid summary: {self.status.name.title()}"
        )
        if self.diff_output:
            embed.add_field(name="Diff", value="No changes" if not self.diff_output.changes else "", inline=False)
            if self.diff_output.changes:
                embed.add_field(name="Added", value=self.diff_output.added)
                embed.add_field(name="Removed", value=self.diff_output.removed)
                embed.add_field(name="", value="", inline=False)
                embed.add_field(name="Moved", value=self.diff_output.moved)
                embed.add_field(name="Updated", value=self.diff_output.updated)
        self.config.notify.discord.webhook.send(embed=embed)

def main() -> None:
    snapraid_runner = SnapraidRunner()
    try:
        logging.info("=" * 60)
        logging.info("Run started")
        logging.info("=" * 60)
        if snapraid_runner.config.touch:
            snapraid_runner.touch()
        diff = snapraid_runner.diff()
        if diff.changes:
            snapraid_runner.sync()
        else:
            logging.info("No changes detected, no sync required")

        if snapraid_runner.config.scrub or snapraid_runner.cli_args.scrub is True:
            snapraid_runner.scrub()

        logging.info("All done")
        logging.info(snapraid_runner.status.value)
    except Exception as e_string: # pylint: disable=broad-exception-caught
        logging.exception("Run failed due to unexpected exception: %s", e_string)
        snapraid_runner.status = Status.FAILED
        logging.error(snapraid_runner.status.value)
    finally:
        snapraid_runner.notify()

if __name__ == "__main__":
    main()
