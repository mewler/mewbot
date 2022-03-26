# Remember when wiring random services together to see what you could make happen?
# I miss those days

# trivial discord bot implemented in mewbot - will respond to the message "!hello" with "World"

from __future__ import annotations

import json
import logging
import os

from typing import Any, Dict, Set, Type

from mewbot.bot import Bot

from mewbot.behaviour import Behaviour
from mewbot.api.v1 import Trigger, Condition, Action
from mewbot.core import InputEvent, OutputEvent, OutputQueue

from mewbot.http_post import PostIOConfig
from mewbot.discord import DiscordInput, DiscordInputEvent, DiscordOutputEvent, DiscordOutput

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


class DiscordTrivialTrigger(Trigger):
    """
    Nothing fancy - just fires whenever there is a DiscordInputEvent
    """

    @staticmethod
    def consumes_inputs() -> Set[Type[InputEvent]]:
        return {
            DiscordInputEvent,
        }

    def matches(self, event: InputEvent) -> bool:
        if not isinstance(event, DiscordInputEvent):
            return False

        return event.text == "!hello"


class DiscordTrivialCondition(Condition):
    """
    Allows every input.
    """

    @staticmethod
    def consumes_inputs() -> Set[Type[InputEvent]]:
        return {
            DiscordInputEvent,
        }

    def allows(self, event: InputEvent) -> bool:
        return True


class DiscordPrintAndReplyAction(Action):
    """
    Print every InputEvent.
    """

    _queue: OutputQueue

    def __init__(self) -> None:
        super().__init__()
        self.logger = logging.getLogger(__name__ + type(self).__name__)

    @staticmethod
    def consumes_inputs() -> Set[Type[InputEvent]]:
        return {
            DiscordInputEvent,
        }

    @staticmethod
    def produces_outputs() -> Set[Type[OutputEvent]]:
        return {
            DiscordOutputEvent,
        }

    async def act(self, event: InputEvent, state: Dict[str, Any]) -> None:
        """
        Construct a DiscordOutputEvent with the result of performing the calculation.
        """
        if not isinstance(event, DiscordInputEvent):
            self.logger.warning("Received wrong event type %s", type(event))
            return

        self.logger.info("event.txt = %s", event.text)
        test_event = DiscordOutputEvent(
            text="world", message=event.message, use_message_channel=True
        )

        self.logger.info(test_event)
        await self.send(test_event)

    async def send(self, event: OutputEvent) -> None:
        await self._queue.put(event)


def load_secrets() -> Any:
    secrets_file = os.path.join(__location__, "TrivialDiscordBot", "secrets.json")

    # Check to see if the file exists and complain if it does not
    if not os.path.isfile(secrets_file):
        raise RuntimeError(
            f"{secrets_file} did not exist - and we need secrets! (In particular, a token)"
        )

    with open(secrets_file, "rb") as json_file:
        return json.load(json_file)


if __name__ == "__main__":

    # Acquire token from json file in the root of this dir
    secrets = load_secrets()
    token = secrets["token"]

    # For the moment just printing all discord input events

    # - Behavior
    # Construct the print_behavior - which just prints every input event
    print_behavior = Behaviour()
    # Triggers on all PostInput events
    print_behavior.add(DiscordTrivialTrigger())
    # Passes all incoming events
    print_behavior.add(DiscordTrivialCondition())
    # Prints all the events which make their way into the bot
    print_behavior.add(DiscordPrintAndReplyAction())

    # - IOConfig
    post_ioconfig = PostIOConfig()

    discord_input = DiscordInput()
    discord_input.set_token(token)

    discord_output = DiscordOutput()

    post_ioconfig.inputs.append(discord_input)
    post_ioconfig.outputs.append(discord_output)

    test_bot = Bot()
    test_bot.name = "TrivialDiscordExample"
    test_bot.add_io_config(post_ioconfig)
    test_bot.add_behaviour(print_behavior)
    test_bot.run()
