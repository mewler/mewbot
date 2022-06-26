#!/usr/bin/env python3

from __future__ import annotations

from typing import Optional, Set, Sequence, Type

import dataclasses
import logging

import discord  # type: ignore

from mewbot.api.v1 import IOConfig, Input, Output, InputEvent, OutputEvent


@dataclasses.dataclass
class DiscordInputEvent(InputEvent):
    """
    Class which represents a new message being detected on any of the channels that the bot is
    connected to.
    Ideally should contain enough messages/objects to actually respond to a message.
    """

    text: str
    message: discord.Message


@dataclasses.dataclass
class DiscordUserJoinInputEvent(InputEvent):
    """
    Class which represents a user joining one of the discord channels which the bot has access to.
    """

    member: discord.member.Member


@dataclasses.dataclass
class DiscordOutputEvent(OutputEvent):
    """
    Currently just used to reply to an input event.
    """

    text: str
    message: discord.message
    use_message_channel: bool


class DiscordIO(IOConfig):
    _input: Optional[DiscordInput] = None
    _output: Optional[DiscordOutput] = None
    _token: str = ""

    @property
    def token(self) -> str:
        return self._token

    @token.setter
    def token(self, token: str) -> None:
        self._token = token

    def get_inputs(self) -> Sequence[Input]:
        if not self._input:
            self._input = DiscordInput(self._token)

        return [self._input]

    def get_outputs(self) -> Sequence[Output]:
        if not self._output:
            self._output = DiscordOutput()

        return [self._output]


class DiscordInput(Input, discord.Client):  # type: ignore
    """
    Uses py-cord as a backend to connect, receive and send messages to discord.
    """

    _logger: logging.Logger
    _token: str

    def __init__(self, token: str) -> None:
        super(Input, self).__init__()  # pylint: disable=bad-super-call
        super(discord.Client, self).__init__()  # pylint: disable=bad-super-call

        self._token = token
        self._logger = logging.getLogger(__name__ + "DiscordInput")

    @staticmethod
    def produces_inputs() -> Set[Type[InputEvent]]:
        """Defines the set of input events this Input class can produce."""
        return {DiscordInputEvent, DiscordUserJoinInputEvent}

    async def run(self) -> None:
        """
        Fires up an aiohttp app to run the service.
        Token needs to be set by this point.
        """
        self._logger.info("About to connect to Discord")

        await super().start(self._token)

    async def on_ready(self) -> None:
        """
        Called once at the start, after the bot has connected to discord.
        :return:
        """
        self._logger.info("%s has connected to Discord!", self.user)

    async def on_message(self, message: discord.Message) -> None:
        """
        Check for acceptance on all commands - execute the first one that matches.
        :param message:
        :return:
        """
        self._logger.info(message.content)

        if not self.queue:
            return

        await self.queue.put(DiscordInputEvent(text=message.content, message=message))

    async def on_member_join(self, member: discord.Member) -> None:
        """
        Triggered when a member joins one of the guilds that the bot is monitoring.
        """
        self._logger.info(
            'New member "%s" has been detected joining"%s"',
            str(member.mention),
            str(member.guild.name),
        )

        if not self.queue:
            return

        await self.queue.put(DiscordUserJoinInputEvent(member=member))


class DiscordOutput(Output):
    @staticmethod
    def consumes_outputs() -> Set[Type[OutputEvent]]:
        """
        Defines the set of output events that this Output class can consume
        :return:
        """
        return {DiscordOutputEvent}

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
