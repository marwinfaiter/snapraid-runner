from attrs import define, field
from discord import SyncWebhook


@define(frozen=True)
class DiscordConfig:
    webhook: SyncWebhook = field(converter=SyncWebhook.from_url) # type: ignore[misc]
