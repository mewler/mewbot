#!/usr/bin/env python3

from __future__ import annotations

from typing import Optional, Set, Type

import logging

from mewbot.api.v1 import Output, OutputEvent
from mewbot.io.file_system.events import (
    CreateFileFSOutputEvent,
    AppendFileFSOutputEvent,
    DeleteFileFSOutputEvent,
    OverwriteFileFSOutputEvent,
)


class FileSystemOutput(Output):

    _logger: logging.Logger
    _output_path: Optional[str]  # A location on the file system to monitor

    def __init__(self, output_path: Optional[str] = None) -> None:
        super(Output, self).__init__()  # pylint: disable=bad-super-call

        self._output_path = output_path
        self._logger = logging.getLogger(__name__ + "FileSystemOutput")

    @staticmethod
    def consumes_outputs() -> Set[Type[OutputEvent]]:
        """
        Defines the set of output events that this Output class can consume
        :return:
        """
        return {
            CreateFileFSOutputEvent,
            AppendFileFSOutputEvent,
            OverwriteFileFSOutputEvent,
            DeleteFileFSOutputEvent,
        }

    async def output(self, event: OutputEvent) -> bool:
        """
        Does the work of transmitting the event to the world.
        :param event:
        :return:
        """
        raise NotImplementedError("Not yet ready for prime time")
