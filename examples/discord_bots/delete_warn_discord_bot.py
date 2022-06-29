#!/usr/bin/env python3
# pylint: disable=duplicate-code
# this is an example - duplication for emphasis is desirable
# Aims to expose the full capabilities of this discord bot framework

from __future__ import annotations

from typing import Any, Dict, Set, Type

import logging

from mewbot.api.v1 import Trigger, Action
from mewbot.core import InputEvent, OutputEvent, OutputQueue
from mewbot.io.discord import (
    DiscordInputEvent,
    DiscordMessageCreationEvent,
    DiscordMessageDeleteInputEvent,
    DiscordOutputEvent,
)


class DiscordAllCommandTrigger(Trigger):
    """
    Nothing fancy - just fires whenever there is a DiscordTextInputEvent - of any type.
    """

    _command: str = ""

    @staticmethod
    def consumes_inputs() -> Set[Type[InputEvent]]:
        return {DiscordMessageCreationEvent, DiscordMessageDeleteInputEvent}

    @property
    def command(self) -> str:
        return self._command

    @command.setter
    def command(self, command: str) -> None:
        self._command = str(command)

    def matches(self, event: InputEvent) -> bool:

        if not isinstance(event, DiscordInputEvent):
            return False

        # Trigger on the preset command - and all edits
        if isinstance(event, DiscordMessageCreationEvent):
            return event.text == self._command

        if isinstance(event, DiscordMessageDeleteInputEvent):
            return True

        return False


class DiscordCommandTextAndDeleteResponse(Action):
    """
    Print every InputEvent.
    """

    _logger: logging.Logger
    _queue: OutputQueue
    _message: str = ""

    def __init__(self) -> None:
        super().__init__()
        self._logger = logging.getLogger(__name__ + type(self).__name__)

    @staticmethod
    def consumes_inputs() -> Set[Type[InputEvent]]:
        return {DiscordMessageCreationEvent, DiscordMessageDeleteInputEvent}

    @staticmethod
    def produces_outputs() -> Set[Type[OutputEvent]]:
        return {DiscordOutputEvent}

    @property
    def message(self) -> str:
        return self._message

    @message.setter
    def message(self, message: str) -> None:
        self._message = str(message)

    async def act(self, event: InputEvent, state: Dict[str, Any]) -> None:
        """
        Construct a DiscordOutputEvent with the result of performing the calculation.
        """
        if isinstance(event, DiscordMessageDeleteInputEvent):
            self._logger.info("We have detected deleting! - %s", event)
            test_event = DiscordOutputEvent(
                text=f'User {event.message.author} has deleted message: "{event.message.content}"',
                message=event.message,
                use_message_channel=True,
            )

        elif isinstance(event, DiscordMessageCreationEvent):
            test_event = DiscordOutputEvent(
                text=self._message, message=event.message, use_message_channel=True
            )

        else:
            self._logger.warning("Received wrong event type %s", type(event))
            return

        await self.send(test_event)
