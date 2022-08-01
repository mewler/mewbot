# Aim is to run, in sections, as many of the input methods as possible
# Including running a full bot with logging triggers and actions.
# However, individual components also have to be isolated for testing purposes.

import asyncio
import os
import shutil
import sys
import tempfile

import pytest

from mewbot.io.file_system import (
    DirTypeFSInput,
)

from .utils import FileSystemTestUtilsDirEvents, FileSystemTestUtilsFileEvents

from mewbot.io.file_system.events import (
    InputFileFileCreationInputEvent,
    InputFileFileDeletionInputEvent,
    InputFileDirCreationInputEvent,
    InputFileDirDeletionInputEvent,

    FileFSInputEvent,
    CreatedFileFSInputEvent,
    UpdatedFileFSInputEvent,
    MovedFileFSInputEvent,
    DeletedFileFSInputEvent,

    DirFSInputEvent,
    CreatedDirFSInputEvent,
    MovedDirFSInputEvent,
    UpdatedDirFSInputEvent,
    DeletedDirFSInputEvent,

)

# pylint: disable=invalid-name
# for clarity, test functions should be named after the things they test
# which means CamelCase in function names

# pylint: disable=duplicate-code
# Due to testing for the subtle differences between how the monitors respond in windows and
# linux, code has - inevitably - ended up very similar.
# As such, this inspection has had to be disabled.


class TestDirTypeFSInput(FileSystemTestUtilsDirEvents, FileSystemTestUtilsFileEvents):

    # - INIT AND ATTRIBUTES

    @pytest.mark.asyncio
    async def test_DirTypeFSInput__init__input_path_None(self) -> None:
        """
        Tests that we can start an isolated copy of FileTypeFSInput - for testing purposes.
        input_path is set to None
        """
        test_fs_input = DirTypeFSInput(input_path=None)
        assert isinstance(test_fs_input, DirTypeFSInput)

    @pytest.mark.asyncio
    async def test_DirTypeFSInput__init__input_path_nonsense(self) -> None:
        """
        Tests that we can start an isolated copy of FileTypeFSInput - for testing purposes.
        """
        input_path_str = "\\///blargleblarge_not_a_path"
        test_fs_input = DirTypeFSInput(input_path=input_path_str)

        assert test_fs_input.input_path_exists is False

        # Test attributes which should have been set
        assert test_fs_input.input_path == input_path_str
        test_fs_input.input_path = "//\\another thing which does not exist"

        try:
            test_fs_input.input_path_exists = True
        except AttributeError:
            pass

        assert test_fs_input.input_path_exists is False

    @pytest.mark.asyncio
    async def test_DirTypeFSInput__init__input_path_existing_dir(self) -> None:
        """
        Tests that we can start an isolated copy of FileTypeFSInput - for testing purposes.

        """
        with tempfile.TemporaryDirectory() as tmp_dir_path:
            test_fs_input = DirTypeFSInput(input_path=tmp_dir_path)

            assert test_fs_input.input_path == tmp_dir_path
            assert test_fs_input.input_path_exists is True

            assert isinstance(test_fs_input, DirTypeFSInput)

    # - RUNNING TO DETECT FILE CHANGES

    @pytest.mark.asyncio
    async def testDirTypeFSInput_existing_dir_create_file(self) -> None:
        """
        Check for the expected created signal from a file which is created in a monitored dir
        """
        with tempfile.TemporaryDirectory() as tmp_dir_path:

            run_task, output_queue = await self.get_DirTypeFSInput(tmp_dir_path)

            # - Using blocking methods - this should still work
            new_file_path = os.path.join(tmp_dir_path, "text_file_delete_me.txt")

            with open(new_file_path, "w", encoding="utf-16") as output_file:
                output_file.write("Here we go")

            await self.process_file_event_queue_response(
                output_queue=output_queue,
                file_path=new_file_path,
                event_type=CreatedFileFSInputEvent
            )

            await self.cancel_task(run_task)

    @pytest.mark.asyncio
    @pytest.mark.skipif(sys.platform.startswith("win"), reason="Linux (like) only test")
    async def testDirTypeFSInput_existing_dir_cre_upd_del_file_linux(self) -> None:
        """
        Check for the expected created signal from a file which is created in a monitored dir
        Followed by an attempt to update the file.
        Followed by deleting that file.
        """
        with tempfile.TemporaryDirectory() as tmp_dir_path:
            run_task, output_queue = await self.get_DirTypeFSInput(tmp_dir_path)

            # - Using blocking methods - this should still work
            new_dir_path = os.path.join(tmp_dir_path, "text_file_delete_me.txt")

            with open(new_dir_path, "w", encoding="utf-16") as output_file:
                output_file.write("Here we go")
            await self.process_file_event_queue_response(
                output_queue=output_queue, file_path=new_dir_path, message=f"{new_dir_path} written",
                event_type=CreatedFileFSInputEvent
            )

            with open(new_dir_path, "a", encoding="utf-16") as output_file:
                output_file.write("Here we go again")
            await self.process_dir_event_queue_response(
                output_queue=output_queue,
                dir_path=tmp_dir_path,
                allowed_queue_size=1,
                message=f"{new_dir_path} written",
                event_type=UpdatedDirFSInputEvent
            )
            await self.process_file_event_queue_response(
                output_queue=output_queue,
                file_path=new_dir_path,
                event_type=UpdatedFileFSInputEvent
            )

            os.unlink(new_dir_path)
            await self.process_dir_event_queue_response(
                output_queue=output_queue,
                dir_path=tmp_dir_path,
                allowed_queue_size=1,
                event_type=UpdatedDirFSInputEvent
            )

            # Probably do not want
            await self.process_file_event_queue_response(
                output_queue=output_queue,
                file_path=new_dir_path,
                event_type=UpdatedFileFSInputEvent
            )
            await self.process_dir_event_queue_response(
                output_queue=output_queue,
                dir_path=tmp_dir_path,
                allowed_queue_size=1,
                event_type=UpdatedDirFSInputEvent
            )
            await self.process_file_event_queue_response(
                output_queue=output_queue,
                file_path=new_dir_path,
                event_type=DeletedFileFSInputEvent
            )

            await self.cancel_task(run_task)

    @pytest.mark.asyncio
    async def testDirTypeFSInput_existing_dir_create_update_file(self) -> None:
        """
        Check for the expected created signal from a file which is created in a monitored dir
        Followed by an attempt to update the file.
        """
        with tempfile.TemporaryDirectory() as tmp_dir_path:
            run_task, output_queue = await self.get_DirTypeFSInput(tmp_dir_path)

            # - Using blocking methods - this should still work
            new_file_path = os.path.join(tmp_dir_path, "text_file_delete_me.txt")

            with open(new_file_path, "w", encoding="utf-16") as output_file:
                output_file.write("Here we go")
            await self.process_file_event_queue_response(
                output_queue=output_queue,
                file_path=new_file_path,
                event_type=CreatedFileFSInputEvent
            )

            with open(new_file_path, "a", encoding="utf-16") as output_file:
                output_file.write("Here we go again")
            await self.process_dir_event_queue_response(
                output_queue=output_queue,
                dir_path=tmp_dir_path,
                allowed_queue_size=1,
                event_type=UpdatedDirFSInputEvent
            )
            await self.process_file_event_queue_response(
                output_queue=output_queue,
                file_path=new_file_path,
                event_type=UpdatedFileFSInputEvent
            )

            await self.cancel_task(run_task)

    @pytest.mark.asyncio
    @pytest.mark.skipif(sys.platform.startswith("win"), reason="Linux (like) only test")
    async def testDirTypeFSInput_existing_dir_cre_upd_del_file_loop_linux(self) -> None:
        """
        Check for expected created signal from a file which is created in a monitored dir
        Followed by an attempt to update the file.
        Then an attempt to delete the file.
        This is done in a loop - to check for any problems with stale events
        """
        with tempfile.TemporaryDirectory() as tmp_dir_path:
            run_task, output_queue = await self.get_DirTypeFSInput(tmp_dir_path)

            for i in range(8):

                # - Using blocking methods - this should still work
                new_file_path = os.path.join(tmp_dir_path, "text_file_delete_me.txt")

                with open(new_file_path, "w", encoding="utf-16") as output_file:
                    output_file.write("Here we go")
                # This is just ... utterly weird
                if i == 0:
                    await self.process_file_event_queue_response(
                        output_queue=output_queue,
                        file_path=new_file_path,
                        message=f"in loop {i}",
                        event_type=CreatedFileFSInputEvent
                    )
                else:
                    await self.process_dir_event_queue_response(
                        output_queue=output_queue,
                        dir_path=tmp_dir_path,
                        message=f"in loop {i}",
                        event_type=UpdatedDirFSInputEvent
                    )
                    await self.process_file_event_queue_response(
                        output_queue=output_queue,
                        file_path=new_file_path,
                        message=f"in loop {i}",
                        event_type=CreatedFileFSInputEvent
                    )

                with open(new_file_path, "a", encoding="utf-16") as output_file:
                    output_file.write(f"Here we go again - {i}")

                await self.process_dir_event_queue_response(
                    output_queue=output_queue,
                    dir_path=tmp_dir_path,
                    event_type=UpdatedDirFSInputEvent
                )
                await self.process_file_event_queue_response(
                    output_queue=output_queue,
                    file_path=new_file_path,
                    event_type=UpdatedFileFSInputEvent
                )

                os.unlink(new_file_path)
                await self.process_dir_event_queue_response(
                    output_queue=output_queue,
                    dir_path=tmp_dir_path,
                    event_type=UpdatedDirFSInputEvent
                )

                # Probably do not want
                await self.process_file_event_queue_response(
                    output_queue=output_queue,
                    file_path=new_file_path,
                    message=f"in loop {i}",
                    event_type=UpdatedFileFSInputEvent
                )

                await self.process_dir_event_queue_response(
                    output_queue=output_queue,
                    dir_path=tmp_dir_path,
                    message=f"in loop {i}",
                    event_type=UpdatedDirFSInputEvent
                )
                await self.process_file_event_queue_response(
                    output_queue=output_queue,
                    file_path=new_file_path,
                    message=f"in loop {i}",
                    event_type=DeletedFileFSInputEvent
                )

            await self.cancel_task(run_task)

    @pytest.mark.asyncio
    @pytest.mark.skipif(sys.platform.startswith("win"), reason="Linux (like) only test")
    async def testDirTypeFSInput_existing_dir_create_update_move_file_linux(self) -> None:
        """
        Check for the expected created signal from a file which is created in a monitored dir
        Followed by an attempt to update the file.
        """
        with tempfile.TemporaryDirectory() as tmp_dir_path:
            run_task, output_queue = await self.get_DirTypeFSInput(tmp_dir_path)

            # - Using blocking methods - this should still work
            new_file_path = os.path.join(tmp_dir_path, "text_file_delete_me.txt")

            with open(new_file_path, "w", encoding="utf-16") as output_file:
                output_file.write("Here we go")
            await self.process_file_event_queue_response(
                output_queue=output_queue,
                file_path=new_file_path,
                event_type=CreatedFileFSInputEvent
            )

            with open(new_file_path, "a", encoding="utf-16") as output_file:
                output_file.write("Here we go again")
            await self.process_dir_event_queue_response(
                output_queue=output_queue,
                dir_path=tmp_dir_path,
                event_type=UpdatedDirFSInputEvent
            )
            await self.process_file_event_queue_response(
                output_queue=output_queue,
                file_path=new_file_path,
                event_type=UpdatedFileFSInputEvent
            )

            # Move a file to a different location
            post_move_file_path = os.path.join(tmp_dir_path, "moved_text_file_delete_me.txt")
            os.rename(src=new_file_path, dst=post_move_file_path)

            await self.process_dir_event_queue_response(
                output_queue=output_queue,
                dir_path=tmp_dir_path,
                event_type=UpdatedDirFSInputEvent
            )
            await self.process_file_event_queue_response(
                output_queue=output_queue,
                file_path=new_file_path,
                event_type=UpdatedFileFSInputEvent
            )
            await self.process_dir_event_queue_response(
                output_queue=output_queue,
                dir_path=tmp_dir_path,
                event_type=UpdatedDirFSInputEvent
            )
            await self.process_file_move_queue_response(
                output_queue,
                file_src_parth=new_file_path,
                file_dst_path=post_move_file_path,
            )

            await self.cancel_task(run_task)

    @pytest.mark.asyncio
    @pytest.mark.skipif(sys.platform.startswith("win"), reason="Linux (like) only test")
    async def testDirTypeFSInput_existing_dir_create_update_move_file_loop_linux(
        self,
    ) -> None:
        """
        Check for the expected created signal from a file which is created in a monitored dir
        Followed by an attempt to update the file.
        """
        with tempfile.TemporaryDirectory() as tmp_dir_path:
            run_task, output_queue = await self.get_DirTypeFSInput(tmp_dir_path)

            for i in range(10):

                # - Using blocking methods - this should still work
                new_file_path = os.path.join(tmp_dir_path, "text_file_delete_me.txt")

                with open(new_file_path, "w", encoding="utf-16") as output_file:
                    output_file.write("Here we go")

                await asyncio.sleep(0.5)
                output_queue_list = self.dump_queue_to_list(output_queue)

                self.check_queue_for_file_creation_input_event(
                    output_queue=output_queue_list, file_path=new_file_path, message=f"in loop {i}"
                )

                with open(new_file_path, "a", encoding="utf-16") as output_file:
                    output_file.write("Here we go again")

                await asyncio.sleep(0.1)

                output_queue_list = self.dump_queue_to_list(output_queue)

                self.check_queue_for_dir_update_input_event(
                    output_queue=output_queue_list,
                    dir_path=tmp_dir_path,
                    message=f"in loop {i}",
                )
                self.check_queue_for_file_update_input_event(
                    output_queue=output_queue_list,
                    file_path=new_file_path,
                    message=f"in loop {i}",
                )

                # Move a file to a different location
                post_move_file_path = os.path.join(
                    tmp_dir_path, "moved_text_file_delete_me.txt"
                )
                os.rename(src=new_file_path, dst=post_move_file_path)
                await asyncio.sleep(0.5)

                output_queue_list = self.dump_queue_to_list(output_queue)

                self.check_queue_for_dir_update_input_event(
                    output_queue=output_queue_list, dir_path=tmp_dir_path, message=f"in loop {i}"
                )
                self.check_queue_for_file_move_input_event(
                    output_queue=output_queue_list,
                    file_src_parth=new_file_path,
                    file_dst_path=post_move_file_path,
                    message=f"in loop {i}"
                )

            await self.cancel_task(run_task)

    # - RUNNING TO DETECT DIR CHANGES

    @pytest.mark.asyncio
    async def testDirTypeFSInput_existing_dir_create_dir(self) -> None:
        """
        Check for the expected created signal from a dir which is created in a monitored dir
        """
        with tempfile.TemporaryDirectory() as tmp_dir_path:

            run_task, output_queue = await self.get_DirTypeFSInput(tmp_dir_path)

            # - Using blocking methods - this should still work
            new_dir_path = os.path.join(tmp_dir_path, "text_file_delete_me.txt")

            os.mkdir(new_dir_path)
            await self.process_dir_event_queue_response(
                output_queue=output_queue,
                dir_path=new_dir_path,
                event_type=CreatedDirFSInputEvent
            )

            await self.cancel_task(run_task)

    @pytest.mark.asyncio
    @pytest.mark.skipif(sys.platform.startswith("win"), reason="Linux (like) only test")
    async def testDirTypeFSInput_existing_dir_cre_del_dir_windows(self) -> None:
        """
        Check that we get the expected created signal from a dir created in a monitored dir
        Followed by an attempt to update the file.
        """
        with tempfile.TemporaryDirectory() as tmp_dir_path:
            run_task, output_queue = await self.get_DirTypeFSInput(tmp_dir_path)

            # - Using blocking methods - this should still work
            new_dir_path = os.path.join(tmp_dir_path, "text_file_delete_me.txt")

            os.mkdir(new_dir_path)
            await self.process_dir_event_queue_response(
                output_queue=output_queue,
                dir_path=new_dir_path,
                event_type=CreatedDirFSInputEvent,
            )

            shutil.rmtree(new_dir_path)
            await self.process_dir_event_queue_response(
                output_queue=output_queue,
                dir_path=tmp_dir_path,
                event_type=UpdatedDirFSInputEvent,
            )
            await self.process_dir_event_queue_response(
                output_queue=output_queue,
                dir_path=new_dir_path,
                event_type=DeletedDirFSInputEvent,
            )

            await self.cancel_task(run_task)

    @pytest.mark.asyncio
    @pytest.mark.skipif(sys.platform.startswith("win"), reason="Linux (like) only test")
    async def testDirTypeFSInput_existing_dir_cre_del_dir_loop_linux(self) -> None:
        """
        Checks we get the expected created signal from a file which is created in a monitored dir
        Followed by an attempt to update the file.
        Then an attempt to delete the file.
        This is done in a loop - to check for any problems with stale events
        """
        with tempfile.TemporaryDirectory() as tmp_dir_path:
            run_task, output_queue = await self.get_DirTypeFSInput(tmp_dir_path)

            for i in range(10):
                # - Using blocking methods - this should still work
                new_dir_path = os.path.join(tmp_dir_path, "text_file_delete_me_txt")

                os.mkdir(new_dir_path)
                if i == 0:
                    await self.process_dir_event_queue_response(
                        output_queue=output_queue,
                        dir_path=new_dir_path,
                        message=f"in loop {i}",
                        event_type=CreatedDirFSInputEvent
                    )

                else:

                    await self.process_dir_event_queue_response(
                        output_queue=output_queue,
                        dir_path=tmp_dir_path,
                        message=f"in loop {i}",
                        event_type=UpdatedDirFSInputEvent
                    )
                    await self.process_dir_event_queue_response(
                        output_queue=output_queue,
                        dir_path=new_dir_path,
                        message=f"in loop {i}",
                        event_type=CreatedDirFSInputEvent
                    )

                shutil.rmtree(new_dir_path)
                await self.process_dir_event_queue_response(
                    output_queue=output_queue,
                    dir_path=tmp_dir_path,
                    message=f"in loop {i}",
                    event_type=UpdatedDirFSInputEvent
                )
                await self.process_dir_event_queue_response(
                    output_queue=output_queue,
                    dir_path=new_dir_path,
                    message=f"in loop {i}",
                    event_type=DeletedDirFSInputEvent
                )

            await self.cancel_task(run_task)

    @pytest.mark.asyncio
    @pytest.mark.skipif(sys.platform.startswith("win"), reason="Linux (like) only test")
    async def testDirTypeFSInput_existing_dir_create_move_dir_linux(self) -> None:
        """
        Checks we get the expected created signal from a dir which is created in a monitored dir
        Followed by moving the dir.
        """

        with tempfile.TemporaryDirectory() as tmp_dir_path:
            run_task, output_queue = await self.get_DirTypeFSInput(tmp_dir_path)

            # - Using blocking methods - this should still work
            new_dir_path = os.path.join(tmp_dir_path, "text_file_delete_me.txt")

            os.mkdir(new_dir_path)
            await self.process_dir_event_queue_response(
                output_queue=output_queue,
                dir_path=new_dir_path,
                event_type=CreatedDirFSInputEvent
            )

            await asyncio.sleep(0.1)

            # Move a file to a different location
            post_move_dir_path = os.path.join(tmp_dir_path, "moved_text_file_delete_me.txt")
            os.rename(src=new_dir_path, dst=post_move_dir_path)

            # This is an asymmetry between how files and folders handle delete
            # left in while I try and think how to deal sanely with it
            # await self.process_dir_deletion_response(output_queue, dir_path=new_dir_path)
            await self.process_dir_event_queue_response(
                output_queue=output_queue,
                dir_path=tmp_dir_path,
                event_type=UpdatedDirFSInputEvent
            )
            await self.process_file_move_queue_response(
                output_queue, file_src_parth=new_dir_path, file_dst_path=post_move_dir_path
            )

            await self.cancel_task(run_task)

    @pytest.mark.asyncio
    @pytest.mark.skipif(sys.platform.startswith("win"), reason="Linux (like) only test")
    async def testDirTypeFSInput_existing_dir_create_move_dir_loop_linux(self) -> None:
        """
        Checks we get the expected created signal from a dir which is created in a monitored dir
        Followed by moving the dir.
        Repeated in a loop.
        """
        with tempfile.TemporaryDirectory() as tmp_dir_path:

            new_subfolder_path = os.path.join(tmp_dir_path, "subfolder_1", "subfolder_2")
            os.makedirs(new_subfolder_path)

            run_task, output_queue = await self.get_DirTypeFSInput(tmp_dir_path)

            for i in range(10):

                # - Using blocking methods - this should still work
                new_dir_path = os.path.join(new_subfolder_path, "text_file_delete_me.txt")

                os.mkdir(new_dir_path)
                if i == 0:
                    await self.process_dir_event_queue_response(
                        output_queue=output_queue,
                        dir_path=new_dir_path,
                        message=f"linux - in loop {i}",
                        event_type=CreatedDirFSInputEvent
                    )
                else:
                    await self.process_dir_event_queue_response(
                        output_queue=output_queue,
                        dir_path=new_dir_path,
                        message=f"linux - in loop {i}",
                        event_type=CreatedDirFSInputEvent
                    )
                    await self.process_dir_event_queue_response(
                        output_queue=output_queue,
                        dir_path=new_subfolder_path,
                        message=f"linux - in loop {i}",
                        event_type=UpdatedDirFSInputEvent
                    )

                # Move a file to a different location
                post_move_dir_path = os.path.join(
                    new_subfolder_path, "moved_text_file_delete_me.txt"
                )
                os.rename(src=new_dir_path, dst=post_move_dir_path)

                # I think this is a Windows problem - probably.
                if i == 0:
                    await self.process_dir_event_queue_response(
                        output_queue=output_queue,
                        dir_path=new_subfolder_path,
                        message=f"in loop {i}",
                        event_type=UpdatedDirFSInputEvent
                    )
                await self.process_file_move_queue_response(
                    output_queue,
                    file_src_parth=new_dir_path,
                    file_dst_path=post_move_dir_path,
                )
                await self.process_dir_event_queue_response(
                    output_queue=output_queue,
                    dir_path=new_subfolder_path,
                    message=f"in loop {i}",
                    event_type=UpdatedDirFSInputEvent
                )

                shutil.rmtree(post_move_dir_path)
                await self.process_dir_event_queue_response(
                    output_queue=output_queue,
                    dir_path=post_move_dir_path,
                    message=f"in loop {i}",
                    event_type=DeletedDirFSInputEvent
                )
                await self.process_dir_event_queue_response(
                    output_queue=output_queue,
                    dir_path=new_subfolder_path,
                    message=f"in loop {i}",
                    event_type=UpdatedDirFSInputEvent
                )

            await self.cancel_task(run_task)
