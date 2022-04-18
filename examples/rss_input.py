#!/usr/bin/env python3
# pylint: disable=duplicate-code
# this is an example - duplication for emphasis is desirable

# https://www.theguardian.com/world/rss

import logging

from typing import Any, Dict, Set, Type

from mewbot.io.rss import RSSInputEvent

from mewbot.api.v1 import Trigger, Action
from mewbot.core import InputEvent, OutputEvent, OutputQueue


class RSSPrintAction(Action):
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

        rss_output_str = []
        rss_output_str.append(f"New event title - {event.title}")
        rss_output_str.append(f"New event author - {event.author}")
        rss_output_str.append(f"New event ... event - \n{event}")

        print("\n".join(rss_output_str))
