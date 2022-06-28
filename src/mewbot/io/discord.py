#!/usr/bin/env python3

from __future__ import annotations

from typing import Optional, Set, Sequence, Type, List

import dataclasses
import logging

import discord  # type: ignore

from mewbot.api.v1 import IOConfig, Input, Output, InputEvent, OutputEvent


@dataclasses.dataclass
class DiscordInputEvent(InputEvent):
    pass


@dataclasses.dataclass
class DiscordTextInputEvent(DiscordInputEvent):
    """
    Class which represents a new message being detected on any of the channels that the bot is
    connected to.
    Ideally should contain enough messages/objects to actually respond to a message.
    """

    text: str
    message: discord.Message


@dataclasses.dataclass
class DiscordUserJoinInputEvent(DiscordInputEvent):
    """
    Class which represents a user joining one of the discord channels which the bot has access to.
    """

    member: discord.member.Member


@dataclasses.dataclass
class DiscordMessageEditInputEvent(DiscordInputEvent):
    """
    Class which represents an edit to an existing message being detected on any of the channels
    that the bot is connected to.
    """

    text_before: str
    message_before: discord.Message

    text_after: str
    message_after: discord.Message


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
    _startup_queue_depth: int = 0

    @property
    def token(self) -> str:
        return self._token

    @token.setter
    def token(self, token: str) -> None:
        self._token = token

    @property
    def startup_queue_depth(self) -> int:
        return self._startup_queue_depth

    @startup_queue_depth.setter
    def startup_queue_depth(self, startup_queue_depth: int) -> None:
        assert (
            startup_queue_depth >= 0
        ), "Please provide a positive (or 0) startup_queue_depth"
        self._startup_queue_depth = startup_queue_depth

    def get_inputs(self) -> Sequence[Input]:
        if not self._input:
            self._input = DiscordInput(self._token, self._startup_queue_depth)

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
    _startup_queue_depth: int

    def __init__(self, token: str, startup_queue_depth: int = 0) -> None:
        """
        :param token: The token need to authenticate this bot to the discord server
        :param startup_queue_depth:
            During startup, the number of DiscordTextInputEvents to put on the wire
            (Other forms of event are not always possible).
        """
        assert startup_queue_depth >= 0, "Does not support a negative startup_queue_depth"

        super(Input, self).__init__()  # pylint: disable=bad-super-call
        super(discord.Client, self).__init__()  # pylint: disable=bad-super-call

        self._token = token
        self._logger = logging.getLogger(__name__ + "DiscordInput")

        self._startup_queue_depth = startup_queue_depth

    @staticmethod
    def produces_inputs() -> Set[Type[InputEvent]]:
        """Defines the set of input events this Input class can produce."""
        return {
            DiscordTextInputEvent,
            DiscordUserJoinInputEvent,
            DiscordMessageEditInputEvent,
        }

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

        await self.retrieve_old_message()

    async def retrieve_old_message(self) -> None:
        """
        If a startup_queue_depth is set, then
        """
        if not self._startup_queue_depth:
            return

        # Might want to, instead, wait for a queue
        if not self.queue:
            return

        self._logger.info("Retrieving %s old messages", self._startup_queue_depth)

        # The aim is to build a list of the last five messages the bot would have seen if it was up
        # - iterate over all the guilds the bot can see
        # - then iterate over all the text channels in that guild
        # - grab a number of messages equal to the queue depth
        # - append them to a master list
        # - sort on time in the master list
        # - return the queue depth number of items from the sorted list
        past_messages: List[discord.Message] = []

        # Short cut for itterating over all guilds, then all channels
        for channel in self.get_all_channels():
            # Ignoring everything which is not a text channel - nothing to do with past voice
            if not isinstance(channel, discord.channel.TextChannel):
                continue

            messages = await channel.history(limit=5).flatten()
            past_messages.extend(messages)

        # Sort the messages and put the last five on the wire
        past_messages = sorted(
            past_messages, key=lambda x: float(x.created_at.timestamp()), reverse=True
        )

        for _ in range(self._startup_queue_depth):
            message = past_messages[_]

            if not isinstance(message, discord.Message):
                self._logger.info("Expected a message and got a %s", type(message))

            await self.queue.put(DiscordTextInputEvent(text=message.content, message=message))

    async def on_message(self, message: discord.Message) -> None:
        """
        Check for acceptance on all commands - execute the first one that matches.
        :param message:
        :return:
        """
        self._logger.info(message.content)

        if not self.queue:
            return

        await self.queue.put(DiscordTextInputEvent(text=message.content, message=message))

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

    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        """
        Triggered when a message is edited on any of the channels which the bot is monitoring.
        """
        self._logger.info("Message edit - %s changed to %s", before.content, after.content)

        if not self.queue:
            return

        await self.queue.put(
            DiscordMessageEditInputEvent(
                text_before=before.content,
                message_before=before,
                text_after=after.content,
                message_after=after,
            )
        )


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
