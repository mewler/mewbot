# Aim is to run, in sections, as many of the input methods as possible
# Including running a full bot with logging triggers and actions.
# However, individual components also have to be isolated for testing purposes.

import asyncio
import os
import shutil
import sys
import tempfile

import pytest

from .utils import FileSystemTestUtilsDirEvents, FileSystemTestUtilsFileEvents

# pylint: disable=invalid-name
# for clarity, test functions should be named after the things they test
# which means CamelCase in function names


class TestDirTypeFSInput(FileSystemTestUtilsDirEvents, FileSystemTestUtilsFileEvents):
    @pytest.mark.asyncio
    @pytest.mark.skipif(not sys.platform.startswith("win"), reason="Windows only test")
    async def testDirTypeFSInput_existing_dir_cre_upd_del_file_loop_windows(self) -> None:
        """
        Check for expected created signal from a file which is created in a monitored dir
        Followed by an attempt to update the file.
        Then an attempt to delete the file.
        This is done in a loop - to check for any problems with stale events
        """
        with tempfile.TemporaryDirectory() as tmp_dir_path:
            run_task, output_queue = await self.get_DirTypeFSInput(tmp_dir_path)

            for i in range(10):
                # - Using blocking methods - this should still work
                new_file_path = os.path.join(tmp_dir_path, "text_file_delete_me.txt")

                with open(new_file_path, "w", encoding="utf-16") as output_file:
                    output_file.write("Here we go")
                await self.process_file_creation_queue_response(
                    output_queue, file_path=new_file_path, message=f"in loop {i}"
                )

                with open(new_file_path, "a", encoding="utf-16") as output_file:
                    output_file.write("Here we go again")
                await self.process_dir_update_queue_response(
                    output_queue, dir_path=tmp_dir_path, allowed_queue_size=1
                )
                await self.process_file_update_queue_response(
                    output_queue, file_path=new_file_path
                )

                os.unlink(new_file_path)
                await self.process_dir_update_queue_response(
                    output_queue, dir_path=tmp_dir_path, allowed_queue_size=1
                )
                # Probably do not want
                await self.process_file_deletion_queue_response(
                    output_queue, file_path=new_file_path
                )

            await self.cancel_task(run_task)

    @pytest.mark.asyncio
    @pytest.mark.skipif(not sys.platform.startswith("win"), reason="Windows only test")
    async def testDirTypeFSInput_existing_dir_create_update_move_file_windows(self) -> None:
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
            await self.process_file_creation_queue_response(
                output_queue, file_path=new_file_path
            )

            with open(new_file_path, "a", encoding="utf-16") as output_file:
                output_file.write("Here we go again")
            await self.process_dir_update_queue_response(
                output_queue, dir_path=tmp_dir_path, allowed_queue_size=1
            )
            await self.process_file_update_queue_response(
                output_queue, file_path=new_file_path
            )

            # Move a file to a different location
            post_move_file_path = os.path.join(tmp_dir_path, "moved_text_file_delete_me.txt")
            os.rename(src=new_file_path, dst=post_move_file_path)

            await self.process_dir_update_queue_response(
                output_queue, dir_path=tmp_dir_path, allowed_queue_size=1
            )
            # No good way to tell if the file was deleted or moved - on windows
            await self.process_file_deletion_queue_response(
                output_queue, file_path=new_file_path
            )
            await self.process_file_move_queue_response(
                output_queue,
                file_src_parth=new_file_path,
                file_dst_path=post_move_file_path,
            )

            await self.cancel_task(run_task)

    @pytest.mark.asyncio
    @pytest.mark.skipif(not sys.platform.startswith("win"), reason="Windows only test")
    async def testDirTypeFSInput_existing_dir_create_update_move_file_loop_windows(
        self,
    ) -> None:
        """
        Check for the expected created signal from a file which is created in a monitored dir
        Followed by an attempt to update the file.
        """
        with tempfile.TemporaryDirectory() as tmp_dir_path:
            run_task, output_queue = await self.get_DirTypeFSInput(tmp_dir_path)

            for i in range(7):

                # - Using blocking methods - this should still work
                new_file_path = os.path.join(tmp_dir_path, "text_file_delete_me.txt")

                with open(new_file_path, "w", encoding="utf-16") as output_file:
                    output_file.write("Here we go")
                if i == 0:
                    await self.process_file_creation_queue_response(
                        output_queue, file_path=new_file_path, message=f"in loop {i}"
                    )
                else:
                    await self.process_file_creation_queue_response(
                        output_queue, file_path=new_file_path, message=f"in loop {i}"
                    )

                with open(new_file_path, "a", encoding="utf-16") as output_file:
                    output_file.write("Here we go again")
                await self.process_dir_update_queue_response(
                    output_queue,
                    dir_path=tmp_dir_path,
                    allowed_queue_size=1,
                )
                await self.process_file_update_queue_response(
                    output_queue, file_path=new_file_path
                )

                # Move a file to a different location
                post_move_file_path = os.path.join(
                    tmp_dir_path, "moved_text_windows_file_delete_me.txt"
                )
                os.rename(src=new_file_path, dst=post_move_file_path)

                await self.process_dir_update_queue_response(
                    output_queue,
                    dir_path=tmp_dir_path,
                    message=f"in loop {i}",
                    allowed_queue_size=1,
                )
                await self.process_file_deletion_queue_response(
                    output_queue, file_path=new_file_path, message=f"in loop {i}"
                )  # This looks like some kind of artifact of the normalisation
                await self.process_file_move_queue_response(
                    output_queue,
                    file_src_parth=new_file_path,
                    file_dst_path=post_move_file_path,
                )

                os.unlink(post_move_file_path)
                await self.process_dir_update_queue_response(
                    output_queue,
                    dir_path=tmp_dir_path,
                    message=f"in loop {i}",
                    allowed_queue_size=1,
                )
                await self.process_file_deletion_queue_response(
                    output_queue, file_path=post_move_file_path, message=f"in loop {i}"
                )

            await self.cancel_task(run_task)

    @pytest.mark.asyncio
    @pytest.mark.skipif(not sys.platform.startswith("win"), reason="Windows only test")
    async def testDirTypeFSInput_existing_dir_create_update_move_file_in_subfolder_loop_windows(
        self,
    ) -> None:
        """
        Check for the expected created signal from a file which is created in a monitored dir
        In a subfolder of that monitored dir.
        Followed by an attempt to update the file.
        Followed by an attempt to move the file.
        This one has been particularly hard to test
        """
        with tempfile.TemporaryDirectory() as tmp_dir_path:

            new_subfolder_path = os.path.join(tmp_dir_path, "subfolder_1", "subfolder_2")
            os.makedirs(new_subfolder_path)

            run_task, output_queue = await self.get_DirTypeFSInput(tmp_dir_path)

            for i in range(10):

                while True:
                    try:
                        output_queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break

                # - Using blocking methods - this should still work
                new_file_path = os.path.join(new_subfolder_path, "text_file_delete_me.txt")

                with open(new_file_path, "w", encoding="utf-16") as output_file:
                    output_file.write("Here we go")

                await asyncio.sleep(0.5)

                # As with all cases where I've had to do this, it seems to vary randomly between
                # runs - Perhaps use this input with care
                self.check_queue_for_file_creation_input_event(
                    output_queue=output_queue, file_path=new_file_path, message=f"in loop {i}"
                )

                with open(new_file_path, "a", encoding="utf-16") as output_file:
                    output_file.write(f"Here we go again - and some more {i}")

                await asyncio.sleep(1.5)

                update_queue_list = self.dump_queue_to_list(output_queue)

                # The fact that not upate event is produced is mildly worrying
                self.check_queue_for_dir_update_input_event(
                    output_queue=update_queue_list,
                    dir_path=new_subfolder_path,
                    message=f"in loop {i}",
                )

                # Move a file to a different location
                post_move_file_path = os.path.join(
                    new_subfolder_path, "moved_text_file_delete_me.txt"
                )
                os.rename(src=new_file_path, dst=post_move_file_path)

                await asyncio.sleep(0.5)

                update_queue_list = self.dump_queue_to_list(output_queue)

                self.check_queue_for_file_move_input_event(
                    update_queue_list,
                    file_src_parth=new_file_path,
                    file_dst_path=post_move_file_path,
                    message=f"in loop {i}",
                )
                self.check_queue_for_dir_update_input_event(
                    output_queue=update_queue_list,
                    dir_path=new_subfolder_path,
                    message=f"in loop {i}",
                )

                os.unlink(post_move_file_path)

                await asyncio.sleep(0.5)

                queue_length = output_queue.qsize()

                if queue_length == 3:

                    await self.process_dir_update_queue_response(
                        output_queue,
                        dir_path=new_subfolder_path,
                        message=f"in loop {i}",
                        allowed_queue_size=1,
                    )
                    await self.process_dir_update_queue_response(
                        output_queue,
                        dir_path=new_subfolder_path,
                        message=f"in loop {i}",
                        allowed_queue_size=1,
                    )
                    await self.process_file_deletion_queue_response(
                        output_queue, file_path=post_move_file_path, message=f"in loop {i}"
                    )

                elif queue_length == 2:

                    await self.process_dir_update_queue_response(
                        output_queue,
                        dir_path=new_subfolder_path,
                        message=f"in loop {i}",
                        allowed_queue_size=1,
                    )
                    await self.process_file_deletion_queue_response(
                        output_queue, file_path=post_move_file_path, message=f"in loop {i}"
                    )

                else:

                    raise NotImplementedError(f"Unexpected queue_length - {queue_length}")

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
            await self.process_dir_creation_queue_response(
                output_queue, dir_path=new_dir_path
            )

            shutil.rmtree(new_dir_path)
            await self.process_dir_update_queue_response(
                output_queue, dir_path=tmp_dir_path, allowed_queue_size=1
            )
            await self.process_dir_deletion_queue_response(
                output_queue, dir_path=new_dir_path
            )

            await self.cancel_task(run_task)

    @pytest.mark.asyncio
    @pytest.mark.skipif(not sys.platform.startswith("win"), reason="Windows only test")
    async def testDirTypeFSInput_existing_dir_cre_del_dir_loop_windows(self) -> None:
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
                    await self.process_dir_creation_queue_response(
                        output_queue, dir_path=new_dir_path, message=f"in loop {i}"
                    )
                else:
                    await self.process_dir_creation_queue_response(
                        output_queue, dir_path=new_dir_path, message=f"in loop {i}"
                    )

                shutil.rmtree(new_dir_path)

                await asyncio.sleep(0.5)

                queue_length: int = output_queue.qsize()

                if queue_length == 1:

                    await self.process_dir_deletion_queue_response(
                        output_queue, dir_path=new_dir_path, message=f"in loop {i}"
                    )

                elif queue_length == 2:

                    await self.process_dir_update_queue_response(
                        output_queue,
                        dir_path=tmp_dir_path,
                        message=f"in loop {i}",
                        allowed_queue_size=1,
                    )
                    await self.process_dir_deletion_queue_response(
                        output_queue, dir_path=new_dir_path, message=f"in loop {i}"
                    )

                elif queue_length == 0:
                    pass

                else:

                    raise NotImplementedError(f"Unexpected queue size {queue_length}")

            await self.cancel_task(run_task)

    @pytest.mark.asyncio
    @pytest.mark.skipif(not sys.platform.startswith("win"), reason="Windows only test")
    async def testDirTypeFSInput_existing_dir_create_move_dir_windows(self) -> None:
        """
        Checks we get the expected created signal from a dir which is created in a monitored dir
        Followed by moving the dir.
        """

        with tempfile.TemporaryDirectory() as tmp_dir_path:
            run_task, output_queue = await self.get_DirTypeFSInput(tmp_dir_path)

            # - Using blocking methods - this should still work
            new_dir_path = os.path.join(tmp_dir_path, "text_windows_file_delete_me.txt")

            os.mkdir(new_dir_path)
            await self.process_dir_creation_queue_response(
                output_queue, dir_path=new_dir_path
            )

            # Move a file to a different location
            post_move_dir_path = os.path.join(
                tmp_dir_path, "moved_text_windows_file_delete_me.txt"
            )
            os.rename(src=new_dir_path, dst=post_move_dir_path)

            # This is an asymmetry between how files and folders handle delete
            # left in while I try and think how to deal sanely with it
            # await self.process_dir_deletion_response(output_queue, dir_path=new_dir_path)
            # await self.process_dir_update_response(output_queue, dir_path=tmp_dir_path)
            await self.process_dir_move_queue_response(
                output_queue, dir_src_parth=new_dir_path, dir_dst_path=post_move_dir_path
            )

            await self.cancel_task(run_task)

    @pytest.mark.asyncio
    @pytest.mark.skipif(not sys.platform.startswith("win"), reason="Windows only test")
    async def testDirTypeFSInput_existing_dir_create_move_dir_loop_in_subbir_windows(
        self,
    ) -> None:
        """
        Checks we get the expected created signal from a dir which is created in a monitored dir
        Followed by moving the dir.
        Repeated in a loop.
        """
        with tempfile.TemporaryDirectory() as tmp_dir_path:

            new_subfolder_path = os.path.join(
                tmp_dir_path, "subfolder_1", "subfolder_2", "subfolder_3"
            )
            os.makedirs(new_subfolder_path)

            run_task, output_queue = await self.get_DirTypeFSInput(tmp_dir_path)

            for i in range(10):

                # - Using blocking methods - this should still work
                new_dir_path = os.path.join(new_subfolder_path, "text_file_delete_me.txt")

                os.mkdir(new_dir_path)
                if i == 0:
                    await self.process_dir_creation_queue_response(
                        output_queue, dir_path=new_dir_path, message=f"in loop {i}"
                    )
                else:

                    await self.process_dir_creation_queue_response(
                        output_queue, dir_path=new_dir_path, message=f"in loop {i}"
                    )

                # Move a file to a different location
                post_move_dir_path = os.path.join(
                    new_subfolder_path, "moved_text_file_delete_me.txt"
                )
                os.rename(src=new_dir_path, dst=post_move_dir_path)

                # I think this is a Windows problem - probably.
                if i == 0:
                    await self.process_dir_update_queue_response(output_queue)
                    await self.process_dir_move_queue_response(
                        output_queue,
                        dir_src_parth=new_dir_path,
                        dir_dst_path=post_move_dir_path,
                        message=f"in loop {i}",
                    )
                else:
                    await self.process_dir_update_queue_response(output_queue)
                    await self.process_dir_move_queue_response(
                        output_queue,
                        dir_src_parth=new_dir_path,
                        dir_dst_path=post_move_dir_path,
                        message=f"in loop {i}",
                    )

                shutil.rmtree(post_move_dir_path)
                await self.process_dir_update_queue_response(
                    output_queue,
                    dir_path=new_subfolder_path,
                    message=f"in loop {i}",
                    allowed_queue_size=1,
                )
                await self.process_dir_update_queue_response(
                    output_queue,
                    dir_path=tmp_dir_path,
                    message=f"in loop {i}",
                    allowed_queue_size=1,
                )
                await self.process_dir_deletion_queue_response(
                    output_queue, dir_path=post_move_dir_path, message=f"in loop {i}"
                )

            await self.cancel_task(run_task)

    @pytest.mark.asyncio
    @pytest.mark.skipif(not sys.platform.startswith("win"), reason="Windows only test")
    async def testDirTypeFSInput_existing_dir_create_move_dir_loop_windows(self) -> None:
        """
        Checks we get the expected created signal from a dir which is created in a monitored dir
        Followed by moving the dir.
        Repeated in a loop.
        """
        with tempfile.TemporaryDirectory() as tmp_dir_path:
            run_task, output_queue = await self.get_DirTypeFSInput(tmp_dir_path)

            for i in range(10):

                # - Using blocking methods - this should still work
                new_dir_path = os.path.join(tmp_dir_path, "text_file_delete_me.txt")

                os.mkdir(new_dir_path)
                if i == 0:
                    await self.process_dir_creation_queue_response(
                        output_queue, dir_path=new_dir_path, message=f"in loop {i}"
                    )
                else:

                    await self.process_dir_creation_queue_response(
                        output_queue, dir_path=new_dir_path, message=f"in loop {i}"
                    )

                # Move a file to a different location
                post_move_dir_path = os.path.join(
                    tmp_dir_path, "moved_text_file_delete_me.txt"
                )
                os.rename(src=new_dir_path, dst=post_move_dir_path)

                # I think this is a Windows problem - probably.
                if i == 0:
                    await self.process_dir_move_queue_response(
                        output_queue,
                        dir_src_parth=new_dir_path,
                        dir_dst_path=post_move_dir_path,
                        message=f"in loop {i}",
                    )
                else:

                    await self.process_dir_move_queue_response(
                        output_queue,
                        dir_src_parth=new_dir_path,
                        dir_dst_path=post_move_dir_path,
                        message=f"in loop {i}",
                    )

                shutil.rmtree(post_move_dir_path)
                await self.process_dir_update_queue_response(
                    output_queue,
                    dir_path=tmp_dir_path,
                    message=f"in loop {i}",
                    allowed_queue_size=1,
                )
                await self.process_dir_deletion_queue_response(
                    output_queue, dir_path=post_move_dir_path, message=f"in loop {i}"
                )

            await self.cancel_task(run_task)
