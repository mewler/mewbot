#!/usr/bin/env python3

from __future__ import annotations

from typing import Optional, Set, Type

import logging
import os

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
    _output_path_exists: bool = False

    def __init__(self, output_path: Optional[str] = None) -> None:
        super(Output, self).__init__()  # pylint: disable=bad-super-call

        self._output_path = output_path
        self._logger = logging.getLogger(__name__ + "FileSystemOutput")
        self._output_path_exists = os.path.isdir(self._output_path)

    @property
    def output_path(self) -> Optional[str]:
        return self._output_path

    @output_path.setter
    def output_path(self, value: Optional[str]) -> None:
        self._output_path = value
        self._output_path_exists = os.path.isdir(self._output_path)

    @property
    def output_path_exists(self) -> bool:
        return self._output_path_exists

    @output_path_exists.setter
    def output_path_exists(self, value: Optional[str]) -> None:
        raise NotImplementedError("Cannot set output_path_exists externally")

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
        if not self._output_path_exists:
            self._logger.warning("Cannot output - output_path '%s' does not exist", self._output_path)
            return False


