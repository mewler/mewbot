#!/usr/bin/env python3

from __future__ import annotations

from typing import Any, Dict, Set, Type

import dataclasses

from mewbot.behaviour import Trigger, Condition, Action
from mewbot.io import InputEvent, OutputEvent
from mewbot.data import DataSource


@dataclasses.dataclass
class TextInputEvent(InputEvent):
    message: str


@dataclasses.dataclass
class TwitchChatMessage(TextInputEvent):
    channel: str
    user: str


@dataclasses.dataclass
class TwitchChatMessageOutput(OutputEvent):
    channel: str
    message: str


class TwitchChatMessageCommandTrigger(Trigger):
    @staticmethod
    def consumes_inputs() -> Set[Type[InputEvent]]:
        return {TwitchChatMessage}

    def matches(self, event: InputEvent) -> bool:
        if not isinstance(event, TwitchChatMessage):
            return False

        return event.message.startswith("!help")


class TwitchCommandModOnlyCondition(Condition):
    @staticmethod
    def consumes_inputs() -> Set[Type[InputEvent]]:
        return {TwitchChatMessage}

    def allows(self, event: InputEvent) -> bool:
        if not isinstance(event, TwitchChatMessage):
            return False

        return event.user == "kitteh"


class PickUnhelpfulMessageAction(Action):
    @staticmethod
    def consumes_inputs() -> Set[Type[InputEvent]]:
        return {TwitchChatMessage}

    @staticmethod
    def produces_outputs() -> Set[Type[OutputEvent]]:
        return set()

    @property
    def message_store(self) -> DataSource[str]:
        return self._store

    @message_store.setter
    def message_store(self, store: DataSource[str]) -> None:
        self._store = store

    def act(self, event: InputEvent, state: Dict[str, Any]) -> None:
        state["message"] = self._store.get()


class SendReplyToTwitch(Action):
    @staticmethod
    def consumes_inputs() -> Set[Type[InputEvent]]:
        return {TwitchChatMessage}

    @staticmethod
    def produces_outputs() -> Set[Type[OutputEvent]]:
        return {TwitchChatMessageOutput}

    def act(self, event: InputEvent, state: Dict[str, Any]) -> None:
        if not isinstance(event, TwitchChatMessage):
            return

        message = TwitchChatMessageOutput(
            channel=event.channel,
            message=event.message,
        )

        self.send(message)


class SendMessageToTwitch(Action):
    _channel: str

    @staticmethod
    def consumes_inputs() -> Set[Type[InputEvent]]:
        return {TextInputEvent}

    @staticmethod
    def produces_outputs() -> Set[Type[OutputEvent]]:
        return {TwitchChatMessageOutput}

    @property
    def twitch_channel(self) -> str:
        return self._channel

    @twitch_channel.setter
    def twitch_channel(self, channel: str) -> None:
        self._channel = channel

    def act(self, event: InputEvent, state: Dict[str, Any]) -> None:
        if not isinstance(event, TextInputEvent):
            return

        message = TwitchChatMessageOutput(
            channel=self.twitch_channel,
            message=event.message,
        )

        self.send(message)


# ============================================================================


def main() -> None:
    from mewbot.component import (  # pylint: disable=import-outside-toplevel
        Component,
        load_from_config,
    )

    class Foo(Component):
        _channel: str

        def __init__(self, **k: Any) -> None:
            super().__init__()

            if not hasattr(self, "_channel"):
                self._channel = "oops"

        @property
        def channel(self) -> str:
            return self._channel

        @channel.setter
        def channel(self, val: str) -> None:
            print(f"Setting channel to {val}")
            self._channel = val

        def __str__(self) -> str:
            return f"Foo(channel={self.channel})"

    demo = Foo(channel="foo")
    print(demo)
    demo.channel = "cat"
    print(demo.serialise())
    print(load_from_config(demo.serialise()))


if __name__ == "__main__":
    main()
