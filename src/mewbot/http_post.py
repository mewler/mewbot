#!/usr/bin/env python3

"""
When defining a new IOConfig, you need to define the components for it

 - The Input Class - here PostInput - which, here, does all the work of actually
                     running the server to support post
 - The Input Event - here PostInputEvent - which is produced when an event the
                     input cares about occurs - here posting to the url
"""

from __future__ import annotations

from typing import Optional, Set, Type, Sequence, List

import dataclasses
import logging
import time

from aiohttp import web

from mewbot.core import InputEvent, InputQueue
from mewbot.api.v1 import IOConfig, Input, Output


@dataclasses.dataclass  # Needed for pycharm linting
class PostInputEvent(InputEvent):
    text: str


class PostInput(Input):
    """
    Runs an aiohttp microservice to allow post requests
    """

    queue: Optional[InputQueue]

    def __init__(self) -> None:
        super().__init__()

        self.host = "localhost"
        self.port = 15520

        self.logger = logging.getLogger(__name__ + "PostInput")

    @staticmethod
    def produces_inputs() -> Set[Type[InputEvent]]:
        """
        Defines the set of input events this Input class can produce.
        :return:
        """
        return {
            PostInputEvent,
        }

    async def post_response(self, request: web.Request) -> web.Response:
        """
        Process a post requests to address/post
        """

        if not self.queue:
            return web.Response(text=f"Received (no queue) - {time.time()}")

        # Get the message on the wire
        r_text = await request.text()
        await self.queue.put(PostInputEvent(text=r_text))

        self.logger.info(r_text)
        return web.Response(text=f"Received - {time.time()}")

    async def run(self) -> None:
        """
        Fires up an aiohttp app to run the service
        """

        servlet = web.Application()
        servlet.add_routes(
            [
                web.post("/", self.post_response),
            ]
        )

        # Create the website container
        runner = web.AppRunner(
            servlet,
            handle_signals=False,
            access_log=logging.getLogger("post_input_server"),
            logger=logging.getLogger("post_input_server"),
        )
        await runner.setup()

        site = web.TCPSite(runner, self.host, self.port)

        # Run the bot
        await site.start()


class PostIOConfig(IOConfig):
    """
    Very basic IOConfig with a PostInput input - which you have
    to add yourself - and that's about it.
    """

    inputs: List[Input]
    outputs: List[Output]

    def __init__(self) -> None:
        super().__init__()

        self.inputs = []
        self.outputs = []

    def get_inputs(self) -> Sequence[Input]:
        return self.inputs

    def get_outputs(self) -> Sequence[Output]:
        return self.outputs
