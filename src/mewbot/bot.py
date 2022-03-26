#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import itertools

from typing import Any, Dict, List, Optional, Set, Type

from mewbot.behaviour import Behaviour
from mewbot.data import DataSource
from mewbot.core import (
    IOConfigInterface,
    InputInterface,
    InputEvent,
    OutputInterface,
    OutputEvent,
    InputQueue,
    OutputQueue,
)


class Bot:
    name: str  # The bot's name
    io_configs: List[IOConfigInterface]  # Connections to bot makes to other services
    behaviours: List[Behaviour]  # All the things the bot does
    datastores: Dict[str, DataSource[Any]]  # Data sources and stores for this bot

    def __init__(self) -> None:
        self.name = "not_set"
        self.io_configs = []
        self.behaviours = []
        self.datastores = {}

    def run(self) -> None:
        runner = BotRunner(
            self._marshal_behaviours(),
            self._marshal_inputs(),
            self._marshal_outputs(),
        )
        runner.run()

    def add_io_config(self, ioc: IOConfigInterface) -> None:
        self.io_configs.append(ioc)

    def add_behaviour(self, behaviour: Behaviour) -> None:
        self.behaviours.append(behaviour)

    def get_data_source(self, name: str) -> Optional[DataSource[Any]]:
        return self.datastores.get(name)

    def _marshal_behaviours(self) -> Dict[Type[InputEvent], Set[Behaviour]]:
        behaviours: Dict[Type[InputEvent], Set[Behaviour]] = {}

        for behaviour in self.behaviours:
            for event_type in behaviour.consumes_inputs():
                behaviours.setdefault(event_type, set()).add(behaviour)

        return behaviours

    def _marshal_inputs(self) -> Set[InputInterface]:
        inputs = set(
            *itertools.chain(connection.get_inputs() for connection in self.io_configs)
        )

        return inputs

    def _marshal_outputs(self) -> Dict[Type[OutputEvent], Set[OutputInterface]]:
        outputs: Dict[Type[OutputEvent], Set[OutputInterface]] = {}

        for connection in self.io_configs:
            for _output in connection.get_outputs():
                for event_type in _output.consumes_outputs():
                    outputs.setdefault(event_type, set()).add(_output)

        return outputs


class BotRunner:
    input_event_queue: InputQueue
    output_event_queue: OutputQueue

    inputs: Set[InputInterface]
    outputs: Dict[Type[OutputEvent], Set[OutputInterface]] = {}
    behaviours: Dict[Type[InputEvent], Set[Behaviour]] = {}

    def __init__(
        self,
        behaviours: Dict[Type[InputEvent], Set[Behaviour]],
        inputs: Set[InputInterface],
        outputs: Dict[Type[OutputEvent], Set[OutputInterface]],
    ) -> None:
        self.input_event_queue = InputQueue()
        self.output_event_queue = OutputQueue()
        self.inputs = inputs
        self.outputs = outputs
        self.behaviours = behaviours

    def run(self) -> None:
        for _input in self.inputs:
            _input.bind(self.input_event_queue)
            asyncio.create_task(_input.run())

        for behaviour in itertools.chain(*self.behaviours.values()):
            for action in behaviour.actions:
                action.bind(self.output_event_queue)

        asyncio.create_task(self.process_input_queue())
        asyncio.create_task(self.process_output_queue())

        pending = asyncio.all_tasks()
        asyncio.get_event_loop().run_until_complete(asyncio.gather(*pending))

    async def process_input_queue(self) -> None:
        while True:
            event = await self.input_event_queue.get()

            for behaviour in self.behaviours[type(event)]:
                behaviour.process(event)

    async def process_output_queue(self) -> None:
        while True:
            event = await self.output_event_queue.get()

            for output in self.outputs[type(event)]:
                asyncio.create_task(output.output(event))
