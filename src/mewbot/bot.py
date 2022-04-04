#!/usr/bin/env python3

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Type

import asyncio
import itertools
import logging
import signal

from mewbot.data import DataSource
from mewbot.core import (
    BehaviourInterface,
    IOConfigInterface,
    InputInterface,
    InputEvent,
    OutputInterface,
    OutputEvent,
    InputQueue,
    OutputQueue,
)

logging.basicConfig(level=logging.INFO)


class Bot:
    name: str  # The bot's name
    _io_configs: List[IOConfigInterface]  # Connections to bot makes to other services
    _behaviours: List[BehaviourInterface]  # All the things the bot does
    _datastores: Dict[str, DataSource[Any]]  # Data sources and stores for this bot

    def __init__(self, name: str) -> None:
        self.name = name
        self._io_configs = []
        self._behaviours = []
        self._datastores = {}

    def run(self) -> None:
        runner = BotRunner(
            self._marshal_behaviours(),
            self._marshal_inputs(),
            self._marshal_outputs(),
        )
        runner.run()

    def add_io_config(self, ioc: IOConfigInterface) -> None:
        self._io_configs.append(ioc)

    def add_behaviour(self, behaviour: BehaviourInterface) -> None:
        self._behaviours.append(behaviour)

    def get_data_source(self, name: str) -> Optional[DataSource[Any]]:
        return self._datastores.get(name)

    def _marshal_behaviours(self) -> Dict[Type[InputEvent], Set[BehaviourInterface]]:
        behaviours: Dict[Type[InputEvent], Set[BehaviourInterface]] = {}

        for behaviour in self._behaviours:
            for event_type in behaviour.consumes_inputs():
                behaviours.setdefault(event_type, set()).add(behaviour)

        return behaviours

    def _marshal_inputs(self) -> Set[InputInterface]:
        inputs = set()

        for connection in self._io_configs:
            for input in connection.get_inputs():
                inputs.add(input)

        return inputs

    def _marshal_outputs(self) -> Dict[Type[OutputEvent], Set[OutputInterface]]:
        outputs: Dict[Type[OutputEvent], Set[OutputInterface]] = {}

        for connection in self._io_configs:
            for _output in connection.get_outputs():
                for event_type in _output.consumes_outputs():
                    outputs.setdefault(event_type, set()).add(_output)

        return outputs


class BotRunner:
    input_event_queue: InputQueue
    output_event_queue: OutputQueue

    inputs: Set[InputInterface]
    outputs: Dict[Type[OutputEvent], Set[OutputInterface]] = {}
    behaviours: Dict[Type[InputEvent], Set[BehaviourInterface]] = {}

    _running: bool = False

    def __init__(
        self,
        behaviours: Dict[Type[InputEvent], Set[BehaviourInterface]],
        inputs: Set[InputInterface],
        outputs: Dict[Type[OutputEvent], Set[OutputInterface]],
    ) -> None:

        self.logger = logging.getLogger(__name__ + "BotRunner")

        self.input_event_queue = InputQueue()
        self.output_event_queue = OutputQueue()

        self.inputs = inputs
        self.outputs = outputs
        self.behaviours = behaviours

    def run(self, _loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        if self._running:
            raise RuntimeError("Bot is already running")

        loop = _loop if _loop else asyncio.get_event_loop()

        self.logger.info("Starting main event loop")
        self._running = True

        def stop(info: Optional[Any] = None) -> None:
            self.logger.warning("Stop called: %s", info)
            if self._running and loop.is_running():
                self.logger.info("Stopping loop run")
                loop.stop()
            self._running = False

        input_task = loop.create_task(self.process_input_queue())
        input_task.add_done_callback(stop)
        output_task = loop.create_task(self.process_output_queue())
        output_task.add_done_callback(stop)

        input_tasks = self.setup_tasks(loop)

        # Handle correctly terminating the loop
        try:
            loop.add_signal_handler(signal.SIGINT, stop)
        except NotImplementedError:
            # We're probably running on windows, where this is not an option
            pass
        try:
            loop.add_signal_handler(signal.SIGTERM, stop)
        except NotImplementedError:
            # We're probably running on windows, where this is not an option
            pass

        try:
            loop.run_forever()
        finally:
            # Stop accepting new events
            for task in input_tasks:
                if not task.done():
                    result = task.cancel()
                    self.logger.warning("Cancelling %s: %s", task, result)

            # Finish processing anything already in the queues.
            loop.run_until_complete(input_task)
            loop.run_until_complete(output_task)

    def setup_tasks(self, loop: asyncio.AbstractEventLoop) -> List[asyncio.Task[None]]:
        input_tasks: List[asyncio.Task[None]] = []

        # Startup the outputs - which are contained in the behaviors
        for behaviour in itertools.chain(*self.behaviours.values()):
            self.logger.info("Binding behaviour %s", behaviour)
            behaviour.bind_output(self.output_event_queue)

        # Startup the inputs
        for _input in self.inputs:
            _input.bind(self.input_event_queue)
            self.logger.info("Starting input %s", _input)
            input_tasks.append(loop.create_task(_input.run()))

        return input_tasks

    async def process_input_queue(self) -> None:
        while self._running:
            try:
                event = await asyncio.wait_for(self.input_event_queue.get(), 5)
            except asyncio.exceptions.TimeoutError:
                continue

            for event_type in self.behaviours:
                if isinstance(event, event_type):
                    for behaviour in self.behaviours[event_type]:
                        await behaviour.process(event)

    async def process_output_queue(self) -> None:
        while self._running:
            try:
                event = await asyncio.wait_for(self.output_event_queue.get(), 5)
            except asyncio.exceptions.TimeoutError:
                continue

            for event_type in self.outputs:
                if isinstance(event, event_type):
                    for output in self.outputs[event_type]:
                        await output.output(event)
