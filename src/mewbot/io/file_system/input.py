#!/usr/bin/env python3

from __future__ import annotations

import os.path
from typing import Optional, Set, Type, Any

import asyncio
import datetime
import logging

import aiopath  # type: ignore
import watchfiles
import watchdog  # type: ignore
from watchdog.events import FileSystemEvent, FileSystemEventHandler  # type: ignore
from watchdog.observers import Observer  # type: ignore

from mewbot.api.v1 import Input, InputEvent
from mewbot.io.file_system.events import (
    FSInputEvent,
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
    InputFileDirDeletionInputEvent
)


class FileTypeFSInput(Input):
    """
    Using watchfiles as a backend to watch for events from a single file.
    Augmented by checks so that the system responds properly if the file does not initially exist.
    Or is deleted during the monitoring process.
    If the watcher is started on a folder, it will wait for the folder to go away before starting.
    If the file is deleted and replaced with a folder, it will wait for the folder to be replaced
    with a file before monitoring.
    """

    _logger: logging.Logger

    _input_path: Optional[str] = None  # A location on the file system to monitor
    _input_path_exists: bool = False
    _input_path_type: Optional[str] = None

    def __init__(self, input_path: Optional[str] = None) -> None:
        super(Input, self).__init__()  # pylint: disable=bad-super-call

        self._input_path = input_path

        self._logger = logging.getLogger(__name__ + ":" + type(self).__name__)

        if input_path is None or not os.path.exists(input_path):

            self.watcher = None
            self._input_path_exists = False
            self._input_path_type = None

        # The only case where the watcher can actually start
        elif self._input_path is not None:  # needed to fool pylint

            self.watcher = watchfiles.awatch(self._input_path)
            self._input_path_exists = True

            if os.path.isdir(self._input_path):
                self._input_path_type = "dir"
            else:
                self._input_path_type = "file"

        else:
            raise NotImplementedError

    @staticmethod
    def produces_inputs() -> Set[Type[InputEvent]]:
        """
        Defines the set of input events this Input class can produce.
        This type of InputClass monitors a single file
        So a number of the file type inputs make no sense for it.
        """
        return {
            InputFileFileCreationInputEvent,  # A file is created at the monitored point
            UpdatedFileFSInputEvent,  # The monitored file is updated
            InputFileFileDeletionInputEvent,  # The monitored file is deleted
        }

    @property
    def input_path(self) -> Optional[str]:
        return self._input_path

    @input_path.setter
    def input_path(self, new_input_path: Optional[str]) -> None:
        self._input_path = new_input_path

    @property
    def input_path_exists(self) -> bool:
        return self._input_path_exists

    @input_path_exists.setter
    def input_path_exists(self, value: Any) -> None:
        """
        Input path is determined internally using some variant of os.path.
        """
        raise AttributeError("input_path_exists cannot be externally set")

    async def run(self) -> None:
        """
        Fires up an aiohttp app to run the service.
        Token needs to be set by this point.
        """
        # Restart if the input path changes ... might be a good idea
        if self._input_path_exists and self._input_path_type == "file":
            self._logger.info(
                'Starting FileTypeFSInput - monitoring existing file "%s"', self._input_path
            )

        elif self._input_path_exists and self._input_path_type == "dir":
            self._logger.warning(
                "Starting FileTypeFSInput - monitoring file is a dir '%s'", self._input_path
            )

        else:
            self._logger.info(
                'Waiting to start FileSystemInput - provided input path did not exist "%s"',
                self._input_path,
            )

        while True:

            await self._monitor_input_path()
            await self._monitor_file_watcher()

    async def send(self, event: FSInputEvent) -> None:

        if self.queue is None:
            return

        await self.queue.put(event)

    async def _monitor_input_path(self) -> None:
        """
        Preforms a check on the file - updating if needed.
        """
        if self._input_path_exists and self._input_path_type == "file":
            return

        self._logger.info(
            "The provided input path will be monitored until a file appears - %s - %s",
            self._input_path,
            self._input_path_type,
        )

        while True:

            if self._input_path is None:
                await asyncio.sleep(0.5)  # Give the rest of the loop a chance to do something
                continue

            target_async_path: aiopath.AsyncPath = aiopath.AsyncPath(self._input_path)
            target_exists: bool = await target_async_path.exists()
            is_target_dir: bool = await target_async_path.is_dir()
            if not target_exists:

                await asyncio.sleep(0.5)  # Give the rest of the loop a chance to do something
                continue

            if target_exists and is_target_dir:

                await asyncio.sleep(0.5)  # Give the rest of the loop a chance to do something
                continue

            # Something has come into existence since the last loop
            self._logger.info(
                "Something has appeared at the input_path - %s", self._input_path
            )

            # All the logic which needs to be run when a file is created at the target location
            # Aim is to get the event on the wire as fast as possible, so as to start the watcher
            # To minimize the chance of missing events
            asyncio.get_running_loop().create_task(
                self._input_path_file_created_task(target_async_path)
            )

            self.watcher = watchfiles.awatch(self._input_path)
            self._input_path_exists = True
            return

    async def _input_path_file_created_task(
        self, target_async_path: aiopath.AsyncPath
    ) -> None:
        """
        Called when _monitor_file detects that there's now something at the input_path location.
        Spun off into a separate method because want to get into starting the watch as fast as
        possible.
        """
        if self._input_path is None:
            self._logger.warning(
                "Unexpected call to _input_path_file_created_task - _input_path is None!"
            )
            return

        if self._input_path is not None and self._input_path_type == "dir":
            self._logger.warning(
                "Unexpected call to _input_path_file_created_task - "
                "_input_path is not None but _input_path_type is dir"
            )

        str_path: str = self._input_path

        if await target_async_path.is_dir():

            self._logger.info('New asset at "%s" detected as dir', self._input_path)

        elif await target_async_path.is_file():

            self._logger.info('New asset at "%s" detected as file', self._input_path)

            await self.send(
                InputFileFileCreationInputEvent(
                    file_path=str_path, file_async_path=target_async_path
                )
            )

        else:
            self._logger.warning(
                "Unexpected case in _input_path_created_task - %s", target_async_path
            )

    async def _monitor_file_watcher(self) -> None:
        """
        Actually do the job of monitoring and responding to the watcher.
        If the file is detected as deleted, then the
        """
        # Ideally this would be done with some kind of run-don't run lock
        # Waiting on better testing before attempting that.
        if self.watcher is None:
            self._logger.info("Unexpected case - self.watcher is None in _monitor_watcher")
            await asyncio.sleep(0.5)  # Give the rest of the loop a chance to act
            return

        async for changes in self.watcher:
            file_deleted = await self._process_changes(changes)

            if file_deleted:
                # File is detected as deleted
                # - shutdown the watcher
                # - indicate we need to start monitoring for a new file
                # (or folder - in which case this will do nothing more)
                self.watcher = None
                self._input_path_exists = False

                return

    async def _process_changes(self, changes: Set[tuple[watchfiles.Change, str]]) -> bool:

        # Changes are sets of chance objects
        # tuples with
        #  - the first entry being a watchfiles.Change object
        #  - the second element being a str path to the changed item

        for change in changes:

            change_type, change_path = change

            if change_type == watchfiles.Change.added:
                self._logger.warning(
                    "With how we are using watchfiles this point should never be reached - %s - '%s'",
                    change_type,
                    change_path,
                )

            elif change_type == watchfiles.Change.modified:
                await self._do_update_event(change_path)

            elif change_type == watchfiles.Change.deleted:
                await self._do_delete_event(change_path)
                return True

            else:
                self._logger.warning(
                    "Unexpected case when trying to parse file change - %s", change_type
                )

        return False

    async def _do_update_event(self, change_path: str) -> None:
        """
        Called when the monitored file is updated.
        """
        target_async_path = aiopath.AsyncPath(change_path)

        await self.send(
            UpdatedFileFSInputEvent(file_path=change_path, file_async_path=target_async_path)
        )

    async def _do_delete_event(self, change_path: str) -> None:
        """
        Called when the monitored file is deleted.
        """
        target_async_path = aiopath.AsyncPath(change_path)

        await self.send(
            InputFileFileDeletionInputEvent(
                file_path=change_path, file_async_path=target_async_path
            )
        )


class DirTypeFSInput(Input):
    """
    File system input intended for directory like objects.
    """

    _logger: logging.Logger

    _input_path: Optional[str] = None  # A location on the file system to monitor
    _input_path_exists: bool = False  # Was a something found at this location?

    _watchdog_observer: Observer = Observer()

    def __init__(self, input_path: Optional[str] = None) -> None:
        super(Input, self).__init__()  # pylint: disable=bad-super-call

        self._input_path = input_path

        self._logger = logging.getLogger(__name__ + ":" + type(self).__name__)

        if input_path is None or not os.path.exists(input_path):

            self._input_path_exists = False
            self._input_path_type = None

        # Cannot await in this context - this is being done before loop start
        elif not os.path.exists(input_path):

            self._input_path_exists = False
            self._input_path_type = None

        # The only case where the watcher can actually start
        elif self._input_path is not None:  # needed to fool pylint

            self._input_path_exists = True

            if os.path.isdir(self._input_path):
                self._input_path_type = "dir"
            else:
                self._input_path_type = "file"

        else:
            raise NotImplementedError

        # Events will be read off this queue and processed
        self._internal_queue: asyncio.Queue[FileSystemEvent] = asyncio.Queue()

    @staticmethod
    def produces_inputs() -> Set[Type[InputEvent]]:
        """
        Defines the set of input events this Input class can produce.
        This is intended to be run on a dir - so will produce events for all the things
        in the dir as well.
        Additionally, the dir being monitored itself can be deleted.
        Hence the final two event types.
        """
        return {
            CreatedFileFSInputEvent,
            UpdatedFileFSInputEvent,
            DeletedFileFSInputEvent,
            CreatedDirFSInputEvent,
            UpdatedDirFSInputEvent,
            DeletedDirFSInputEvent,
            InputFileDirCreationInputEvent,
            InputFileDirDeletionInputEvent,
        }

    @property
    def input_path(self) -> Optional[str]:
        return self._input_path

    @input_path.setter
    def input_path(self, new_input_path: Optional[str]) -> None:
        self._input_path = new_input_path

    @property
    def input_path_exists(self) -> bool:
        return self._input_path_exists

    @input_path_exists.setter
    def input_path_exists(self, value: Any) -> None:
        """
        Input path is determined internally using some variant of os.path.
        """
        raise AttributeError("input_path_exists cannot be externally set")

    async def run(self) -> None:
        """
        Fires up an aiohttp app to run the service.
        Token needs to be set by this point.
        """
        # Restart if the input path changes ... might be a good idea
        if self._input_path_exists and self._input_path_type == "dir":
            self._logger.info(
                'Starting DirTypeFSInput - monitoring existing dir "%s"', self._input_path
            )

        elif self._input_path_exists and self._input_path_type == "dir":
            self._logger.warning(
                "Starting DirTypeFSInput - monitoring dir is a file '%s'", self._input_path
            )

        else:
            self._logger.info(
                'Waiting to start DirTypeFSInput - provided input path did not exist "%s"',
                self._input_path,
            )

        while True:

            await self._monitor_input_path()
            await self._monitor_dir_watcher()

    async def _monitor_input_path(self) -> None:
        """
        Preforms a check on the file - updating if needed.
        """
        if self._input_path_exists and self._input_path_type == "dir":
            return

        self._logger.info(
            "The provided input path will be monitored until a dir appears - %s - %s",
            self._input_path,
            self._input_path_type,
        )

        while True:

            if self._input_path is None:
                await asyncio.sleep(0.5)  # Give the rest of the loop a chance to do something
                continue

            target_async_path: aiopath.AsyncPath = aiopath.AsyncPath(self._input_path)
            target_exists: bool = await target_async_path.exists()
            is_target_file: bool = await target_async_path.is_file()

            if target_exists and is_target_file:

                await asyncio.sleep(0.5)  # Give the rest of the loop a chance to do something
                continue

            if not target_exists:

                await asyncio.sleep(0.5)  # Give the rest of the loop a chance to do something
                continue

            # Something has come into existence since the last loop
            self._logger.info(
                "Something has appeared at the input_path - %s", self._input_path
            )

            asyncio.get_running_loop().create_task(
                self._input_path_dir_created_task(target_async_path)
            )

            self._input_path_exists = True
            return

    async def _input_path_dir_created_task(
        self, target_async_path: aiopath.AsyncPath
    ) -> None:
        """
        Called when _monitor_file detects that there's now something at the input_path location.
        Spun off into a separate method because want to get into starting the watch as fast as
        possible.
        """
        if self._input_path is None:
            self._logger.warning(
                "Unexpected call to _input_path_file_created_task - _input_path is None!"
            )
            return
        if self._input_path is not None and self._input_path_type == "file":
            self._logger.warning(
                "Unexpected call to _input_path_file_created_task - "
                "_input_path is not None but _input_path_type is file"
            )

        str_path: str = self._input_path

        if await target_async_path.is_file():  # Not sure this case should ever be reached

            self._logger.info('New asset at "%s" detected as file', self._input_path)

        elif await target_async_path.is_dir():

            self._logger.info('New asset at "%s" detected as dir', self._input_path)

            await self.send(
                InputFileDirCreationInputEvent(
                    dir_path=str_path, dir_async_path=target_async_path
                )
            )

        else:
            self._logger.warning(
                "Unexpected case in _input_path_created_task - %s", target_async_path
            )

    async def _monitor_dir_watcher(self) -> None:

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
                )
            )
            self._input_path_exists = False

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
                CreatedDirFSInputEvent(dir_path=str_path, dir_async_path=target_async_path)
            )

        elif await target_async_path.is_file():

            self._logger.info('New asset at "%s" detected as file', self._input_path)

            await self.send(
                CreatedFileFSInputEvent(file_path=str_path, file_async_path=target_async_path)
            )

        else:
            self._logger.warning(
                "Unexpected case in _input_path_created_task - %s", target_async_path
            )

    async def send(self, event: FSInputEvent) -> None:

        if self.queue is None:
            return

        await self.queue.put(event)

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
        # FILES
        if isinstance(event, watchdog.events.FileCreatedEvent):
            await self.send(
                CreatedFileFSInputEvent(
                    file_path=event.src_path,
                    file_async_path=aiopath.AsyncPath(event.src_path),
                )
            )

        elif isinstance(event, watchdog.events.FileModifiedEvent):
            await self.send(
                UpdatedFileFSInputEvent(
                    file_path=event.src_path,
                    file_async_path=aiopath.AsyncPath(event.src_path),
                )
            )

        elif isinstance(event, watchdog.events.FileMovedEvent):
            await self.send(
                MovedFileFSInputEvent(
                    file_path=event.src_path,
                    file_async_path=aiopath.AsyncPath(event.src_path),
                )
            )

        elif isinstance(event, watchdog.events.FileSystemMovedEvent):
            self._logger.info("System moved a file %s", str(event))
            await self.send(
                MovedFileFSInputEvent(
                    file_path=event.src_path,
                    file_async_path=aiopath.AsyncPath(event.src_path),
                )
            )

        elif isinstance(event, watchdog.events.FileDeletedEvent):
            await self.send(
                DeletedFileFSInputEvent(
                    file_path=event.src_path,
                    file_async_path=aiopath.AsyncPath(event.src_path),
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
                )
            )

        elif isinstance(event, watchdog.events.DirModifiedEvent):
            await self.send(
                UpdatedDirFSInputEvent(
                    dir_path=event.src_path,
                    dir_async_path=aiopath.AsyncPath(event.src_path),
                )
            )

        elif isinstance(event, watchdog.events.DirMovedEvent):
            await self.send(
                MovedDirFSInputEvent(
                    dir_src_path=event.src_path,
                    dir_src_async_path=aiopath.AsyncPath(event.src_path),
                    dir_path=event.dest_path,
                    dir_async_path=aiopath.AsyncPath(event.dest_path),
                )
            )

        elif isinstance(event, watchdog.events.DirDeletedEvent):
            await self.send(
                DeletedDirFSInputEvent(
                    dir_path=event.src_path, dir_async_path=aiopath.AsyncPath(event.src_path)
                )
            )

    def watch(self) -> None:
        """
        Use watchdog in a seperate thread to watch a dir for changes.
        """
        handler = _EventHandler(queue=self._internal_queue, loop=asyncio.get_event_loop())

        self._watchdog_observer = Observer()
        self._watchdog_observer.schedule(
            event_handler=handler, path=self._input_path, recursive=True
        )
        self._watchdog_observer.start()

        self._logger.info("Started _watchdog_observer")

        self._watchdog_observer.join(10)

        asyncio.get_event_loop().call_soon_threadsafe(self._internal_queue.put_nowait, None)


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
        self._loop.call_soon_threadsafe(self._queue.put_nowait, event)
