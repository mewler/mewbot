from typing import Optional

import asyncio

from mewbot.api.v1 import InputEvent
from mewbot.io.file_system import (
    InputFileFileCreationInputEvent,
    InputFileDirCreationInputEvent,
    InputFileFileDeletionInputEvent,
    CreatedFileFSInputEvent,
    UpdatedFileFSInputEvent,
    MovedFileFSInputEvent,
    DeletedFileFSInputEvent,
    CreatedDirFSInputEvent,
    MovedDirFSInputEvent,
    UpdatedDirFSInputEvent,
    DeletedDirFSInputEvent,
)


class FileSystemTestUtils:
    async def process_file_creation_response(
        self,
        output_queue: asyncio.Queue[InputEvent],
        file_path: Optional[str] = None,
        allow_update_events_in_queue_after: bool = False,
        message: str = ""
    ) -> None:
        """
        Get the next event off the queue.
        Check that it's one for a file being created with expected file path.
        """

        # This should have generated an event
        queue_out = await output_queue.get()
        assert isinstance(
            queue_out, CreatedFileFSInputEvent
        ), f"Expected CreatedFileFSInputEvent - got {queue_out}" + f" - {message}" if message else ""

        if file_path is not None:
            assert queue_out.file_path == file_path

        if not allow_update_events_in_queue_after:
            await self.verify_queue_is_empty(output_queue)
        else:
            # Exhaust the queue, checking all events are Update ones
            # Due to some hacks to deal with how windows handles file events
            await asyncio.sleep(1.0)
            while True:
                try:
                    queue_out = output_queue.get_nowait()
                except asyncio.queues.QueueEmpty:
                    return

                assert isinstance(
                    queue_out, UpdatedFileFSInputEvent
                ), f"Expected UpdatedFileFSInputEvent - got {queue_out}"

    async def process_file_update_response(
        self, output_queue: asyncio.Queue[InputEvent], file_path: Optional[str] = None, message: str = ""
    ) -> None:
        """
        Get the next event off the queue - check that it's one for the input file being deleted.
        """
        # This should have generated an event
        queue_out = await output_queue.get()
        assert isinstance(
            queue_out, UpdatedFileFSInputEvent
        ), f"Expected UpdatedFileFSInputEvent - got {queue_out}" + f" - {message}" if message else ""

        if file_path is not None:
            assert file_path == queue_out.file_path

        await self.verify_queue_is_empty(output_queue)

    async def process_file_move_response(
        self,
        output_queue: asyncio.Queue[InputEvent],
        file_src_parth: Optional[str] = None,
        file_dst_path: Optional[str] = None,
    ) -> None:
        """
        Get the next event off the queue - check that it's one for the input file being deleted.
        """
        # This should have generated an event
        queue_out = await output_queue.get()
        assert isinstance(
            queue_out, MovedFileFSInputEvent
        ), f"Expected MovedFileFSInputEvent - got {queue_out}"

        if file_src_parth is not None:
            assert queue_out.file_src == file_src_parth

        if file_dst_path is not None:
            assert queue_out.file_path == file_dst_path

        await self.verify_queue_is_empty(output_queue)

    async def process_file_deletion_response(
        self, output_queue: asyncio.Queue[InputEvent], file_path: Optional[str] = None, message: str = ""
    ) -> None:
        """
        Get the next event off the queue - check that it's one for the input file being deleted.
        """
        queue_out = await output_queue.get()

        if file_path is not None:
            assert isinstance(
                queue_out, DeletedFileFSInputEvent
            ), f"expected DeletedFileFSInputEvent - got {queue_out}" + f" - {message}" if message else ""
            assert file_path == queue_out.file_path

        # At this point the queue should be empty.
        await self.verify_queue_is_empty(output_queue)

        # This should have generated an event - which we just took off the queue
        assert isinstance(
            queue_out, DeletedFileFSInputEvent
        ), f"expected DeletedFileFSInputEvent - got {queue_out}"

    async def process_dir_creation_response(
        self, output_queue: asyncio.Queue[InputEvent], dir_path: Optional[str] = None
    ) -> None:
        """
        Get the next event off the queue - check that it's one for a file being created in the
        input dir.
        """

        # This should have generated an event
        queue_out = await output_queue.get()
        assert isinstance(
            queue_out, CreatedDirFSInputEvent
        ), f"Expected CreatedDirFSInputEvent - got {queue_out}"
        if dir_path is not None:
            assert queue_out.dir_path == dir_path

        await self.verify_queue_is_empty(output_queue)

    async def process_dir_update_response(
        self, output_queue: asyncio.Queue[InputEvent], dir_path: Optional[str] = None, message: str = ""
    ) -> None:
        """
        Get the next event off the queue - check that it's one for a file being created in the
        input dir.
        """

        # This should have generated an event
        queue_out = await output_queue.get()
        assert isinstance(
            queue_out, UpdatedDirFSInputEvent
        ), f"Expected UpdatedDirFSInputEvent - got {queue_out}" + f" - {message}" if message else ""
        if dir_path is not None:
            assert queue_out.dir_path == dir_path

        await self.verify_queue_is_empty(output_queue)

    async def process_input_file_creation_response(
        self, output_queue: asyncio.Queue[InputEvent]
    ) -> None:
        """
        This event is emitted when we're in file mode, monitoring a file, which does not yet exist.
        When the file is created, this event is emitted.
        """

        # This should have generated an event
        queue_out = await output_queue.get()
        assert isinstance(queue_out, InputFileFileCreationInputEvent)

        await self.verify_queue_is_empty(output_queue)

    async def process_input_dir_creation_response(
        self, output_queue: asyncio.Queue[InputEvent]
    ) -> None:
        """
        This event is emitted when we're in dir mode, monitoring a dir, which does not yet exist.
        When the dir is created, this event is emitted.
        """

        # This should have generated an event
        queue_out = await output_queue.get()
        assert isinstance(
            queue_out, InputFileDirCreationInputEvent
        ), f"Expected InputFileDirCreationInputEvent - got {queue_out}"

        await self.verify_queue_is_empty(output_queue)

    async def process_dir_move_response(
        self,
        output_queue: asyncio.Queue[InputEvent],
        dir_src_parth: Optional[str] = None,
        dir_dst_path: Optional[str] = None,
    ) -> None:
        """
        Get the next event off the queue - check that it's one for the input file being deleted.
        """
        # This should have generated an event
        queue_out = await output_queue.get()
        assert isinstance(
            queue_out, MovedDirFSInputEvent
        ), f"Expected MovedFileFSInputEvent - got {queue_out}"

        if dir_src_parth is not None:
            assert queue_out.dir_path == dir_src_parth

        if dir_dst_path is not None:
            assert queue_out.dir_src_path == dir_dst_path

        await self.verify_queue_is_empty(output_queue)

    async def process_dir_deletion_response(
        self, output_queue: asyncio.Queue[InputEvent], dir_path: Optional[str] = None
    ) -> None:
        """
        Get the next event off the queue - check that it's one for a file being created in the
        input dir.
        """

        # This should have generated an event
        queue_out = await output_queue.get()
        assert isinstance(
            queue_out, DeletedDirFSInputEvent
        ), f"Expected DeletedDirFSInputEvent - got {queue_out}"
        if dir_path is not None:
            assert isinstance(
                queue_out, DeletedDirFSInputEvent
            ), f"Expected DeletedDirFSInputEvent - got {queue_out}"
            assert queue_out.dir_path == dir_path

        await self.verify_queue_is_empty(output_queue)

    async def process_input_file_deletion_response(
        self, output_queue: asyncio.Queue[InputEvent]
    ) -> None:
        """
        Get the next event off the queue - check that it's one for the input file being deleted.
        """
        # This should have generated an event
        queue_out = await output_queue.get()
        assert isinstance(queue_out, InputFileFileDeletionInputEvent)

        await self.verify_queue_is_empty(output_queue)

    @staticmethod
    async def verify_queue_is_empty(
        output_queue: asyncio.Queue[InputEvent], task_done: bool = True
    ) -> None:
        # There should be no other events in the queue
        output_queue_qsize = output_queue.qsize()
        assert (
            output_queue_qsize == 0
        ), f"Output queue actually has {output_queue_qsize} entries"

        # Indicate to the queue that task processing is complete
        if task_done:
            output_queue.task_done()

    @staticmethod
    async def cancel_task(run_task: asyncio.Task[None]) -> None:

        # Otherwise the queue seems to be blocking pytest from a clean exit.
        try:
            run_task.cancel()
            await run_task
        except asyncio.exceptions.CancelledError:
            pass
