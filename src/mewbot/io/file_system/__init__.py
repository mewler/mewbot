#!/usr/bin/env python3

from __future__ import annotations

from typing import Optional, Sequence, Union

from mewbot.api.v1 import IOConfig, Input, Output
from mewbot.io.file_system.events import (
    FSInputEvent,
    FSOutputEvent,
    FileFSInputEvent,
    FileFSOutputEvent,
    CreatedFileFSInputEvent,
    UpdatedFileFSInputEvent,
    MovedFileFSInputEvent,
    DeletedFileFSInputEvent,
    InputFileFileCreationInputEvent,
    InputFileFileDeletionInputEvent,
    CreatedDirFSInputEvent,
    UpdatedDirFSInputEvent,
    MovedDirFSInputEvent,
    DeletedDirFSInputEvent,
    InputFileDirCreationInputEvent,
    InputFileDirDeletionInputEvent,
    CreateFileFSOutputEvent,
    AppendFileFSOutputEvent,
    DeleteFileFSOutputEvent,
    OverwriteFileFSOutputEvent,
)
from mewbot.io.file_system.input import FileTypeFSInput, DirTypeFSInput
from mewbot.io.file_system.output import FileSystemOutput

__all__ = (
    "FSInputEvent",
    "FSOutputEvent",
    "FileFSInputEvent",
    "FileFSOutputEvent",
    "CreatedFileFSInputEvent",
    "UpdatedFileFSInputEvent",
    "MovedFileFSInputEvent",
    "DeletedFileFSInputEvent",
    "InputFileFileCreationInputEvent",
    "InputFileFileDeletionInputEvent",
    "CreatedDirFSInputEvent",
    "UpdatedDirFSInputEvent",
    "MovedDirFSInputEvent",
    "DeletedDirFSInputEvent",
    "InputFileDirCreationInputEvent",
    "InputFileDirDeletionInputEvent",
    "CreateFileFSOutputEvent",
    "AppendFileFSOutputEvent",
    "DeleteFileFSOutputEvent",
    "OverwriteFileFSOutputEvent",
    "FileTypeFSInput",
    "DirTypeFSInput",
    "FileSystemOutput",
)


class FileSystemIO(IOConfig):

    _input: Optional[Union[FileTypeFSInput, DirTypeFSInput]] = None
    _output: Optional[FileSystemOutput] = None

    _input_path: Optional[str] = None
    _input_path_type: str = "not_set"
    _output_path: Optional[str] = None

    @property
    def input_path(self) -> Optional[str]:
        return self._input_path

    @input_path.setter
    def input_path(self, input_path: str) -> None:
        self._input_path = input_path

    @property
    def input_path_type(self) -> str:
        """
        When starting this class you need to set the type of resource you are monitoring.
        This is due to limitations of the underlying libraries used to do the actual monitoring.
        """
        return self._input_path_type

    @input_path_type.setter
    def input_path_type(self, input_path_type: str) -> None:
        assert input_path_type in (
            "dir",
            "file",
        ), f"input_path_type couldn't be set as {input_path_type}"
        self._input_path_type = input_path_type

    @property
    def output_path(self) -> Optional[str]:
        return self._output_path

    @output_path.setter
    def output_path(self, output_path: str) -> None:
        self._output_path = output_path

    def get_inputs(self) -> Sequence[Input]:

        assert self._input_path_type in ("dir", "file",), (
            f"input_path_type must be properly set before startup - "
            f"{self._input_path_type} is not proper"
        )

        if not self._input:

            if self._input_path_type == "file":
                self._input = FileTypeFSInput(self._input_path)
            elif self._input_path_type == "dir":
                self._input = DirTypeFSInput(self._input_path)
            else:
                raise NotImplementedError(
                    f"{self._input_path_type} not good. Options are 'dir' and 'file'"
                )

        return [self._input]

    def get_outputs(self) -> Sequence[Output]:
        if not self._output:
            self._output = FileSystemOutput(self._output_path)

        return [self._output]
