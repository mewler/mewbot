# Aim is to run, in sections, as many of the input methods as possible
# Including running a full bot with logging triggers and actions.
# However, individual components also have to be isolated for testing purposes.

import asyncio
import tempfile

# import os

import pytest

# from mewbot.api.v1 import InputEvent
from mewbot.io.file_system import (
    FileTypeFSInput,
    # CreatedFileFSInputEvent,
    # DeletedFileFSInputEvent,
)


# pylint: disable=invalid-name
# test functions should be named after the things they test


class TestFileTypeFSInput:
    @pytest.mark.asyncio
    async def test_hello_world(self) -> None:
        """
        Basic test that the pytest-asyncio framework is working.
        """
        await asyncio.sleep(0.2)

    @pytest.mark.asyncio
    async def test_FileTypeFSInput__init__input_path_None(self) -> None:
        """
        Tests that we can start an isolated copy of FileTypeFSInput - for testing purposes.
        input_path is set to None
        """
        test_fs_input = FileTypeFSInput(input_path=None)
        assert isinstance(test_fs_input, FileTypeFSInput)

    @pytest.mark.asyncio
    async def test_FileTypeFSInput__init__input_path_nonsense(self) -> None:
        """
        Tests that we can start an isolated copy of FileTypeFSInput - for testing purposes.

        """
        test_fs_input = FileTypeFSInput(input_path="\\///blargleblarge_not_a_path")
        assert isinstance(test_fs_input, FileTypeFSInput)

    @pytest.mark.asyncio
    async def test_FileTypeFSInput__init__input_path_existing_dir(self) -> None:
        """
        Tests that we can start an isolated copy of FileTypeFSInput - for testing purposes.

        """
        with tempfile.TemporaryDirectory() as tmp_dir_path:
            test_fs_input = FileTypeFSInput(input_path=tmp_dir_path)
            assert isinstance(test_fs_input, FileTypeFSInput)
            del test_fs_input
