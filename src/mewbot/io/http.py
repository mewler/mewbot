#!/usr/bin/env python3

"""
When defining a new IOConfig, you need to define the components for it

 - The Input Class - here PostInput - which, here, does all the work of actually
                     running the server to support post
 - The Input Event - here PostInputEvent - which is produced when an event the
                     input cares about occurs - here posting to the url
"""

from __future__ import annotations

from typing import Set, Type

import dataclasses
import logging
import time

from aiohttp import web  # type: ignore

from mewbot.core import InputEvent
from mewbot.io.socket import SocketIO, SocketInput


@dataclasses.dataclass  # Needed for pycharm linting
class IncomingWebhookEvent(InputEvent):
    text: str


class HTTPServlet(SocketIO):
    """
    Very basic IOConfig with a PostInput input - which you have
    to add yourself - and that's about it.
    """

    def _create_socket(self) -> HTTPInputListener:
        return HTTPInputListener(self._host, self._port, self._logger)


class HTTPInputListener(SocketInput):
    """
    Runs an aiohttp microservice to allow post requests
    """

    _runner: web.AppRunner

    def __init__(self, host: str, port: int, logger: logging.Logger) -> None:
        super().__init__(host, port, logger)

        servlet = web.Application()
        servlet.add_routes([web.post("/", self.post_response)])

        # Create the website container
        self._runner = web.AppRunner(
            servlet, handle_signals=False, access_log=logger, logger=logger
        )

    @staticmethod
    def produces_inputs() -> Set[Type[InputEvent]]:
        """
        Defines the set of input events this Input class can produce.
        :return:
        """
        return {IncomingWebhookEvent}

    async def post_response(self, request: web.Request) -> web.Response:
        """
        Process a post requests to address/post
        """

        if not self.queue:
            return web.Response(text=f"Received (no queue) - {time.time()}")

        # Get the message on the wire
        r_text = await request.text()
        await self.queue.put(IncomingWebhookEvent(text=r_text))

        self._logger.info(r_text)
        return web.Response(text=f"Received - {time.time()}")

    async def run(self) -> None:
        """
        Fires up an aiohttp app to run the service
        """
        await self._runner.setup()

        site = web.TCPSite(self._runner, self._host, self._port)

        # Run the bot
        await site.start()
