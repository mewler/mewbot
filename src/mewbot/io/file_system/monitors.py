from __future__ import annotations

import asyncio
import logging
import os

from typing import Set, Optional, Union, Any

import aiopath  # type: ignore
import watchdog  # type: ignore
from watchdog.events import FileSystemEvent, FileSystemEventHandler  # type: ignore
from watchdog.observers import Observer  # type: ignore


from mewbot.core import InputEvent
from mewbot.io.file_system.events import (
    InputFileDirDeletionInputEvent,
    CreatedDirFSInputEvent,
    CreatedFileFSInputEvent,
    FSInputEvent,
    UpdatedFileFSInputEvent,
    DeletedFileFSInputEvent,
    MovedDirFSInputEvent,
    MovedFileFSInputEvent,
    DeletedDirFSInputEvent,
    UpdatedDirFSInputEvent,
)


class WindowsFileSystemObserver:
    """
    Does the job of actually observing the file system.
    Isolated here because the observer subsystem for windows is particularly problematic, and it
    should be swapped out wholesale where possible.
    """

    _watchdog_observer: Observer = Observer()

    # workaround for a problem with file monitors on Windows
    # when a file is deleted you receive several modification events before the delete event.
    # These are meaningless - the file is, in truth, already gone
    # This cache contains file paths which the user has been told have been deleted.
    # And python believes to be gone
    # Removed from the cache when an actual delete event comes in, or a creation/move to event
    _python_registers_deleted_cache: Set[str] = set()
    _python_registers_created_cache: Set[str] = set()

    _output_queue: Optional[asyncio.Queue[InputEvent]]
    _input_path: Optional[str] = None

    _logger: logging.Logger

    _internal_queue: asyncio.Queue[FileSystemEvent]

    _dir_cache: Set[str]

    def __init__(
        self, output_queue: Optional[asyncio.Queue[InputEvent]], input_path: str
    ) -> None:

        self._output_queue = output_queue
        self._input_path = input_path

        self._logger = logging.getLogger(__name__ + ":" + type(self).__name__)

        self._internal_queue = asyncio.Queue()
        self._dir_cache = set()
        self.build_dir_cache()

    def build_dir_cache(self) -> None:
        """
        On Windows DIR deletion events are being reported as FILE del events.
        There is no good way to check the status of an object after it's gone,
        thus need to cache all the dirs first.
        """
        if self._input_path is None:
            return

        self._logger.info("Building dir cache for %s", self._input_path)
        for root, dirs, _ in os.walk(top=self._input_path):
            self._dir_cache.update(set(os.path.join(root, dn) for dn in dirs))
        self._logger.info(
            "dir cache built for %s - %i dirs found", self._input_path, len(self._dir_cache)
        )

    async def monitor_dir_watcher(self) -> bool:

        if self._input_path is not None:

            self.watch()
        else:
            self._logger.warning("self._input_path is None in run - this should not happen")
            raise NotImplementedError(
                "self._input_path is None in run - this should not happen"
            )

        dir_deleted = await self._process_queue()
        if dir_deleted:
            self._logger.info(
                "%s has been deleted - returning to wait mode", self._input_path
            )
            await self.send(
                InputFileDirDeletionInputEvent(
                    dir_path=self._input_path,
                    dir_async_path=aiopath.AsyncPath(self._input_path),
                    base_event=None,
                )
            )
            return False
        return True

    async def _process_queue(self) -> bool:
        """
        Take event off the internal queue, process them, and then put them on the wire.
        """
        target_async_path: aiopath.AsyncPath = aiopath.AsyncPath(self._input_path)

        while True:

            new_event = await self._internal_queue.get()

            # The events produced when the dir is deleted are not helpful
            # Currently not sure that watchdog elegantly indicates that it's had its target dir
            # deleted
            # So need this horrible hack. Will get the rest of it working, then optimize

            # No helpful info is provided by the watcher if the target dir itself is deleted
            # So need to check before each event

            target_exists: bool = await target_async_path.exists()

            if not target_exists:
                self._logger.info("Delete event detected - %s is gone", self._input_path)
                return True

            await self._process_event(new_event)

    async def _input_path_created_task(self, target_async_path: aiopath.AsyncPath) -> None:
        """
        Called when _monitor_file detects that there's now something at the input_path location.
        Spun off into a separate method because want to get into starting the watch as fast as
        possible.
        """
        if self._input_path is None:
            self._logger.warning(
                "Unexpected call to _input_path_created_task - _input_path is None!"
            )
            return

        str_path: str = self._input_path

        if await target_async_path.is_dir():

            self._logger.info('New asset at "%s" detected as dir', self._input_path)

            await self.send(
                CreatedDirFSInputEvent(
                    dir_path=str_path, dir_async_path=target_async_path, base_event=None
                )
            )

        elif await target_async_path.is_file():

            self._logger.info('New asset at "%s" detected as file', self._input_path)

            await self.send(
                CreatedFileFSInputEvent(
                    file_path=str_path, file_async_path=target_async_path, base_event=None
                )
            )

        else:
            self._logger.warning(
                "Unexpected case in _input_path_created_task - %s", target_async_path
            )

    async def send(self, event: FSInputEvent) -> None:

        if self._output_queue is None:
            return

        await self._output_queue.put(event)

    async def _process_event(self, event: FileSystemEvent) -> None:
        """
        Take an event and process it before putting it on the wire.
        """
        # Filter null events
        if event is None:
            return

        if isinstance(
            event,
            (
                watchdog.events.FileCreatedEvent,
                watchdog.events.FileModifiedEvent,
                watchdog.events.FileMovedEvent,
                watchdog.events.FileSystemMovedEvent,
                watchdog.events.FileDeletedEvent,
            ),
        ):
            await self._process_file_event(event)
        elif isinstance(
            event,
            (
                watchdog.events.DirCreatedEvent,
                watchdog.events.DirModifiedEvent,
                watchdog.events.DirMovedEvent,
                watchdog.events.DirDeletedEvent,
            ),
        ):
            await self._process_dir_event(event)
        else:
            self._logger.info("Unhandled event in _process_event - %s", event)

    async def _process_file_event(self, event: FileSystemEvent) -> None:
        """
        Take an event and process it before putting it on the wire.
        """

        if isinstance(event, watchdog.events.FileCreatedEvent):

            await self._process_file_creation_event(event)

        elif isinstance(event, watchdog.events.FileModifiedEvent):

            await self._process_file_modified_event(event)

        elif isinstance(
            event, (watchdog.events.FileMovedEvent, watchdog.events.FileSystemMovedEvent)
        ):

            await self._process_file_move_event(event)

        elif isinstance(event, watchdog.events.FileDeletedEvent):

            await self._process_file_delete_event(event)

        else:
            self._logger.warning("Unexpected case in _process_file_event - %s", event)

    async def _process_file_creation_event(
        self, event: watchdog.events.FileCreatedEvent
    ) -> None:

        file_async_path = aiopath.AsyncPath(event.src_path)

        if not await file_async_path.exists():
            # zombie event - appeal to reality says the file does not exist
            return

        if event.src_path in self._python_registers_created_cache:
            # User has already been notified - no reason to tell them again
            return

        # After one of these there very much should be something at the target loc
        self._python_registers_deleted_cache.discard(event.src_path)
        self._python_registers_created_cache.add(event.src_path)

        await self.send(
            CreatedFileFSInputEvent(
                file_path=event.src_path,
                file_async_path=aiopath.AsyncPath(event.src_path),
                base_event=event,
            )
        )

    async def _process_file_modified_event(
        self, event: watchdog.events.FileModifiedEvent
    ) -> None:

        file_async_path = aiopath.AsyncPath(event.src_path)

        if await file_async_path.exists():
            # This might be a legit event

            if event.src_path in self._python_registers_deleted_cache:
                # We're getting modification events - and the file exists
                # where once it was registered as deleted
                # So tell the user the file exists again
                self._python_registers_deleted_cache.discard(event.src_path)
                self._python_registers_created_cache.add(event.src_path)

                await self.send(
                    CreatedFileFSInputEvent(
                        file_path=event.src_path,
                        file_async_path=file_async_path,
                        base_event=event,
                    )
                )

                return

            # Inotify on linux also notifies you of a change to the folder in this case
            await self.send(
                UpdatedDirFSInputEvent(
                    dir_path=self._input_path,
                    dir_async_path=aiopath.AsyncPath(self._input_path),
                    base_event=None,
                )
            )

            await self.send(
                UpdatedFileFSInputEvent(
                    file_path=event.src_path,
                    file_async_path=file_async_path,
                    base_event=event,
                )
            )

        else:

            if event.src_path in self._python_registers_deleted_cache:
                # User has already been informed - no need to do anything
                # Any modification events we get here are stale
                return

            # User might think the file still exists - tell them it does not

            # Note that the user has been informed the file is gone
            self._python_registers_deleted_cache.add(event.src_path)
            # The user can be informed again that the file exists
            self._python_registers_created_cache.remove(event.src_path)

            await self.send(
                UpdatedDirFSInputEvent(
                    dir_path=self._input_path,
                    dir_async_path=aiopath.AsyncPath(self._input_path),
                    base_event=None,
                )
            )

            await self.send(
                DeletedFileFSInputEvent(
                    file_path=event.src_path,
                    file_async_path=aiopath.AsyncPath(event.src_path),
                    base_event=event,
                )
            )
            return

    async def _process_file_move_event(
        self,
        event: Union[
            watchdog.events.FileSystemMovedEvent, watchdog.events.FileSystemMovedEvent
        ],
    ) -> None:

        if isinstance(event, watchdog.events.FileSystemMovedEvent):
            self._logger.info("System moved a file %s", str(event))

        # Unfortunately, we're getting these events when a file is moved as well
        if event.src_path in self._dir_cache:

            self._dir_cache.discard(event.src_path)
            self._dir_cache.add(event.dest_path)
            await self.send(
                MovedDirFSInputEvent(
                    dir_path=event.src_path,
                    dir_async_path=aiopath.AsyncPath(event.src_path),
                    dir_src_path=event.dest_path,
                    dir_src_async_path=aiopath.AsyncPath(event.dest_path),
                    base_event=event,
                )
            )
            return

        # Hopefully, from this point on, any modified and deleted events are legit.
        # The user has been effectively told that the src_path no longer exists
        self._python_registers_deleted_cache.add(event.src_path)
        self._python_registers_deleted_cache.discard(event.dest_path)

        # A file hs been moved into position
        # so the user does not need to be informed that one has been created
        # The user has been (effectively) informed that an object has been created here
        self._python_registers_created_cache.add(event.dest_path)
        self._python_registers_created_cache.discard(event.src_path)

        await self.send(
            MovedFileFSInputEvent(
                file_path=event.dest_path,
                file_src=event.src_path,
                file_async_path=aiopath.AsyncPath(event.src_path),
                base_event=event,
            )
        )

    async def _process_file_delete_event(
        self, event: watchdog.events.FileDeletedEvent
    ) -> None:

        file_async_path = aiopath.AsyncPath(event.src_path)

        # Only put a deletion event on the wire if
        # - we haven't done so already
        # - There has been no other events which could be sanely followed by a
        #   delete event
        # - The file does not, in fact, still exist

        if event.src_path in self._python_registers_deleted_cache:

            self._python_registers_deleted_cache.discard(event.src_path)

        elif not await file_async_path.exists():

            print(self._dir_cache)
            # For some reason the watcher is emitting file delete events when a dir is deleted
            if event.src_path in self._dir_cache:

                # Inotify on linux also notifies you of a change to the folder in this case
                await self.send(
                    UpdatedDirFSInputEvent(
                        dir_path=self._input_path,
                        dir_async_path=aiopath.AsyncPath(self._input_path),
                        base_event=None,
                    )
                )

                await self.send(
                    DeletedDirFSInputEvent(
                        dir_path=event.src_path,
                        dir_async_path=aiopath.AsyncPath(event.src_path),
                        base_event=event,
                    )
                )
                return

            # Inotify on linux also notifies you of a change to the folder in this case
            await self.send(
                UpdatedDirFSInputEvent(
                    dir_path=self._input_path,
                    dir_async_path=aiopath.AsyncPath(self._input_path),
                    base_event=None,
                )
            )

            await self.send(
                DeletedFileFSInputEvent(
                    file_path=event.src_path,
                    file_async_path=aiopath.AsyncPath(event.src_path),
                    base_event=event,
                )
            )

        else:

            pass

    async def _process_dir_event(self, event: FileSystemEvent) -> None:
        """
        Take an event and process it before putting it on the wire.
        """

        # DIRS
        if isinstance(event, watchdog.events.DirCreatedEvent):

            # A new directory has been created - record it
            self._dir_cache.add(event.src_path)
            await self.send(
                CreatedDirFSInputEvent(
                    dir_path=event.src_path,
                    dir_async_path=aiopath.AsyncPath(event.src_path),
                    base_event=event,
                )
            )

        elif isinstance(event, watchdog.events.DirModifiedEvent):
            await self.send(
                UpdatedDirFSInputEvent(
                    dir_path=event.src_path,
                    dir_async_path=aiopath.AsyncPath(event.src_path),
                    base_event=event,
                )
            )

        elif isinstance(event, watchdog.events.DirMovedEvent):

            # If a dir experiences a move event, the original dir effectively ceases to exist
            # And a new one appears - update the _dir_cache accordingly
            self._dir_cache.discard(event.src_path)
            self._dir_cache.add(event.dest_path)

            await self.send(
                MovedDirFSInputEvent(
                    dir_src_path=event.src_path,
                    dir_src_async_path=aiopath.AsyncPath(event.src_path),
                    dir_path=event.dest_path,
                    dir_async_path=aiopath.AsyncPath(event.dest_path),
                    base_event=event,
                )
            )

        elif isinstance(event, watchdog.events.DirDeletedEvent):

            # Not that I think you'll ever actually see one of these events
            # Because Windows registers a dir delete event as a file delete for some reason
            self._dir_cache.discard(event.src_path)

            await self.send(
                DeletedDirFSInputEvent(
                    dir_path=event.src_path,
                    dir_async_path=aiopath.AsyncPath(event.src_path),
                    base_event=event,
                )
            )

    def watch(self) -> None:
        """
        Use watchdog in a separate thread to watch a dir for changes.
        """
        handler = _EventHandler(queue=self._internal_queue, loop=asyncio.get_event_loop())

        self._watchdog_observer = Observer()
        self._watchdog_observer.schedule(
            event_handler=handler, path=self._input_path, recursive=True
        )
        self._watchdog_observer.start()

        self._logger.info("Started _watchdog_observer")

        self._watchdog_observer.join(10)

        try:
            asyncio.get_event_loop().call_soon_threadsafe(
                self._internal_queue.put_nowait, None
            )
        except RuntimeError:  # Can happen when the shutdown is not clean
            return


class LinuxFileSystemObserver:
    """
    Does the job of actually observing the file system.
    Isolated here because the observer subsystem for windows is particularly problematic, and it
    should be swapped out wholesale where possible.
    """

    _watchdog_observer: Observer = Observer()

    _output_queue: Optional[asyncio.Queue[InputEvent]]
    _input_path: Optional[str] = None

    _logger: logging.Logger

    _internal_queue: asyncio.Queue[FileSystemEvent]

    def __init__(
        self, output_queue: Optional[asyncio.Queue[InputEvent]], input_path: str
    ) -> None:

        self._output_queue = output_queue
        self._input_path = input_path

        self._logger = logging.getLogger(__name__ + ":" + type(self).__name__)

        self._internal_queue = asyncio.Queue()

    async def monitor_dir_watcher(self) -> bool:

        if self._input_path is not None:

            self.watch()
        else:
            self._logger.warning("self._input_path is None in run - this should not happen")
            raise NotImplementedError(
                "self._input_path is None in run - this should not happen"
            )

        dir_deleted = await self._process_queue()
        if dir_deleted:
            self._logger.info(
                "%s has been deleted - returning to wait mode", self._input_path
            )
            await self.send(
                InputFileDirDeletionInputEvent(
                    dir_path=self._input_path,
                    dir_async_path=aiopath.AsyncPath(self._input_path),
                    base_event=None,
                )
            )
            return False
        return True

    async def _process_queue(self) -> bool:
        """
        Take event off the internal queue, process them, and then put them on the wire.
        """
        target_async_path: aiopath.AsyncPath = aiopath.AsyncPath(self._input_path)

        while True:

            new_event = await self._internal_queue.get()

            # The events produced when the dir is deleted are not helpful
            # Currently not sure that watchdog elegantly indicates that it's had its target dir
            # deleted
            # So need this horrible hack. Will get the rest of it working, then optimize

            # No helpful info is provided by the watcher if the target dir itself is deleted
            # So need to check before each event

            target_exists: bool = await target_async_path.exists()

            if not target_exists:
                self._logger.info("Delete event detected - %s is gone", self._input_path)
                return True

            await self._process_event(new_event)

    async def _input_path_created_task(self, target_async_path: aiopath.AsyncPath) -> None:
        """
        Called when _monitor_file detects that there's now something at the input_path location.
        Spun off into a separate method because want to get into starting the watch as fast as
        possible.
        """
        if self._input_path is None:
            self._logger.warning(
                "Unexpected call to _input_path_created_task - _input_path is None!"
            )
            return

        str_path: str = self._input_path

        if await target_async_path.is_dir():

            self._logger.info('New asset at "%s" detected as dir', self._input_path)

            await self.send(
                CreatedDirFSInputEvent(
                    dir_path=str_path, dir_async_path=target_async_path, base_event=None
                )
            )

        elif await target_async_path.is_file():

            self._logger.info('New asset at "%s" detected as file', self._input_path)

            await self.send(
                CreatedFileFSInputEvent(
                    file_path=str_path, file_async_path=target_async_path, base_event=None
                )
            )

        else:
            self._logger.warning(
                "Unexpected case in _input_path_created_task - %s", target_async_path
            )

    async def send(self, event: FSInputEvent) -> None:

        if self._output_queue is None:
            return

        await self._output_queue.put(event)

    async def _process_event(self, event: FileSystemEvent) -> None:
        """
        Take an event and process it before putting it on the wire.
        """
        # Filter null events
        if event is None:
            return

        if isinstance(
            event,
            (
                watchdog.events.FileCreatedEvent,
                watchdog.events.FileModifiedEvent,
                watchdog.events.FileMovedEvent,
                watchdog.events.FileSystemMovedEvent,
                watchdog.events.FileDeletedEvent,
            ),
        ):
            await self._process_file_event(event)
        elif isinstance(
            event,
            (
                watchdog.events.DirCreatedEvent,
                watchdog.events.DirModifiedEvent,
                watchdog.events.DirMovedEvent,
                watchdog.events.DirDeletedEvent,
            ),
        ):
            await self._process_dir_event(event)
        else:
            self._logger.info("Unhandled event in _process_event - %s", event)

    async def _process_file_event(self, event: FileSystemEvent) -> None:
        """
        Take an event and process it before putting it on the wire.
        """

        if isinstance(event, watchdog.events.FileCreatedEvent):

            await self._process_file_creation_event(event)

        elif isinstance(event, watchdog.events.FileModifiedEvent):

            await self._process_file_modified_event(event)

        elif isinstance(
            event, (watchdog.events.FileMovedEvent, watchdog.events.FileSystemMovedEvent)
        ):

            await self._process_file_move_event(event)

        elif isinstance(event, watchdog.events.FileDeletedEvent):

            await self._process_file_delete_event(event)

        else:
            self._logger.warning("Unexpected case in _process_file_event - %s", event)

    async def _process_file_creation_event(
        self, event: watchdog.events.FileCreatedEvent
    ) -> None:

        await self.send(
            CreatedFileFSInputEvent(
                file_path=event.src_path,
                file_async_path=aiopath.AsyncPath(event.src_path),
                base_event=event,
            )
        )

    async def _process_file_modified_event(
        self, event: watchdog.events.FileModifiedEvent
    ) -> None:

        file_async_path = aiopath.AsyncPath(event.src_path)

        await self.send(
            UpdatedFileFSInputEvent(
                file_path=event.src_path,
                file_async_path=file_async_path,
                base_event=event,
            )
        )

    async def _process_file_move_event(
        self,
        event: Union[
            watchdog.events.FileSystemMovedEvent, watchdog.events.FileSystemMovedEvent
        ],
    ) -> None:

        await self.send(
            MovedFileFSInputEvent(
                file_path=event.dest_path,
                file_src=event.src_path,
                file_async_path=aiopath.AsyncPath(event.src_path),
                base_event=event,
            )
        )

    async def _process_file_delete_event(
        self, event: watchdog.events.FileDeletedEvent
    ) -> None:

        await self.send(
            DeletedFileFSInputEvent(
                file_path=event.src_path,
                file_async_path=aiopath.AsyncPath(event.src_path),
                base_event=event,
            )
        )

    async def _process_dir_event(self, event: FileSystemEvent) -> None:
        """
        Take an event and process it before putting it on the wire.
        """

        # DIRS
        if isinstance(event, watchdog.events.DirCreatedEvent):

            await self.send(
                CreatedDirFSInputEvent(
                    dir_path=event.src_path,
                    dir_async_path=aiopath.AsyncPath(event.src_path),
                    base_event=event,
                )
            )

        elif isinstance(event, watchdog.events.DirModifiedEvent):
            await self.send(
                UpdatedDirFSInputEvent(
                    dir_path=event.src_path,
                    dir_async_path=aiopath.AsyncPath(event.src_path),
                    base_event=event,
                )
            )

        elif isinstance(event, watchdog.events.DirMovedEvent):

            await self.send(
                MovedDirFSInputEvent(
                    dir_src_path=event.src_path,
                    dir_src_async_path=aiopath.AsyncPath(event.src_path),
                    dir_path=event.dest_path,
                    dir_async_path=aiopath.AsyncPath(event.dest_path),
                    base_event=event,
                )
            )

        elif isinstance(event, watchdog.events.DirDeletedEvent):

            await self.send(
                DeletedDirFSInputEvent(
                    dir_path=event.src_path,
                    dir_async_path=aiopath.AsyncPath(event.src_path),
                    base_event=event,
                )
            )

    def watch(self) -> None:
        """
        Use watchdog in a separate thread to watch a dir for changes.
        """
        handler = _EventHandler(queue=self._internal_queue, loop=asyncio.get_event_loop())

        self._watchdog_observer = Observer()
        self._watchdog_observer.schedule(
            event_handler=handler, path=self._input_path, recursive=True
        )
        self._watchdog_observer.start()

        self._logger.info("Started _watchdog_observer")

        self._watchdog_observer.join(10)

        try:
            asyncio.get_event_loop().call_soon_threadsafe(
                self._internal_queue.put_nowait, None
            )
        except RuntimeError:  # Can happen when the shutdown is not clean
            return


class _EventHandler(FileSystemEventHandler):  # type: ignore

    _loop: asyncio.AbstractEventLoop
    _queue: asyncio.Queue[FileSystemEvent]

    def __init__(
        self,
        queue: asyncio.Queue[FileSystemEvent],
        loop: asyncio.AbstractEventLoop,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self._loop = loop
        self._queue = queue
        super(*args, **kwargs)

    def on_any_event(self, event: FileSystemEvent) -> None:
        try:
            self._loop.call_soon_threadsafe(self._queue.put_nowait, event)
        except RuntimeError:
            return
