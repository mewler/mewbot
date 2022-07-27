# Aim is to run, in sections, as many of the input methods as possible
# Including running a full bot with logging triggers and actions.
# However, individual components also have to be isolated for testing purposes.

import asyncio
import shutil
import sys
import tempfile
import os

from typing import Tuple

import pytest

from mewbot.api.v1 import InputEvent
from mewbot.io.file_system import (
    FileTypeFSInput,
)
from .utils import FileSystemTestUtils


# pylint: disable=invalid-name
# for clarity, test functions should be named after the things they test
# which means CamelCase in function names


platform_str: str = sys.platform
if platform_str == "win32":
    detected_os: str = "windows"
else:
    detected_os: str = "linux"


class TestFileTypeFSInput(FileSystemTestUtils):

    # - INIT AND ATTRIBUTES

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
    async def test_FileTypeFSInput_run_without_error_inside_existing_dir(self) -> None:
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
            with open(tmp_file_path, "w", encoding="utf-8") as test_outfile:
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
            with open(tmp_file_path, "w", encoding="utf-8") as test_outfile:
                test_outfile.write("We are testing mewbot!")

            test_fs_input = FileTypeFSInput(input_path=tmp_file_path)
            assert isinstance(test_fs_input, FileTypeFSInput)

            output_queue: asyncio.Queue[InputEvent] = asyncio.Queue()
            test_fs_input.queue = output_queue

            # We need to retain control of the thread to delay shutdown
            # And to probe the results
            run_task = asyncio.get_running_loop().create_task(test_fs_input.run())

            # Give the class a chance to actually do init
            await asyncio.sleep(0.5)

            # Generate some events which should end up in the queue
            # - Using blocking methods - this should still work
            with open(tmp_file_path, "w", encoding="utf-8") as test_outfile:
                test_outfile.write("\nThe testing will continue until moral improves!")

            await self.process_file_update_response(output_queue)

            for i in range(20):

                # Generate some events which should end up in the queue
                # - Using blocking methods - this should still work
                with open(tmp_file_path, "w", encoding="utf-8") as test_outfile:
                    test_outfile.write(
                        f"\nThe testing will continue until moral improves! - time {i}"
                    )

                await self.process_file_update_response(output_queue)

            # Otherwise the queue seems to be blocking pytest from a clean exit.
            await self.cancel_task(run_task)

            # Tests are NOW making a clean exist after this test
            # This seems to have been a problem with the presence of a queue

    @pytest.mark.asyncio
    async def test_FileTypeFSInput_create_update_delete_target_file_loop(self) -> None:
        """
        1 - Start without a file at all.
        2 - Starting the input
        3 - Create a file - check for the file creation event
        3 - Append to that file - check this produces the expected event
        4 - Delete the file - looking for the event
        4 - Do it a few times - check the results continue to be produced
        """
        with tempfile.TemporaryDirectory() as tmp_dir_path:

            input_path = os.path.join(tmp_dir_path, "test_file_delete_me.txt")

            run_task, output_queue = await self.get_FileTypeFSInput(input_path)

            for i in range(10):

                with open(input_path, "w", encoding="utf-8") as test_outfile:
                    test_outfile.write(
                        f"\nThe testing will continue until moral improves! - time {i}"
                    )
                await self.process_input_file_creation_response(output_queue)

                with open(input_path, "w", encoding="utf-8") as test_outfile:
                    test_outfile.write(
                        f"\nThe testing will continue until moral improves! - time {i}"
                    )

                await self.process_file_update_response(output_queue)

                with open(input_path, "a", encoding="utf-8") as test_outfile:
                    test_outfile.write(
                        f"\nThe testing will continue until moral improves! - time {i}"
                    )

                await self.process_file_update_response(output_queue)

                os.unlink(input_path)
                await self.process_input_file_deletion_response(output_queue)

            await self.cancel_task(run_task)

    @pytest.mark.asyncio
    async def test_FileTypeFSInput_existing_file_io_in_non_existing_file(self) -> None:
        """
        1 - Start without a file at all.
        2 - Starting the input
        3 - Create a file - check for the file creation event
        3 - Append to that file - check this produces the expected event
        4 - Delete the file - looking for the event
        4 - Do it a few times - check the results continue to be produced
        """
        with tempfile.TemporaryDirectory() as tmp_dir_path:

            # io will be done on this file
            tmp_file_path = os.path.join(tmp_dir_path, "mewbot_test_file.test")

            test_fs_input = FileTypeFSInput(input_path=tmp_file_path)
            assert isinstance(test_fs_input, FileTypeFSInput)

            output_queue: asyncio.Queue[InputEvent] = asyncio.Queue()
            test_fs_input.queue = output_queue

            # We need to retain control of the thread to delay shutdown
            # And to probe the results
            run_task = asyncio.get_running_loop().create_task(test_fs_input.run())

            # Give the class a chance to actually do init
            await asyncio.sleep(0.5)

            with open(tmp_file_path, "w", encoding="utf-8") as test_outfile:
                test_outfile.write("We are testing mewbot!")

            await self.process_input_file_creation_response(output_queue)

            # Generate some events which should end up in the queue
            # - Using blocking methods - this should still work
            with open(tmp_file_path, "w", encoding="utf-8") as test_outfile:
                test_outfile.write("\nThe testing will continue until moral improves!")

            await self.process_file_update_response(output_queue)

            for i in range(5):

                # Generate some events which should end up in the queue
                # - Using blocking methods - this should still work
                with open(tmp_file_path, "w", encoding="utf-8") as test_outfile:
                    test_outfile.write(
                        f"\nThe testing will continue until moral improves! - time {i}"
                    )
                await self.process_file_update_response(output_queue)

                # Delete the file - then recreate it
                os.unlink(tmp_file_path)

                await self.process_input_file_deletion_response(output_queue)

                # Generate some events which should end up in the queue
                # - Using blocking methods - this should still work
                with open(tmp_file_path, "w", encoding="utf-8") as test_outfile:
                    test_outfile.write(
                        "\nThe testing will continue until moral improves!"
                    )

                await self.process_input_file_creation_response(output_queue)

            # Otherwise the queue seems to be blocking pytest from a clean exit.
            await self.cancel_task(run_task)

            # Tests are NOW making a clean exist after this test
            # This seems to have been a problem with the presence of a queue

    @pytest.mark.asyncio
    async def test_FileTypeFSInput_existing_dir_deleted_and_replaced_with_file(
        self,
    ) -> None:
        """
        1 - Start without a file at all.
        2 - Starting the input
        3 - create a dir at the monitored location - this should do nothing
        4 - delete that dir
        5 - Create a file - check for the file creation event
        6 - Append to that file - check this produces the expected event
        7 - Delete the file - looking for the event
        8 - Do it a few times - check the results continue to be produced
        """
        with tempfile.TemporaryDirectory() as tmp_dir_path:

            # io will be done on this file
            tmp_file_path = os.path.join(tmp_dir_path, "mewbot_test_file.test")

            run_task, output_queue = await self.get_FileTypeFSInput(tmp_file_path)

            # Give the class a chance to actually do init
            await asyncio.sleep(0.5)

            # Make a dir - the class should not respond
            os.mkdir(tmp_file_path)

            await asyncio.sleep(0.5)

            await self.verify_queue_size(output_queue, task_done=False)

            # Delete the file - the class should also not respond
            os.rmdir(tmp_file_path)

            await asyncio.sleep(0.5)

            await self.verify_queue_size(output_queue, task_done=False)

            with open(tmp_file_path, "w", encoding="utf-8") as test_outfile:
                test_outfile.write("We are testing mewbot!")

            await self.process_input_file_creation_response(output_queue)

            # Generate some events which should end up in the queue
            # - Using blocking methods - this should still work
            with open(tmp_file_path, "w", encoding="utf-8") as test_outfile:
                test_outfile.write("\nThe testing will continue until moral improves!")

            await self.process_file_update_response(output_queue)

            for i in range(5):
                # Generate some events which should end up in the queue
                # - Using blocking methods - this should still work
                with open(tmp_file_path, "w", encoding="utf-8") as test_outfile:
                    test_outfile.write(
                        f"\nThe testing will continue until moral improves! - time {i}"
                    )
                await self.process_file_update_response(output_queue)

                # Delete the file - then recreate it
                os.unlink(tmp_file_path)

                await self.process_input_file_deletion_response(output_queue)

                # Generate some events which should end up in the queue
                # - Using blocking methods - this should still work
                with open(tmp_file_path, "w", encoding="utf-8") as test_outfile:
                    test_outfile.write(
                        "\nThe testing will continue until moral improves!"
                    )

                await self.process_input_file_creation_response(output_queue)

            # Otherwise the queue seems to be blocking pytest from a clean exit.
            await self.cancel_task(run_task)

            # Tests are NOW making a clean exist after this test
            # This seems to have been a problem with the presence of a queue

    @pytest.mark.asyncio
    async def test_FileTypeFSInput_create_update_delete_target_file_dir_overwrite(
        self,
    ) -> None:
        """
        1 - Start without a file at all.
        2 - Starting the input
        3 - Create a file - check for the file creation event
        3 - Append to that file - check this produces the expected event
        4 - Overwrite the file with a dir - this should crash the observer
            But it should be caught and an appopriate event generated
        """
        with tempfile.TemporaryDirectory() as tmp_dir_path:

            input_path = os.path.join(tmp_dir_path, "test_file_delete_me.txt")

            run_task, output_queue = await self.get_FileTypeFSInput(input_path)

            for i in range(10):

                with open(input_path, "w", encoding="utf-8") as test_outfile:
                    test_outfile.write(
                        f"\nThe testing will continue until moral improves! - time {i}"
                    )
                await self.process_input_file_creation_response(output_queue)

                with open(input_path, "w", encoding="utf-8") as test_outfile:
                    test_outfile.write(
                        f"\nThe testing will continue until moral improves! - time {i}"
                    )

                await self.process_file_update_response(output_queue)

                with open(input_path, "a", encoding="utf-8") as test_outfile:
                    test_outfile.write(
                        f"\nThe testing will continue until moral improves! - time {i}"
                    )

                await self.process_file_update_response(output_queue)

                test_dir_path = os.path.join(tmp_dir_path, "test_dir_del_me")
                os.mkdir(test_dir_path)

                # Attempt to copy a dir over the top of the input file
                # this should fail with no effect.
                try:
                    shutil.copytree(test_dir_path, input_path)
                except FileExistsError:
                    pass

                shutil.rmtree(test_dir_path)
                os.unlink(input_path)

                await self.process_input_file_deletion_response(output_queue)

                # Make a folder at the monitored path - this should produce no result
                os.mkdir(input_path)

                shutil.rmtree(input_path)

            await self.cancel_task(run_task)

    @staticmethod
    async def get_FileTypeFSInput(
        input_path: str,
    ) -> Tuple[asyncio.Task[None], asyncio.Queue[InputEvent]]:

        test_fs_input = FileTypeFSInput(input_path=input_path)
        assert isinstance(test_fs_input, FileTypeFSInput)

        output_queue: asyncio.Queue[InputEvent] = asyncio.Queue()
        test_fs_input.queue = output_queue

        # We need to retain control of the thread to delay shutdown
        # And to probe the results
        run_task = asyncio.get_running_loop().create_task(test_fs_input.run())

        return run_task, output_queue
