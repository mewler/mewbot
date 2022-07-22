#!/usr/bin/env python3

from __future__ import annotations

from typing import Optional, Set, Type

import logging
import os
import sys

import aiopath  # type: ignore

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
    _output_encoding: str

    def __init__(self, output_path: Optional[str] = None) -> None:
        super(Output, self).__init__()  # pylint: disable=bad-super-call

        self._output_path = output_path
        self._logger = logging.getLogger(__name__ + "FileSystemOutput")
        if isinstance(output_path, str):
            self._output_path_exists = os.path.isdir(output_path)
        else:
            self._output_path_exists = False

        self._output_encoding = sys.getdefaultencoding()

        self._logger.info(
            "Started - target path '%s' - exists %s",
            self._output_path,
            self._output_path_exists,
        )

    @property
    def output_path(self) -> Optional[str]:
        return self._output_path

    @output_path.setter
    def output_path(self, value: Optional[str]) -> None:
        self._output_path = value
        if value is not None:
            self._output_path_exists = os.path.isdir(value)
        else:
            self._output_path_exists = False

    @property
    def output_path_exists(self) -> bool:
        return self._output_path_exists

    @output_path_exists.setter
    def output_path_exists(self, value: Optional[str]) -> None:
        raise AttributeError("Cannot set output_path_exists externally")

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
        if self._output_path is not None:
            output_path = self._output_path
        else:
            return False

        if not self._output_path_exists:
            self._logger.warning(
                "Cannot output - output_path '%s' does not exist", output_path
            )
            return False

        if isinstance(event, CreateFileFSOutputEvent):

            return await self._process_create_file_event(output_path, event)

        if isinstance(event, AppendFileFSOutputEvent):

            return await self._process_addition_file_event(output_path, event)

        if isinstance(event, OverwriteFileFSOutputEvent):

            return await self._process_overwrite_file_event(output_path, event)

        if isinstance(event, DeleteFileFSOutputEvent):

            return await self._process_delete_file_event(output_path, event)

        raise NotImplementedError(f"Unexpected event type {event}")

    @staticmethod
    async def _process_create_file_event(
        output_path: str, event: CreateFileFSOutputEvent
    ) -> bool:

        file_output_path = aiopath.AsyncPath(os.path.join(output_path, event.file_name))

        # Will not write over the top of an existing file - overwrite exists for that
        if await file_output_path.exists():
            return False

        mode = "w" if not event.is_binary else "wb"
        async with file_output_path.open(mode=mode) as outfile:
            await outfile.write(event.file_contents)
        return True

    @staticmethod
    async def _process_addition_file_event(
        output_path: str, event: AppendFileFSOutputEvent
    ) -> bool:

        file_output_path = aiopath.AsyncPath(os.path.join(output_path, event.file_name))

        # Cannot append to a file which does not exist - create exists for that
        if not await file_output_path.exists():
            return False

        mode = "a" if not event.is_binary else "ab"
        async with file_output_path.open(mode=mode) as outfile:
            await outfile.write(event.file_contents)
        return True

    @staticmethod
    async def _process_overwrite_file_event(
        output_path: str, event: OverwriteFileFSOutputEvent
    ) -> bool:

        file_output_path = aiopath.AsyncPath(os.path.join(output_path, event.file_name))

        mode = "w" if not event.is_binary else "wb"
        async with file_output_path.open(mode=mode) as outfile:
            await outfile.write(event.file_contents)
        return True

    @staticmethod
    async def _process_delete_file_event(
        output_path: str, event: DeleteFileFSOutputEvent
    ) -> bool:

        file_output_path = aiopath.AsyncPath(os.path.join(output_path, event.file_name))

        await file_output_path.unlink()
        return True
