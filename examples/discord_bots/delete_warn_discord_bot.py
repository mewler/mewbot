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
    DiscordMessageDeleteInputEvent,
    DiscordOutputEvent,
)


class DiscordDeleteEventTrigger(Trigger):
    """
    Nothing fancy - just fires whenever there is a DiscordDeleteEvent.
    """

    @staticmethod
    def consumes_inputs() -> Set[Type[InputEvent]]:
        return {
            DiscordMessageDeleteInputEvent,
        }

    def matches(self, event: InputEvent) -> bool:

        if isinstance(event, DiscordMessageDeleteInputEvent):
            return True

        return False


class DiscordDeleteResponseAction(Action):
    """
    Respond to every deletion event in the channel where the message was located.
    """

    _logger: logging.Logger
    _queue: OutputQueue
    _message: str = ""

    def __init__(self) -> None:
        super().__init__()
        self._logger = logging.getLogger(__name__ + type(self).__name__)

    @staticmethod
    def consumes_inputs() -> Set[Type[InputEvent]]:
        return {
            DiscordMessageDeleteInputEvent,
        }

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
            await self.send(test_event)

        self._logger.warning("Received wrong event type %s", type(event))
