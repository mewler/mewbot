from __future__ import annotations

from typing import Set, Type, Dict, Any

from mewbot.core import InputEvent, OutputEvent
from mewbot.api.v1 import Condition, Trigger, Action


class Foo(Condition):
    @staticmethod
    def consumes_inputs() -> Set[Type[InputEvent]]:
        return set()

    _channel: str

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


class AllEventTrigger(Trigger):
    """
    Nothing fancy - just fires whenever there is an PostInputEvent.
    Will be used in the PrintBehavior.
    """

    @staticmethod
    def consumes_inputs() -> Set[Type[InputEvent]]:
        return {InputEvent}

    def matches(self, event: InputEvent) -> bool:
        return True


class PrintAction(Action):
    """
    Print every InputEvent.
    """

    @staticmethod
    def consumes_inputs() -> Set[Type[InputEvent]]:
        return {InputEvent}

    @staticmethod
    def produces_outputs() -> Set[Type[OutputEvent]]:
        return set()

    async def act(self, event: InputEvent, state: Dict[str, Any]) -> None:
        print("Processed event", event)
