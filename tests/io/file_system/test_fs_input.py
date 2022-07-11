# Aim is to run, in sections, as many of the input methods as possible
# Including running a full bot with logging triggers and actions.
# However, individual components also have to be isolated for testing purposes.

# import asyncio
# import tempfile
# import os
#
# import pytest
#
# from mewbot.api.v1 import InputEvent
# from mewbot.io.file_system import (
#     FileTypeFSInput,
#     CreatedFileFSInputEvent,
#     DeletedFileFSInputEvent,
# )

# pylint: disable=invalid-name
# test functions should be named after the things they test


class TestFileTypeFSInput:

    ...

    # @pytest.mark.asyncio
    # async def test_FileTypeFSInput_run_without_error_existing_dir(self) -> None:
    #     """
    #     Tests that the run method of the input class does not throw an error.
    #     Testing on a dir which actually exists
    #     """
    #     with tempfile.TemporaryDirectory() as tmp_dir_path:
    #         test_fs_input = FileTypeFSInput(input_path=tmp_dir_path)
    #         assert isinstance(test_fs_input, FileTypeFSInput)
    #
    #         # We need to retain control of the thread to shutdown
    #         asyncio.get_running_loop().create_task(test_fs_input.run())
    #
    #         await asyncio.sleep(0.5)
    #         # Note - manually stopping the loop seems to lead to a rather nasty cash

    # @pytest.mark.asyncio
    # async def test_FileTypeFSInput_existing_dir_io_in_existing_dir(self) -> None:
    #     """
    #     Tests that the run method of the input class does not throw an error.
    #     Testing on a dir which actually exists
    #     """
    #     with tempfile.TemporaryDirectory() as tmp_dir_path:
    #         test_fs_input = FileTypeFSInput(input_path=tmp_dir_path)
    #         assert isinstance(test_fs_input, FileTypeFSInput)
    #
    #         output_queue: asyncio.Queue[InputEvent] = asyncio.Queue()
    #         test_fs_input.queue = output_queue
    #
    #         # We need to retain control of the thread to delay shutdown
    #         # And to probe the results
    #         asyncio.get_running_loop().create_task(test_fs_input.run())
    #
    #         # Give the class a chance to actually do init
    #         await asyncio.sleep(0.5)
    #
    #         # Generate some events which should end up in the queue
    #         # - Using blocking methods - this should still work
    #         new_file_path = os.path.join(tmp_dir_path, "text_file_delete_me.txt")
    #
    #         with open(new_file_path, "w", encoding="utf-16") as output_file:
    #             output_file.write("Here we go")
    #
    #         # This should have generated an event
    #         queue_out = await output_queue.get()
    #         assert isinstance(queue_out, CreatedFileFSInputEvent)
    #
    #         # There should be no other events in the queue
    #         output_queue_qsize = output_queue.qsize()
    #         assert (
    #             output_queue_qsize == 0
    #         ), f"Output queue actually has {output_queue_qsize} entries"
    #
    # @pytest.mark.asyncio
    # async def test_FileTypeFSInput_existing_file_then_deleted_then_recreated(self) -> None:
    #     """
    #     Start with an existing file - which will be monitored.
    #     Delete that file (should prompt a deletion event)
    #     Then recreate the file (should prompt an added event)
    #     Then append to that file (should prompt a changed event)
    #     """
    #     with tempfile.TemporaryDirectory() as tmp_dir_path:
    #
    #         # Start with an existing file
    #         new_file_path = os.path.join(tmp_dir_path, "text_file_delete_me.txt")
    #
    #         with open(new_file_path, "w", encoding="utf-16") as output_file:
    #             output_file.write("Here we go")
    #
    #         test_fs_input = FileTypeFSInput(input_path=tmp_dir_path)
    #         assert isinstance(test_fs_input, FileTypeFSInput)
    #
    #         output_queue: asyncio.Queue[InputEvent] = asyncio.Queue()
    #         test_fs_input.queue = output_queue
    #
    #         # We need to retain control of the thread to delay shutdown
    #         # And to probe the results
    #         asyncio.get_running_loop().create_task(test_fs_input.run())
    #
    #         # Give the class a chance to actually do init
    #         await asyncio.sleep(0.5)
    #
    #         # Delete the existing file
    #         os.unlink(new_file_path)
    #
    #         # This should have generated an event
    #         queue_out = await output_queue.get()
    #         assert isinstance(queue_out, DeletedFileFSInputEvent)
    #
    #         # There should be no other events in the queue
    #         output_queue_qsize = output_queue.qsize()
    #         assert (
    #             output_queue_qsize == 0
    #         ), f"Output queue actually has {output_queue_qsize} entries"
    #
    #         # Generate some events which should end up in the queue
    #         # - Using blocking methods - this should still work
    #         new_file_path = os.path.join(tmp_dir_path, "text_file_delete_me.txt")
    #
    #         with open(new_file_path, "w", encoding="utf-16") as output_file:
    #             output_file.write("Here we go")
    #
    #         # This should have generated an event
    #         queue_out = await output_queue.get()
    #         assert isinstance(queue_out, CreatedFileFSInputEvent)
    #
    #         # There should be no other events in the queue
    #         output_queue_qsize = output_queue.qsize()
    #         assert (
    #             output_queue_qsize == 0
    #         ), f"Output queue actually has {output_queue_qsize} entries"

    # @pytest.mark.asyncio
    # async def test_FileTypeFSInput_dir_created_after_run(self) -> None:
    #     """
    #     The underlying library has some problems when the target resource starts off not existing.
    #     Try and probe this by creating a file to monitor after run is called.
    #     """
    #     # Start off with a file path which does not exist
    #     # run the input method
    #     # then create the file and check that a file_creation even occurs as expected
    #     with tempfile.TemporaryDirectory() as tmp_dir_path:
    #
    #         new_file_path = os.path.join(tmp_dir_path, "text_file_delete_me.txt")
    #
    #         test_fs_input = FileTypeFSInput(input_path=new_file_path)
    #         assert isinstance(test_fs_input, FileTypeFSInput)
    #
    #         output_queue: asyncio.Queue[InputEvent] = asyncio.Queue()
    #         test_fs_input.queue = output_queue
    #
    #         # We need to retain control of the thread to delay shutdown
    #         # And to probe the results
    #         asyncio.get_running_loop().create_task(test_fs_input.run())
    #
    #         # Give the class a chance to actually do init
    #         await asyncio.sleep(0.5)
    #
    #         # Bring the file into existence - if all has gone well, now it should be monitored
    #         with open(new_file_path, "w", encoding="utf-16") as output_file:
    #             output_file.write("Here we go")
    #
    #         # This should have generated an event
    #         queue_out = await output_queue.get()
    #         assert isinstance(queue_out, CreatedFileFSInputEvent)
    #
    #         # There should be no other events in the queue
    #         output_queue_qsize = output_queue.qsize()
    #         assert (
    #             output_queue_qsize == 0
    #         ), f"Output queue actually has {output_queue_qsize} entries"
