#!/usr/bin/env python3

from __future__ import annotations

import abc
from typing import Set, Type, Optional, Dict, Any, Sequence

from mewbot.core import InputEvent, InputQueue, OutputEvent, OutputQueue, ComponentKind

from mewbot.component import ComponentRegistry, Component


@ComponentRegistry.register_api_version(ComponentKind.IO_CONFIG, "v1")
class IOConfig(Component):
    """
    Define a service that mewbot can connect to.
    """

    @abc.abstractmethod
    def get_inputs(self) -> Sequence[Input]:
        ...

    @abc.abstractmethod
    def get_outputs(self) -> Sequence[Output]:
        ...


class Input:
    queue = Optional[InputQueue]

    def __init__(self) -> None:
        self.queue = None

    def bind(self, queue: InputQueue) -> None:
        self.queue = queue

    @staticmethod
    def produces_inputs() -> Set[Type[InputEvent]]:
        """
        Defines the set of input events this Input class can produce.
        :return:
        """

    @abc.abstractmethod
    async def run(self) -> None:
        pass


class Output:
    @staticmethod
    def consumes_outputs() -> Set[Type[OutputEvent]]:
        """
        Defines the set of output events that this Output class can consume
        :return:
        """

    async def output(self, event: OutputEvent) -> bool:
        """
        Does the work of transmitting the event to the world.
        :param event:
        :return:
        """


@ComponentRegistry.register_api_version(ComponentKind.TRIGGER, "v1")
class Trigger(Component):
    @staticmethod
    @abc.abstractmethod
    def consumes_inputs() -> Set[Type[InputEvent]]:
        pass

    @abc.abstractmethod
    def matches(self, event: InputEvent) -> bool:
        pass


@ComponentRegistry.register_api_version(ComponentKind.CONDITION, "v1")
class Condition(Component):
    @staticmethod
    @abc.abstractmethod
    def consumes_inputs() -> Set[Type[InputEvent]]:
        pass

    @abc.abstractmethod
    def allows(self, event: InputEvent) -> bool:
        pass


@ComponentRegistry.register_api_version(ComponentKind.ACTION, "v1")
class Action(Component):
    @staticmethod
    @abc.abstractmethod
    def consumes_inputs() -> Set[Type[InputEvent]]:
        pass

    @staticmethod
    @abc.abstractmethod
    def produces_outputs() -> Set[Type[OutputEvent]]:
        pass

    _queue: Optional[OutputQueue]

    def __init__(self) -> None:
        self._queue = None

    def bind(self, queue: OutputQueue) -> None:
        self._queue = queue

    def send(self, event: OutputEvent) -> None:
        if not self._queue:
            raise Exception("Can not sent events before queue initialisation")

        self._queue.put_nowait(event)

    @abc.abstractmethod
    def act(self, event: InputEvent, state: Dict[str, Any]) -> None:
        pass
