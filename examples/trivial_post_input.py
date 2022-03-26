#!/usr/bin/env python3

"""
Implementing a new Input - as it happens to be the first input,
a few other things are going to have to go on

- like defining some behaviors
- and actually building a bot
- and fixing any weird type errors
"""

from __future__ import annotations

from typing import Set, Type, Dict, Any

from mewbot.bot import Bot
from mewbot.behaviour import Behaviour
from mewbot.core import InputEvent, OutputEvent
from mewbot.api.v1 import Trigger, Condition, Action

from mewbot.http_post import PostInput, PostIOConfig, PostInputEvent


class TrivialTrigger(Trigger):
    """
    Nothing fancy - just fires whenever there is an PostInputEvent.
    Will be used in the PrintBehavior.
    """

    @staticmethod
    def consumes_inputs() -> Set[Type[InputEvent]]:
        return {
            PostInputEvent,
        }

    def matches(self, event: InputEvent) -> bool:
        return True


class TrivialCondition(Condition):
    """
    Allows every input
    """

    @staticmethod
    def consumes_inputs() -> Set[Type[InputEvent]]:
        return {
            PostInputEvent,
        }

    def allows(self, event: InputEvent) -> bool:
        return True


class PrintAction(Action):
    """
    Print every InputEvent.
    """

    @staticmethod
    def consumes_inputs() -> Set[Type[InputEvent]]:
        return {
            PostInputEvent,
        }

    @staticmethod
    def produces_outputs() -> Set[Type[OutputEvent]]:
        return set()

    async def act(self, event: InputEvent, state: Dict[str, Any]) -> None:
        print(event)


if __name__ == "__main__":

    # - Behavior
    # Construct the print_behavior - which just prints every input event
    print_behavior = Behaviour()
    # Triggers on all PostInput events
    print_behavior.add(TrivialTrigger())
    # Passes all incoming events
    print_behavior.add(TrivialCondition())
    # Prints all the events which make their way into the bot
    print_behavior.add(PrintAction())

    # - IOConfig
    post_ioconfig = PostIOConfig()
    post_ioconfig.inputs.append(PostInput())

    test_bot = Bot()
    test_bot.name = "TrivialWebhookExample"
    test_bot.add_io_config(post_ioconfig)
    test_bot.add_behaviour(print_behavior)
    test_bot.run()
