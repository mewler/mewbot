#!/usr/bin/env python3

from __future__ import annotations

from typing import Optional, Set, Sequence, Type

import abc
import asyncio
import dataclasses

from mewbot.component import Component


@dataclasses.dataclass
class InputEvent:
    pass


@dataclasses.dataclass
class OutputEvent:
    pass


InputQueue = asyncio.Queue[InputEvent]
OutputQueue = asyncio.Queue[OutputEvent]


class IOConfig(Component):
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
        pass

    @abc.abstractmethod
    async def run(self) -> None:
        pass


class Output:
    @staticmethod
    def consumes_outputs() -> Set[Type[OutputEvent]]:
        pass

    async def output(self, event: OutputEvent) -> bool:
        pass
