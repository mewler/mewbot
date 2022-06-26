# Loads a file in, sees if it works

from __future__ import annotations

from typing import Type

from tests.common import BaseTestClassWithConfig

from mewbot.io.discord import DiscordIO
from mewbot.api.v1 import IOConfig

# pylint: disable=R0903
#  Disable "too few public methods" for test cases - most test files will be classes used for
#  grouping and then individual tests alongside these


class TestIoHttpsPost(BaseTestClassWithConfig[DiscordIO]):
    config_file: str = "examples/trivial_discord_bot.yaml"
    implementation: Type[DiscordIO] = DiscordIO

    def test_check_class(self) -> None:
        assert isinstance(self.component, DiscordIO)
        assert isinstance(self.component, IOConfig)
