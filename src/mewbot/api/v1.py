#!/usr/bin/env python3

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Set, Union, Type

import abc

from mewbot.core import (
    InputEvent,
    InputQueue,
    OutputEvent,
    OutputQueue,
    ComponentKind,
    TriggerInterface,
    ConditionInterface,
    ActionInterface,
)
from mewbot.component import ComponentRegistry, Component, BehaviourConfigBlock


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
    queue: Optional[InputQueue]

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

    async def send(self, event: OutputEvent) -> None:
        if not self._queue:
            raise RuntimeError("Can not sent events before queue initialisation")

        await self._queue.put(event)

    @abc.abstractmethod
    async def act(self, event: InputEvent, state: Dict[str, Any]) -> None:
        pass


@ComponentRegistry.register_api_version(ComponentKind.BEHAVIOUR, "v1")
class Behaviour(Component):
    name: str
    active: bool

    triggers: List[Trigger]
    conditions: List[Condition]
    actions: List[Action]

    interests: Set[Type[InputEvent]]

    def __init__(self, name: str, active: bool = True) -> None:
        self.name = name
        self.active = active

        self.interests = set()
        self.triggers = []
        self.conditions = []
        self.actions = []

    # noinspection PyTypeChecker
    def add(
        self, component: Union[TriggerInterface, ConditionInterface, ActionInterface]
    ) -> None:
        if not isinstance(component, (Trigger, Condition, Action)):
            raise TypeError(f"Component {component} is not a Trigger, Condition, or Action")

        # noinspection PyUnresolvedReferences
        interests = component.consumes_inputs()
        interests = self.interests.intersection(interests) if self.interests else interests

        if not interests:
            raise ValueError(
                f"Component {component} doesn't match input types {self.interests}"
            )

        self.interests = interests

        if isinstance(component, Trigger):
            self.triggers.append(component)
        if isinstance(component, Condition):
            self.conditions.append(component)
        if isinstance(component, Action):
            self.actions.append(component)

    def consumes_inputs(self) -> Set[Type[InputEvent]]:
        return self.interests

    def bind_output(self, output: OutputQueue) -> None:
        for action in self.actions:
            action.bind(output)

    async def process(self, event: InputEvent) -> None:
        if not any(True for trigger in self.triggers if trigger.matches(event)):
            return

        if not all(True for condition in self.conditions if condition.allows(event)):
            return

        state: Dict[str, Any] = {}

        for action in self.actions:
            await action.act(event, state)

    def serialise(self) -> BehaviourConfigBlock:
        config = BehaviourConfigBlock(**super().serialise())  # type: ignore

        config["triggers"] = [x.serialise() for x in self.triggers]
        config["conditions"] = [x.serialise() for x in self.conditions]
        config["actions"] = [x.serialise() for x in self.actions]

        return config  # type: ignore


__all__ = [
    "IOConfig",
    "Input",
    "Output",
    "Behaviour",
    "Trigger",
    "Condition",
    "Action",
    "InputEvent",
    "OutputEvent",
]
