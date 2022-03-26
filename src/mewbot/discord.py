# Aim - going to have one instance of pycord
#       Subclass

from typing import Any, Optional, Set, Type

import dataclasses
import logging

import discord  # type: ignore

from mewbot.core import InputEvent, InputQueue, OutputEvent
from mewbot.api.v1 import Input, Output


@dataclasses.dataclass
class DiscordInputEvent(InputEvent):
    """
    Ideally should contain enough messages/objects to actually respond to a message.
    """

    text: str
    message: discord.Message


class DiscordInput(Input):
    """
    Uses py-cord as a backend to connect, recieve and send messages to discord.
    """

    queue: Optional[InputQueue]
    token: str

    def __init__(self) -> None:
        super().__init__()

        # Needs to be set before startup
        self.token = ""

        self.logger = logging.getLogger(__name__ + "DiscordInput")

    def set_token(self, token: str) -> None:
        self.token = token

    @staticmethod
    def produces_inputs() -> Set[Type[InputEvent]]:
        """
        Defines the set of input events this Input class can produce.
        :return:
        """
        return {
            DiscordInputEvent,
        }

    async def run(self) -> None:
        """
        Fires up an aiohttp app to run the service.
        Token needs to be set by this point.
        """
        self.logger.info("About to connect to Discord")

        bot = DiscordInputEventClient(max_messages=4096)
        bot.queue = self.queue

        await bot.start(self.token)


class DiscordInputEventClient(discord.Client):  # type: ignore
    """
    It's pretty trivial for the moment - just generates an input event.
    """

    queue: Optional[InputQueue]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.logger = logging.getLogger(__name__ + "DiscordInputEventClient")

    async def on_ready(self) -> None:
        """
        Called once at the start, after the bot has connected to discord.
        :return:
        """
        self.logger.info("%s has connected to Discord!", self.user)

    async def on_message(self, message: discord.Message) -> None:
        """
        Check for acceptance on all commands - execute the first one that matches.
        :param message:
        :return:
        """
        self.logger.info(message.content)

        if not self.queue:
            return

        await self.queue.put(DiscordInputEvent(text=message.content, message=message))


@dataclasses.dataclass
class DiscordOutputEvent(OutputEvent):
    text: str
    message: discord.message
    use_message_channel: bool


class DiscordOutput(Output):
    @staticmethod
    def consumes_outputs() -> Set[Type[OutputEvent]]:
        """
        Defines the set of output events that this Output class can consume
        :return:
        """
        return {
            DiscordOutputEvent,
        }

    async def output(self, event: OutputEvent) -> bool:
        """
        Does the work of transmitting the event to the world.
        :param event:
        :return:
        """

        if not isinstance(event, DiscordOutputEvent):
            return False

        if event.use_message_channel:
            await event.message.channel.send(event.text)
            return True

        raise NotImplementedError("Currently can only respond to a message")
