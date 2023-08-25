#!/usr/bin/env python3
import logging
import subprocess
import re

import yaml
from cattrs import structure
from discord import Embed, Colour

import smtplib
from email.mime.text import MIMEText
from email import charset

from .models.cli_args import CLIArgs
from .models.config import Config
from .models.loggers import Loggers
from .models.diff import Diff
from .models.command import Command
from .models.status import Status

class SnapraidRunner:
    def __init__(self):
        self.cli_args = CLIArgs().parse_args()
        self.config = self._get_config()
        self.loggers = Loggers.create_loggers(self.config)
        self.diff_output = None
        self.status = Status.SUCCESS

    def _get_config(self):
        with open(self.cli_args.config) as f:
            config_dict = yaml.full_load(f) or {}
            return structure(config_dict, Config)

    def touch(self):
        self.run_snapraid(Command.TOUCH)

    def sync(self):
        self.run_snapraid(Command.SYNC)

    def scrub(self):
        self.run_snapraid(Command.SCRUB)

    def diff(self):
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

    def run_snapraid(self, command: Command):
        logging.info(f"Running {command.value}...")
        process = subprocess.Popen(
            [
                "snapraid",
                command.value,
                *(
                    [
                        "--plan", str(self.config.scrub.plan),
                        "--older-than", str(self.config.scrub.older_than)
                    ]
                    if all([
                        command == Command.SCRUB,
                        self.config.scrub,
                    ]) else []
                ),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            errors="replace"
        )
        stdout = []
        for line in iter(process.stdout.readline, ""):
            logging.log(logging.OUTPUT, line.rstrip())
            stdout.append(line)

        for line in iter(process.stderr.readline, ""):
            logging.log(logging.OUTERR, line.rstrip())
        logging.info("*" * 60)
        return stdout

    def notify(self):
        if self.config.notify.email:
            self.notify_email()
        if self.config.notify.discord:
            self.notify_discord()

    def notify_email(self):
        # use quoted-printable instead of the default base64
        charset.add_charset("utf-8", charset.SHORTEST, charset.QP)
        body = self.loggers.email_logger.stream.getvalue()
        maxsize = self.config.notify.email.max_size * 1024
        if maxsize and len(body) > maxsize:
            cut_lines = body.count("\n", maxsize // 2, -maxsize // 2)
            body = (
                "NOTE: Log was too big for email and was shortened\n\n" +
                body[:maxsize // 2] +
                "[...]\n\n\n --- LOG WAS TOO BIG - {} LINES REMOVED --\n\n\n[...]".format(
                    cut_lines) +
                body[-maxsize // 2:])

        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = f"self.config.notify.email.subject: {self.status.name.title()}"
        msg["From"] = self.config.notify.email.from_email
        msg["To"] = self.config.notify.email.to_email
        if self.config.notify.email.smtp.ssl:
            server = smtplib.SMTP_SSL(
                host=self.config.notify.email.smtp.host,
                port=self.config.notify.email.smtp.port,
                timeout=5
            )
        else:
            server = smtplib.SMTP(
                host=self.config.notify.email.smtp.host,
                port=self.config.notify.email.smtp.port,
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

    def notify_discord(self):
        embed = Embed(
            color=Colour.green() if self.status == Status.SUCCESS else Colour.red(),
            title=f"Snapraid summary: {self.status.name.title()}"
        )
        if self.diff_output:
            embed.add_field(name="Diff", value="No changes" if not self.diff_output.changes else "", inline=False)
            if self.diff_output.changes:
                embed.add_field(name="Added", value=self.diff_output.added)
                embed.add_field(name="Removed", value=self.diff_output.removed)
                embed.add_field(name="", value="", inline=False),
                embed.add_field(name="Moved", value=self.diff_output.moved)
                embed.add_field(name="Updated", value=self.diff_output.updated)
        self.config.notify.discord.webhook.send(embed=embed)

def main():
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
    except Exception as e_string:
        logging.exception(f"Run failed due to unexpected exception: {e_string}")
        snapraid_runner.status = Status.FAILED
        logging.error(snapraid_runner.status.value)
    finally:
        snapraid_runner.notify()
