#!/usr/bin/env python3

from __future__ import annotations

from typing import Type, Any, List, Generator, TypedDict, Dict, Sequence, Set

import abc
import asyncio
import importlib
import inspect
import sys
import uuid

from datastore import DataStore, DataSource


class ConfigBlock(TypedDict):
    api: str
    kind: str
    properties: Dict[str, Any]


def limit_multi_inheritence(cls):
    Registry.mi_limits.append(cls)
    return cls


class Registry(abc.ABCMeta):
    registered: List[Type[Any]] = []
    mi_limits: List[Type[Any]] = []

    def __new__(cls, name: str, bases: Any, namespace: Any, **k) -> Type[Any]:
        created_type: Type[Any] = super().__new__(cls, name, bases, namespace, **k)

        if sum(1 for base in cls.mi_limits if issubclass(created_type, base)) > 1:
            raise Exception("You may not inherit from more than one of Mewbot's base types")

        # if not created_type.__doc__:
        #    raise Exception(f"No docs? No service! ({name})")

        Registry.registered.append(created_type)
        return created_type


def registered_classes(implements: Type[Any]) -> Generator[Type[Any], None, None]:
    return (
        cls
        for cls in Registry.registered
        if issubclass(cls, implements) and not inspect.isabstract(cls)
    )


def load_from_config(config: ConfigBlock) -> BaseRegisterable:
    if set(config.keys()) != {"api", "id", "kind", "properties"}:
        raise Exception("Invalid configuration keys")

    if config["api"] not in sys.modules:
        importlib.import_module(config["api"])

    module = sys.modules[config["api"]]

    if not hasattr(module, config["kind"]):
        raise Exception(f"Unable to find {config['kind']} in {config['api']}")

    target_class: Type[Any] = getattr(module, config["kind"])

    if not issubclass(target_class, BaseRegisterable):
        raise Exception("Trying to load a non-registered class from config")

    return target_class(id=config["id"], **config["properties"])


class BaseRegisterable(metaclass=Registry):
    """Hello!"""

    def __new__(cls, **properties: Any) -> BaseRegisterable:
        if not issubclass(cls, BaseRegisterable):
            raise Exception("Attempting to create a non registerable class")

        obj: BaseRegisterable = super(BaseRegisterable, cls).__new__(cls)

        _dir = dir(cls)

        for prop, value in properties.items():
            if hasattr(_dir, prop):
                raise Exception(f"No such property {prop} on {cls}")

            if not isinstance(getattr(cls, prop), property):
                raise Exception(f"Property {prop} on {cls} is not a @property")

            if getattr(cls, prop).fset:
                setattr(obj, prop, value)

        if "id" in properties:
            obj._id = properties["id"]
        else:
            obj._id = uuid.uuid4()

        return obj

    def serialise(self) -> ConfigBlock:
        cls = type(self)

        output: ConfigBlock = {
            "api": cls.__module__,
            "kind": cls.__name__,
            "id": self.id,
            "properties": {},
        }

        for prop in dir(cls):
            if not isinstance(getattr(cls, prop), property):
                continue

            if getattr(cls, prop).fset:
                output["properties"][prop] = getattr(self, prop)

        return output

    @property
    def id(self) -> str:
        return self._id

    def __init__(self, **k: Any) -> None:
        pass


class Bot:
    name: str  # The bot's name
    io: List[IOConfig]  # Connections to bot makes to other services
    behaviours: List[Behaviour]  # All the things the bot does
    datastores: Dict[str, DataStore]  # Datastores for this bot

    def run():
        input_event_queue = Queue()
        output_event_queue = Queue()

        outputs: Dict[Type[OutputEvent], Set[Output]] = {}

        for connection in self.io:
            for _input in connection.get_inputs():
                _input.bind(input_event_queue)
                asyncio.submit(_input.run())

            for _output in connection.get_outputs():
                for event_type in _output.consumes_outputs():
                    outputs.setdefault(event_type, set()).add(_output)

        behaves: Dict[Type[InputEvent], Set[Behaviour]] = {}

        for behaviour in behaviours:
            for action in behaviour.actions:
                action.bind(output_event_queue)

            for event_type in behaviour.consumes_inputs():
                behaves.setdefault(event_type, set()).add(behaviour)

        runner = BotRubber(input_event_queue, output_event_queue, outputs, behaves)

        asyncio.submit(runner.process_input_queue)
        asyncio.submit(runner.process_output_queue)
        asyncio.run_until_complete()


class BotRunner:
    input_event_queue: Queue
    output_event_queue: Queue

    outputs: Dict[Type[OutputEvent], Set[Output]] = {}
    behaves: Dict[Type[InputEvent], Set[Behaviour]] = {}

    def __init__(
        self,
        input_event_queue: Queue,
        output_event_queue: Queue,
        outputs: Dict[Type[OutputEvent], Set[Output]],
        behaves: Dict[Type[InputEvent], Set[Behaviour]],
    ) -> None:
        self.input_event_queue = input_event_queue
        self.output_event_queue = output_event_queue
        self.outputs = outputs
        self.behaves = behaves

    def process_input_queue():
        while True:
            event = input_event_queue.get()

            for behaviour in self.behaviours[type(event)]:
                behaviour.process(event)

    def process_output_queue():
        while True:
            event = output_event_queue.get()

            for output in self.outputs[type(event)]:
                asyncio.submit(output.output(event))


class BehaviourComponent(BaseRegisterable):
    @staticmethod
    def consumes_inputs() -> Set[Type[InputEvent]]:
        pass


class TwitchChatMessage:
    message: str


@limit_multi_inheritence
class Trigger(BehaviourComponent):
    def matches(event: InputEvent) -> bool:
        pass


class TwitchChatMessageCommandTrigger(Trigger):
    @staticmethod
    def consumes_inputs():
        return [TwitchChatMessage]

    def matches(event: TwitchChatMessage) -> bool:
        return event.message.startswith("!help")


@limit_multi_inheritence
class Condition:
    def allows(event: InputEvent) -> bool:
        pass


class TwitchCommandModOnlyCondition(Condition):
    def consumes_inputs():
        return [TwitchChatMessage]

    def matches(event: TwitchChatMessage) -> bool:
        return event.user.is_moderator


@limit_multi_inheritence
class Action:
    def __init__(self, output_queue) -> None:
        self._queue = output_queue

    def produces_output() -> Set[Type[OutputEvent]]:
        pass

    def send(self, event: OutputEvent) -> None:
        self._queue.submit(event)

    def act(event: InputEvent, state: Dict[str, Any]) -> Dict[str, Any]:
        pass


class PickUnhelpfulMessageAction(Action):
    @property
    def message_store(self) -> DataSource[str]:
        return self._store

    @message_store.setter
    def message_store(self, store: DataSource[str]) -> None:
        self._store = store

    def consumes_inputs():
        return [TwitchChatMessage]

    def act(self, event: InputEvent, state: Dict[str, Any]) -> Dict[str, Any]:
        state["message"] = self._store.get()


class SendReplyToTwitch(Action):
    def consumes_inputs():
        return [TwitchChatMessage]

    def act(self, event: TwitchChatMessage, state: Dict[str, Any]) -> Dict[str, Any]:
        self.send(TwitchChatMessageOutput(channel=event.channel, message=state["message"]))


class SendMessageToTwitch(Action):
    @property
    def twitch_channel(self) -> str:
        return self._channel

    @staticmethod
    def consumes_inputs():
        return [TextInputEvent]

    def act(self, event: TwitchChatMessage, state: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(event, TwitchChatMessage) and event.channel == self.twitch_channel:
            return

        self.send(TwitchChatMessageOutput(channel=self.twitch_channel, message=event.message))


class Behaviour:
    active: bool = True
    triggers: List[Trigger]  # This of things that can trigger this behaviour
    conditions: List[
        Condition
    ]  # conditions on the action being called when it is matched (e.g. "is subscribed")
    actions: List[Action]  # the things to do if an event matches, and the conditions are met

    interests: Set[Type[InputEvent]]

    def __init__(self):
        self.interests = set()
        self.triggers = []
        self.conditions = []
        self.actions = []

    def add(self, block: BaseRegisterable) -> None:
        if not any(issubclass(block, x) for x in [Trigger, Condition, Action]):
            raise TypeError()

        interests = block.consumes_inputs()

        if self.interests and not self.interests.intersection(interests):
            raise ValueError("Adding a behaviour component that doesn't match input types")

        if issubclass(block, Trigger):
            self.trigger.append(block)
        if issubclass(block, Condition):
            self.condition.append(block)
        if issubclass(block, Action):
            self.action


class IOConfig(BaseRegisterable):
    @abc.abstractmethod
    def get_inputs(self) -> Sequence[Input]:
        ...

    @abc.abstractmethod
    def get_outputs(self) -> Sequence[Output]:
        ...


class Input:
    def __init__(self):
        self.queue = None

    def bind(queue):
        self.queue = queue

    @staticmethod
    def produces_inputs() -> Set[Type[InputEvent]]:
        pass

    @abc.abstractmethod
    async def run():
        pass


class Output:
    @staticmethod
    def consumes_outputs() -> Set[Type[OutputEvent]]:
        pass

    async def output(event: OutputEvent) -> bool:
        pass


class InputEvent:
    pass


class OutputEvent:
    pass


# class Base(Trigger, Action):
#    pass


class Foo(BaseRegisterable):
    _channel: str

    def __init__(self, **k: Any) -> None:
        super().__init__()

        if not hasattr(self, "_channel"):
            self._channel = "oops"

    @property
    def channel(self) -> str:
        return self._channel

    @channel.setter
    def channel(self, val: str) -> None:
        print(f"Setting channel to {val}")
        self._channel = val

    def __str__(self) -> str:
        return f"Foo(channel={self.channel})"


x = Foo(channel="foo", id="bar")
print(x)
x.channel = "cat"
print(x.serialise())
print(load_from_config(x.serialise()))

# x = Foo()
# print(x)
# x.channel = "cat"
# print(x.serialise())
