#!/usr/bin/env python3
# pylint: disable=duplicate-code
# this is an example - duplication for emphasis is desirable

from __future__ import annotations

from typing import Any, Dict, Set, Type

import logging

from mewbot.api.v1 import Trigger, Action
from mewbot.core import InputEvent, OutputEvent, OutputQueue
from mewbot.io.file_system import (
    CreatedDirFSInputEvent,
    UpdatedDirFSInputEvent,
    MovedDirFSInputEvent,
    DeletedDirFSInputEvent,
    CreatedFileFSInputEvent,
    UpdatedFileFSInputEvent,
    MovedFileFSInputEvent,
    DeletedFileFSInputEvent,
    InputFileDirCreationInputEvent,
    InputFileDirDeletionInputEvent,
)


class DirSystemAllCommandTrigger(Trigger):
    """
    Nothing fancy - just fires whenever there is a dir related FSInputEvent
    """

    @staticmethod
    def consumes_inputs() -> Set[Type[InputEvent]]:
        return {
            CreatedDirFSInputEvent,
            UpdatedDirFSInputEvent,
            MovedDirFSInputEvent,
            DeletedDirFSInputEvent,
            CreatedFileFSInputEvent,
            UpdatedFileFSInputEvent,
            MovedFileFSInputEvent,
            DeletedFileFSInputEvent,
            InputFileDirCreationInputEvent,
            InputFileDirDeletionInputEvent,
        }

    def matches(self, event: InputEvent) -> bool:

        print("-------\n", "event seen by matches - ", event, "\n-------")

        if not isinstance(
            event,
            (
                CreatedDirFSInputEvent,
                UpdatedDirFSInputEvent,
                MovedDirFSInputEvent,
                DeletedDirFSInputEvent,
                CreatedFileFSInputEvent,
                MovedFileFSInputEvent,
                UpdatedFileFSInputEvent,
                DeletedFileFSInputEvent,
                InputFileDirCreationInputEvent,
                InputFileDirDeletionInputEvent,
            ),
        ):
            return False

        return True


class DirSystemInputPrintResponse(Action):
    """
    Print every DirSystem Dir related InputEvent.
    """

    _logger: logging.Logger
    _queue: OutputQueue

    def __init__(self) -> None:
        super().__init__()
        self._logger = logging.getLogger(__name__ + type(self).__name__)

    @staticmethod
    def consumes_inputs() -> Set[Type[InputEvent]]:
        return {
            CreatedDirFSInputEvent,
            UpdatedDirFSInputEvent,
            MovedDirFSInputEvent,
            DeletedDirFSInputEvent,
            CreatedFileFSInputEvent,
            UpdatedFileFSInputEvent,
            MovedFileFSInputEvent,
            DeletedFileFSInputEvent,
            InputFileDirCreationInputEvent,
            InputFileDirDeletionInputEvent,
        }

    @staticmethod
    def produces_outputs() -> Set[Type[OutputEvent]]:
        return set()

    async def act(self, event: InputEvent, state: Dict[str, Any]) -> None:
        """
        Construct a DiscordOutputEvent with the result of performing the calculation.
        """
        if not isinstance(event, InputEvent):
            self._logger.warning("Received wrong event type %s", type(event))
            return

        print("-------\n", "event seen by action - ", event, "\n-------")
