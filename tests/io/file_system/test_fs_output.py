# Aim is to run, in sections, as many of the input methods as possible
# Including running a full bot with logging triggers and actions.
# However, individual components also have to be isolated for testing purposes.

# import shutil
import tempfile
import os
import sys

import pytest

from mewbot.io.file_system import (
    FileSystemOutput,
    CreateFileFSOutputEvent,
    AppendFileFSOutputEvent,
    OverwriteFileFSOutputEvent,
    DeleteFileFSOutputEvent,
)
from .utils import FileSystemTestUtils


# pylint: disable=invalid-name
# for clarity, test functions should be named after the things they test
# which means CamelCase in function names


class TestFileTypeFSOutput(FileSystemTestUtils):

    # - INIT AND ATTRIBUTES
    @pytest.mark.asyncio
    async def test_FileSystemOutput__init__input_path_None(self) -> None:
        """
        Tests that we can start an isolated copy of FileTypeFSInput - for testing purposes.
        input_path is set to None
        """
        test_fs_input = FileSystemOutput(output_path=None)
        assert isinstance(test_fs_input, FileSystemOutput)

    @pytest.mark.asyncio
    async def test_FileSystemOutput__init__output_path_nonsense(self) -> None:
        """
        Tests that we can start an isolated copy of FileTypeFSInput - for testing purposes.
        """
        output_path_str = "\\///blargleblarge_not_a_path"
        test_fs_output = FileSystemOutput(output_path=output_path_str)
        assert isinstance(test_fs_output, FileSystemOutput)
        assert test_fs_output.output_path_exists is False

        # Test attributes which should have been set
        assert test_fs_output.output_path == output_path_str
        test_fs_output.output_path = "//\\another thing which does not exist"

        assert test_fs_output.output_path_exists is False

        try:
            test_fs_output.output_path_exists = True
        except AttributeError:
            pass

    @pytest.mark.asyncio
    async def test_FileTypeFSInput__init__input_path_existing_dir(self) -> None:
        """
        Tests that we can start an isolated copy of FileTypeFSInput - for testing purposes.

        """
        with tempfile.TemporaryDirectory() as tmp_dir_path:
            test_fs_input = FileSystemOutput(output_path=tmp_dir_path)
            assert isinstance(test_fs_input, FileSystemOutput)

            assert test_fs_input.output_path == tmp_dir_path
            assert test_fs_input.output_path_exists is True

    # - OUTPUT
    @pytest.mark.asyncio
    async def test_FileSystemOutput_CreateFileFSOutputEvent(self) -> None:
        """
        Tests that a CreateFileFSOutputEvent is written out to disk as expected.
        """
        with tempfile.TemporaryDirectory() as tmp_dir_path:
            test_fs_output = await self.get_FileSystemOutput(tmp_dir_path)

            test_file_name = "test_event_del_me.txt"
            test_file_contents = "This is a test"
            test_event = CreateFileFSOutputEvent(
                file_name=test_file_name, file_contents=test_file_contents, is_binary=False
            )

            status = await test_fs_output.output(test_event)
            assert status is True

            # Check the file actually exists
            expected_output_path = os.path.join(tmp_dir_path, test_file_name)
            assert os.path.exists(expected_output_path)
            assert os.path.isfile(expected_output_path)

            with open(
                expected_output_path, "r", encoding=sys.getdefaultencoding()
            ) as expected_outfile:
                assert expected_outfile.read() == test_file_contents

    @pytest.mark.asyncio
    async def test_FileSystemOutput_AppendFileFSOutputEvent(self) -> None:
        """
        Tests that a CreateFileFSOutputEvent is written out to disk as expected.
        """
        with tempfile.TemporaryDirectory() as tmp_dir_path:
            test_fs_output = await self.get_FileSystemOutput(tmp_dir_path)

            # Writing an object out for appending
            test_file_name = "test_event_for_app_me.txt"
            test_file_contents = "This is a test - an endless series of them"
            test_event = CreateFileFSOutputEvent(
                file_name=test_file_name, file_contents=test_file_contents, is_binary=False
            )

            cre_status = await test_fs_output.output(test_event)
            assert cre_status is True

            # Check the file actually exists
            expected_output_path = os.path.join(tmp_dir_path, test_file_name)
            assert os.path.exists(expected_output_path)
            assert os.path.isfile(expected_output_path)

            with open(
                expected_output_path, "r", encoding=sys.getdefaultencoding()
            ) as expected_outfile:
                assert expected_outfile.read() == test_file_contents

            # Append to the file
            test_app_file_contents = "\nAppending to the file."
            test_app_event = AppendFileFSOutputEvent(
                file_name=test_file_name,
                file_contents=test_app_file_contents,
                is_binary=False,
            )

            app_status = await test_fs_output.output(test_app_event)
            assert app_status is True

            # Check the file actually exists
            expected_output_path = os.path.join(tmp_dir_path, test_file_name)
            assert os.path.exists(expected_output_path)
            assert os.path.isfile(expected_output_path)

            with open(
                expected_output_path, "r", encoding=sys.getdefaultencoding()
            ) as expected_outfile:
                assert expected_outfile.read() == test_file_contents + test_app_file_contents

    @pytest.mark.asyncio
    async def test_FileSystemOutput_OverwriteFileFSOutputEvent(self) -> None:
        """
        Tests that a CreateFileFSOutputEvent is written out to disk as expected.
        """
        with tempfile.TemporaryDirectory() as tmp_dir_path:
            test_fs_output = await self.get_FileSystemOutput(tmp_dir_path)

            # Writing an object out for appending
            test_file_name = "test_event_for_app_me.txt"
            test_file_contents = "This is a test - an endless series of them"
            test_event = CreateFileFSOutputEvent(
                file_name=test_file_name, file_contents=test_file_contents, is_binary=False
            )

            cre_status = await test_fs_output.output(test_event)
            assert cre_status is True

            # Check the file actually exists
            expected_output_path = os.path.join(tmp_dir_path, test_file_name)
            assert os.path.exists(expected_output_path)
            assert os.path.isfile(expected_output_path)

            with open(
                expected_output_path, "r", encoding=sys.getdefaultencoding()
            ) as expected_outfile:
                assert expected_outfile.read() == test_file_contents

            # Append to the file
            test_app_file_contents = "\nAppending to the file."
            test_app_event = OverwriteFileFSOutputEvent(
                file_name=test_file_name,
                file_contents=test_app_file_contents,
                is_binary=False,
            )

            app_status = await test_fs_output.output(test_app_event)
            assert app_status is True

            # Check the file actually exists
            expected_output_path = os.path.join(tmp_dir_path, test_file_name)
            assert os.path.exists(expected_output_path)
            assert os.path.isfile(expected_output_path)

            with open(
                expected_output_path, "r", encoding=sys.getdefaultencoding()
            ) as expected_outfile:
                assert expected_outfile.read() == test_app_file_contents

    @pytest.mark.asyncio
    async def test_FileSystemOutput_DeleteFileFSOutputEvent(self) -> None:
        """
        Tests that a CreateFileFSOutputEvent is written out to disk as expected.
        """
        with tempfile.TemporaryDirectory() as tmp_dir_path:
            test_fs_output = await self.get_FileSystemOutput(tmp_dir_path)

            # Writing an object out for appending
            test_file_name = "test_event_for_app_me.txt"
            test_file_contents = "This is a test - an endless series of them"
            test_event = CreateFileFSOutputEvent(
                file_name=test_file_name, file_contents=test_file_contents, is_binary=False
            )

            cre_status = await test_fs_output.output(test_event)
            assert cre_status is True

            # Check the file actually exists
            expected_output_path = os.path.join(tmp_dir_path, test_file_name)
            assert os.path.exists(expected_output_path)
            assert os.path.isfile(expected_output_path)

            with open(
                expected_output_path, "r", encoding=sys.getdefaultencoding()
            ) as expected_outfile:
                assert expected_outfile.read() == test_file_contents

            # Delete the file
            test_del_event = DeleteFileFSOutputEvent(
                file_name=test_file_name,
            )

            del_status = await test_fs_output.output(test_del_event)
            assert del_status is True

            # Check the file actually exists
            expected_output_path = os.path.join(tmp_dir_path, test_file_name)
            assert not os.path.exists(expected_output_path)
            assert not os.path.isfile(expected_output_path)

    @staticmethod
    async def get_FileSystemOutput(
        output_path: str,
    ) -> FileSystemOutput:

        test_fs_output = FileSystemOutput(output_path=output_path)
        assert isinstance(test_fs_output, FileSystemOutput)

        return test_fs_output
