#!/usr/bin/env python3

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Type

import abc

from mewbot.component import Component
from mewbot.io import InputEvent, OutputEvent, OutputQueue
from mewbot.registry import limit_multi_inheritence


class BehaviourComponent(Component):
    @staticmethod
    @abc.abstractmethod
    def consumes_inputs() -> Set[Type[InputEvent]]:
        pass


@limit_multi_inheritence
class Trigger(BehaviourComponent):
    @abc.abstractmethod
    def matches(self, event: InputEvent) -> bool:
        pass


@limit_multi_inheritence
class Condition(BehaviourComponent):
    @abc.abstractmethod
    def allows(self, event: InputEvent) -> bool:
        pass


@limit_multi_inheritence
class Action(BehaviourComponent):
    @staticmethod
    @abc.abstractmethod
    def produces_outputs() -> Set[Type[OutputEvent]]:
        pass

    _queue: Optional[OutputQueue]

    def __init__(self) -> None:
        super().__init__()
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


class Behaviour:
    active: bool = True
    triggers: List[Trigger]  # This of things that can trigger this behaviour
    conditions: List[
        Condition
    ]  # conditions on the action being called when it is matched (e.g. "is subscribed")
    actions: List[Action]  # the things to do if an event matches, and the conditions are met

    interests: Set[Type[InputEvent]]

    def __init__(self) -> None:
        self.interests = set()
        self.triggers = []
        self.conditions = []
        self.actions = []

    def add(self, block: BehaviourComponent) -> None:
        if not isinstance(block, BehaviourComponent):
            raise TypeError()

        interests = block.consumes_inputs()
        interests = self.interests.intersection(interests) if self.interests else interests

        if not interests:
            raise ValueError("Adding a behaviour component that doesn't match input types")

        self.interests = interests

        if isinstance(block, Trigger):
            self.triggers.append(block)
        if isinstance(block, Condition):
            self.conditions.append(block)
        if isinstance(block, Action):
            self.actions.append(block)

    def consumes_inputs(self) -> Set[Type[InputEvent]]:
        return self.interests

    def process(self, event: InputEvent) -> None:
        if not any(True for trigger in self.triggers if trigger.matches(event)):
            return

        if not all(True for condition in self.conditions if condition.allows(event)):
            return

        state: Dict[str, Any] = {}

        for action in self.actions:
            action.act(event, state)
