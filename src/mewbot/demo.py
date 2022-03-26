from __future__ import annotations

from typing import Set, Type

from mewbot.core import InputEvent
from mewbot.api.v1 import Condition


class Foo(Condition):
    @staticmethod
    def consumes_inputs() -> Set[Type[InputEvent]]:
        return set()

    _channel: str

    def __init__(self) -> None:
        if not hasattr(self, "_channel"):
            self._channel = "oops"

    @property
    def channel(self) -> str:
        return self._channel

    @channel.setter
    def channel(self, val: str) -> None:
        self._channel = val

    def allows(self, event: InputEvent) -> bool:
        return True

    def __str__(self) -> str:
        return f"Foo(channel={self.channel})"
