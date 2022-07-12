# Aim is to run, in sections, as many of the input methods as possible
# Including running a full bot with logging triggers and actions.
# However, individual components also have to be isolated for testing purposes.

import asyncio
import tempfile

import os

import pytest

from mewbot.api.v1 import InputEvent
from mewbot.io.file_system import (
    FileTypeFSInput,
    UpdatedFileFSInputEvent
    # DeletedFileFSInputEvent,
)


# pylint: disable=invalid-name
# for clarity, test functions should be named after the things they test
# which means CamelCase in function names


class TestFileTypeFSInput:

    # - INIT AND ATTRIBUTE

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
        input_path_str = "\\///blargleblarge_not_a_path"
        test_fs_input = FileTypeFSInput(input_path=input_path_str)
        assert isinstance(test_fs_input, FileTypeFSInput)

        # Test attributes which should have been set
        assert test_fs_input.input_path == input_path_str
        test_fs_input.input_path = "//\\another thing which does not exist"

        assert test_fs_input.input_path_exists is False

        try:
            test_fs_input.input_path_exists = True
        except AttributeError:
            pass

    @pytest.mark.asyncio
    async def test_FileTypeFSInput__init__input_path_existing_dir(self) -> None:
        """
        Tests that we can start an isolated copy of FileTypeFSInput - for testing purposes.

        """
        with tempfile.TemporaryDirectory() as tmp_dir_path:
            test_fs_input = FileTypeFSInput(input_path=tmp_dir_path)
            assert isinstance(test_fs_input, FileTypeFSInput)

            assert test_fs_input.input_path == tmp_dir_path
            assert test_fs_input.input_path_exists is True

    # - RUN

    @pytest.mark.asyncio
    async def test_FileTypeFSInput_run_without_error_existing_dir(self) -> None:
        """
        Tests that the run method of the input class does not throw an error.
        Testing on a dir which actually exists.
        This will not produce actual events, because it's a FileTypeFSInput
        The object it's pointed at is a dir.
        """
        with tempfile.TemporaryDirectory() as tmp_dir_path:
            test_fs_input = FileTypeFSInput(input_path=tmp_dir_path)
            assert isinstance(test_fs_input, FileTypeFSInput)

            # We need to retain control of the thread to preform shutdown
            asyncio.get_running_loop().create_task(test_fs_input.run())

            await asyncio.sleep(0.5)
            # Note - manually stopping the loop seems to lead to a rather nasty cash

            # Tests are making a clean exist after this test

    @pytest.mark.asyncio
    async def test_FileTypeFSInput_run_without_error_existing_file(self) -> None:
        """
        Tests that the run method of the input class does not throw an error.
        Testing on a dir which actually exists.
        This will not produce actual events, because it's a FileTypeFSInput
        The object it's pointed at is a dir.
        """
        with tempfile.TemporaryDirectory() as tmp_dir_path:

            tmp_file_path = os.path.join(tmp_dir_path, "mewbot_test_file.test")
            with open(tmp_file_path, "w") as test_outfile:
                test_outfile.write("We are testing mewbot!")

            test_fs_input = FileTypeFSInput(input_path=tmp_file_path)
            assert isinstance(test_fs_input, FileTypeFSInput)

            # We need to retain control of the thread to preform shutdown
            asyncio.get_running_loop().create_task(test_fs_input.run())

            await asyncio.sleep(0.5)
            # Note - manually stopping the loop seems to lead to a rather nasty cash

            # Tests are making a clean exist after this test

    @pytest.mark.asyncio
    async def test_FileTypeFSInput_existing_file_io_in_existing_file(self) -> None:
        """
        1 - Creating a file which actually exists
        2 - Starting the input
        3 - Append to that file - check this produces the expected event
        4 - Do it a few times - check the results continue to be produced
        """
        with tempfile.TemporaryDirectory() as tmp_dir_path:

            tmp_file_path = os.path.join(tmp_dir_path, "mewbot_test_file.test")
            with open(tmp_file_path, "w") as test_outfile:
                test_outfile.write("We are testing mewbot!")

            test_fs_input = FileTypeFSInput(input_path=tmp_file_path)
            assert isinstance(test_fs_input, FileTypeFSInput)

            output_queue: asyncio.Queue[InputEvent] = asyncio.Queue()
            test_fs_input.queue = output_queue

            # We need to retain control of the thread to delay shutdown
            # And to probe the results
            asyncio.get_running_loop().create_task(test_fs_input.run())

            # Give the class a chance to actually do init
            await asyncio.sleep(0.5)

            # Generate some events which should end up in the queue
            # - Using blocking methods - this should still work
            with open(tmp_file_path, "w") as test_outfile:
                test_outfile.write("\nThe testing will continue until moral improves!")

            # This should have generated an event
            queue_out = await output_queue.get()
            assert isinstance(queue_out, UpdatedFileFSInputEvent)

            # There should be no other events in the queue
            output_queue_qsize = output_queue.qsize()
            assert (
                output_queue_qsize == 0
            ), f"Output queue actually has {output_queue_qsize} entries"

            # Indicate to the queue that task processing is complete
            output_queue.task_done()

            # Tests are NOT making a clean exist after this test
            # This seems to be a problem with the prescence of a queue
