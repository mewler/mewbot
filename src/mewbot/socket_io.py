import asyncio
import dataclasses
import logging
import socket

from typing import Optional, Set, Type

from mewbot.core import InputEvent, InputQueue
from mewbot.api.v1 import Input


@dataclasses.dataclass  # Needed for pycharm linting
class SocketInputEvent(InputEvent):
    data: bytes


class SocketInput(Input):
    """
    Not complete, but it took an annoyingly long time to get working
    so I'm leaving it in for future use.
    """

    logger: logging.Logger

    host: str
    port: int

    queue: Optional[InputQueue] = None

    def __init__(self) -> None:
        super().__init__()

        self.host = "localhost"
        self.port = 15559

        self.logger = logging.getLogger(__name__ + "SocketInput")

    @staticmethod
    def produces_inputs() -> Set[Type[InputEvent]]:
        """
        Defines the set of input events this Input class can produce.
        :return:
        """
        return {
            SocketInputEvent,
        }

    async def run(self) -> None:
        self.logger.info("Binding get server to %s:%d", self.host, self.port)

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen(8)
        # Needed so asyncio can release this resource
        server_socket.setblocking(False)

        loop = asyncio.get_event_loop()

        # Setup done - now actually run
        while True:
            client, _ = await loop.sock_accept(server_socket)

            # Read and echo
            chunks = []
            while True:
                data = client.recv(2048)
                if not data:
                    break
                chunks.append(data)
            client.sendall(b"".join(chunks))
            client.close()

            if not self.queue:
                self.logger.warning("Received event with no attached queue")
                continue

            await self.queue.put(SocketInputEvent(data=data))
