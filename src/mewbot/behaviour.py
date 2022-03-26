#!/usr/bin/env python3

from __future__ import annotations

from typing import Any, Dict, List, Set, Type, Union

from mewbot.core import InputEvent, TriggerInterface, ConditionInterface, ActionInterface


class Behaviour:
    active: bool = True
    triggers: List[TriggerInterface]
    conditions: List[ConditionInterface]
    actions: List[ActionInterface]

    interests: Set[Type[InputEvent]]

    def __init__(self) -> None:
        self.interests = set()
        self.triggers = []
        self.conditions = []
        self.actions = []

    def add(
        self, component: Union[TriggerInterface, ConditionInterface, ActionInterface]
    ) -> None:
        if not isinstance(component, (TriggerInterface, ConditionInterface, ActionInterface)):
            raise TypeError()

        interests = component.consumes_inputs()
        interests = self.interests.intersection(interests) if self.interests else interests

        if not interests:
            raise ValueError("Adding a behaviour component that doesn't match input types")

        self.interests = interests

        if isinstance(component, TriggerInterface):
            self.triggers.append(component)
        if isinstance(component, ConditionInterface):
            self.conditions.append(component)
        if isinstance(component, ActionInterface):
            self.actions.append(component)

    def consumes_inputs(self) -> Set[Type[InputEvent]]:
        return self.interests

    async def process(self, event: InputEvent) -> None:
        if not any(True for trigger in self.triggers if trigger.matches(event)):
            return

        if not all(True for condition in self.conditions if condition.allows(event)):
            return

        state: Dict[str, Any] = {}

        for action in self.actions:
            await action.act(event, state)
