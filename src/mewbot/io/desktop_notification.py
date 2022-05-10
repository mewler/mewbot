#!/usr/bin/env python3

from __future__ import annotations

from typing import Optional, Set, Sequence, Type, Any

import dataclasses
import logging
import sys
import subprocess

from mewbot.api.v1 import IOConfig, Input, Output, OutputEvent

try:
    from win10toast import ToastNotifier  # type: ignore
except ImportError:
    ToastNotifier = None

# Input for this class is theoretically possible and would be desirable - would allow mewbot to
# trigger on an arbitrary desktop notifications.
# Development ongoing


@dataclasses.dataclass
class DesktopNotificationOutputEvent(OutputEvent):
    """
    In most notification systems, you need a title and a body.
    """

    title: str
    text: str


class DesktopNotificationIO(IOConfig):

    _input: None
    _output: Optional[DesktopNotificationOutput] = None

    def __init__(self, *args: Optional[Any], **kwargs: Optional[Any]) -> None:
        self._logger = logging.getLogger(__name__ + "DesktopNotificationIO")
        # Not entirely sure why, but empty properties in the yaml errors
        self._logger.info("DesktopNotificationIO received args - %s", args)
        self._logger.info("DesktopNotificationIO received kwargs - %s", kwargs)

    def get_inputs(self) -> Sequence[Input]:

        return []

    def get_outputs(self) -> Sequence[Output]:
        if not self._output:
            self._output = DesktopNotificationOutput()

        return [self._output]


class DesktopNotificationOutput(Output):

    _engine: DesktopNotificationOutputEngine
    _logger: logging.Logger

    def __init__(self, *args: Optional[Any], **kwargs: Optional[Any]) -> None:
        super().__init__(*args, **kwargs)

        self._logger = logging.getLogger(__name__ + "DesktopNotificationOutput")
        self._logger.info(
            "Starting DesktopNotificationOutputEngine. Please assume crash positions!"
        )

        self._engine = DesktopNotificationOutputEngine()

    @staticmethod
    def consumes_outputs() -> Set[Type[OutputEvent]]:
        """
        Defines the set of output events that this Output class can consume
        :return:
        """
        return {DesktopNotificationOutputEvent}

    async def output(self, event: OutputEvent) -> bool:
        """
        Does the work of transmitting the event to the world.
        :param event:
        :return:
        """
        self._logger.info("output triggering with %s", event)

        if not isinstance(event, DesktopNotificationOutputEvent):
            return False

        return self._engine.notify(event.title, event.text)


class DesktopNotificationOutputEngine:
    """
    Cross-Platform notification shim/engine.

    Works by patching the `_notify` function at init time to contain the correct implementation.
    """

    _logger: logging.Logger
    _detected_os: str
    _platform_str: str
    _enabled: bool

    def __init__(self) -> None:

        self._logger = logging.getLogger(__name__ + "DesktopNotificationOutputEngine")
        self._logger.info("DesktopNotificationOutputEngine starting")

        # Note-to-self: Warn if we are in a non-tested state
        # Note-to-self: Need to test to see if we are headless and fallback if we are

        self._platform_str = sys.platform
        # Not using an f-string because we want lazy evaluation if possible
        self._logger.info("We are detected as running on %s", self._platform_str)

        # Could use "in" or string normalisation - but I want it to fail noisily and log the error
        # if I have made any incorrect assumptions.
        # So, hopefully, the user will tell us and I can check to see if anything creative
        # is required.
        # silent failure of desktop notifications is not desired. Noisy failure is.

        self._enabled = False
        if self._platform_str == "win32":
            self._detected_os = "windows"
            self._do_windows_setup()

        elif "linux" in self._platform_str:

            if self._platform_str == "linux2":
                self._logger.warning(
                    "You seem to be running python below 3.3, "
                    "or python behavior has changed - sys.platform = %s",
                    self._platform_str,
                )

            self._detected_os = "linux"
            # When notify2 is implemented, the _detected_os string for it will be linux_notify

        elif self._platform_str == "darwin":
            self._detected_os = "macos"
            self._enabled = False

        elif "freebsd" in self._platform_str or "dragonfly" in self._platform_str:
            self._detected_os = "freebsd"  # freebsd like behavior should work
            self._enabled = False

        elif "haiku" in self._platform_str:
            self._detected_os = "haiku"
            self._enabled = False

        else:
            self._logger.warning(
                "Unexpected and unsupported configuration %s - cannot enable",
                self._platform_str,
            )
            self._detected_os = "unknown"
            self._enabled = False

        if self._enabled:
            self._logger.info(
                "DesktopNotificationOutputEngine enabled - %s", self._detected_os
            )
        else:
            self._logger.warning(
                "DesktopNotificationOutputEngine failed to enable - %s", self._detected_os
            )

    def notify(self, title: str, text: str) -> bool:
        """
        Preform the actual notification task using the internal setup.
        Means we can avoid live patching externally accessible functions.
        """
        if not self._enabled:
            return False

        caller = {
            "windows": self._windows_toast_method,
            "linux": self._linux_notify_send_method,
            "linux_notify": self._linux_notify2_method,
        }.get(self._detected_os)

        if not caller:
            self._logger.warning("No notification method supported for %s", self._detected_os)
            return False

        return caller(title, text)

    def disable(self) -> None:
        """
        Disable the notification system.
        :return:
        """
        self._enabled = False

    @property
    def enabled(self) -> bool:
        return self._enabled

    def _do_windows_setup(self) -> None:
        """
        Determine if we can notify and disable self if cannot
        """
        if ToastNotifier is None:
            self._logger.info(
                "Cannot enable - chosen method requires win10toast and it's not installed"
            )
            self.disable()
            return
        assert ToastNotifier is not None

        setattr(self, "_notify", self._windows_toast_method)
        self._enabled = True

    def _linux_notify_send_method(self, title: str, text: str) -> bool:
        """
        Use notify-send to attempt to notify the user. This should work on (most) systems, but does
        not support callback or use dbus. _linux_notify2_method uses notify2 which wraps dbus.
        :return:
        """
        status = subprocess.call(["notify-send", title, text])
        if status == 0:
            return True

        self._logger.info("desktop notification failed with %s", status)
        return False

    def _linux_notify2_method(self, title: str, text: str) -> bool:
        # notify2 uses the python dbus bindings - which might well be needed for other things later
        # I have not - yet - managed to get a working recipe for this on my dev box
        self._logger.warning("Cannot notify - notify2 not working - %s - %s", title, text)
        return False

    def _windows_toast_method(self, title: str, text: str) -> bool:
        """
        Uses the win10toast library to send "toast" notifications.
        Except it turns out it doesn't. See the answers in
        https://stackoverflow.com/questions/64230231/
        In fact, it abuses the legacy win xp notification system - so no feedback.
        For the moment focus on getting notifications to display at all.
        :param title:
        :param text:
        :return:
        """
        if ToastNotifier is None:
            self._logger.info(
                "Cannot display - chosen method requires win10toast and it's not installed"
            )
            return False

        toaster = ToastNotifier()

        # Notification will be shown in own thread - so (hopefully) to allow yield back to
        # the main loop
        toaster.show_toast(title, text, duration=5, threaded=True)
        return True
