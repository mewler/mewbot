#!/usr/bin/env python3

from __future__ import annotations

from typing import Any, Dict, List, Protocol, Sequence, Set, Type, Union, runtime_checkable

import asyncio
import enum
import dataclasses


class ComponentKind(str, enum.Enum):
    BEHAVIOUR = "Behaviour"
    TRIGGER = "Trigger"
    CONDITION = "Condition"
    ACTION = "Action"
    IO_CONFIG = "IOConfig"
    TEMPLATE = "Template"
    DATASOURCE = "DataSource"

    @classmethod
    def has_value(cls, value: str) -> bool:
        return value in cls.values()

    @classmethod
    def values(cls) -> List[str]:
        return list(e for e in cls)

    @classmethod
    def interface(cls, value: ComponentKind) -> Type[Any]:
        _map = {
            cls.BEHAVIOUR: BehaviourInterface,
            cls.TRIGGER: TriggerInterface,
            cls.CONDITION: ConditionInterface,
            cls.ACTION: ActionInterface,
            cls.IO_CONFIG: IOConfigInterface,
        }

        if value in _map:
            return _map[value]

        raise ValueError(f"Invalid value {value}")


@dataclasses.dataclass
class InputEvent:
    pass


@dataclasses.dataclass
class OutputEvent:
    pass


InputQueue = asyncio.Queue[InputEvent]
OutputQueue = asyncio.Queue[OutputEvent]


@runtime_checkable
class IOConfigInterface(Protocol):
    def get_inputs(self) -> Sequence[InputInterface]:
        pass

    def get_outputs(self) -> Sequence[OutputInterface]:
        pass


@runtime_checkable
class InputInterface(Protocol):
    @staticmethod
    def produces_inputs() -> Set[Type[InputEvent]]:
        """
        Defines the set of input events this Input class can produce.
        """

    def bind(self, queue: InputQueue) -> None:
        pass

    async def run(self) -> None:
        pass


@runtime_checkable
class OutputInterface(Protocol):
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


@runtime_checkable
class TriggerInterface(Protocol):
    @staticmethod
    def consumes_inputs() -> Set[Type[InputEvent]]:
        pass

    def matches(self, event: InputEvent) -> bool:
        pass


@runtime_checkable
class ConditionInterface(Protocol):
    @staticmethod
    def consumes_inputs() -> Set[Type[InputEvent]]:
        pass

    def allows(self, event: InputEvent) -> bool:
        pass


@runtime_checkable
class ActionInterface(Protocol):
    @staticmethod
    def consumes_inputs() -> Set[Type[InputEvent]]:
        pass

    @staticmethod
    def produces_outputs() -> Set[Type[OutputEvent]]:
        pass

    def bind(self, queue: OutputQueue) -> None:
        pass

    async def act(self, event: InputEvent, state: Dict[str, Any]) -> None:
        pass


@runtime_checkable
class BehaviourInterface(Protocol):
    def add(
        self, component: Union[TriggerInterface, ConditionInterface, ActionInterface]
    ) -> None:
        pass

    def consumes_inputs(self) -> Set[Type[InputEvent]]:
        pass

    def bind_output(self, output: OutputQueue) -> None:
        pass

    async def process(self, event: InputEvent) -> None:
        pass


__all__ = [
    "ComponentKind",
    "IOConfigInterface",
    "InputInterface",
    "OutputInterface",
    "BehaviourInterface",
    "TriggerInterface",
    "ConditionInterface",
    "ActionInterface",
    "InputEvent",
    "OutputEvent",
    "InputQueue",
    "OutputQueue",
]
