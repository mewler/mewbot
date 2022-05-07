#!/use/bin/env python3

from __future__ import annotations

from typing import Type, Any, TextIO

import importlib
import sys
import yaml

from mewbot.bot import Bot
from mewbot.component import ConfigBlock, BehaviourConfigBlock
from mewbot.core import (
    Component,
    ComponentKind,
    IOConfigInterface,
    BehaviourInterface,
    TriggerInterface,
    ConditionInterface,
    ActionInterface,
)


_REQUIRED_KEYS = set(ConfigBlock.__annotations__.keys())  # pylint: disable=no-member


def assert_message(obj: Any, interface: Type[Any]) -> str:
    uuid = getattr(obj, "uuid", "<unknown>")
    return (
        f"Loaded component did not implemented expected interface {interface}. "
        f"Loaded component: type={type(obj)}, uuid={uuid}, info={str(obj)}"
    )


def configure_bot(name: str, stream: TextIO) -> Bot:
    bot = Bot(name)
    number = 0

    for document in yaml.load_all(stream, Loader=yaml.CSafeLoader):
        number += 1

        if not _REQUIRED_KEYS.issubset(document.keys()):
            raise ValueError(
                f"Document {number} missing some keys: {_REQUIRED_KEYS.difference(document.keys())}"
            )

        if document["kind"] == ComponentKind.BEHAVIOUR:
            bot.add_behaviour(load_behaviour(document))
        if document["kind"] == ComponentKind.DATASOURCE:
            ...
        if document["kind"] == ComponentKind.IO_CONFIG:
            component = load_component(document)
            assert isinstance(component, IOConfigInterface), assert_message(
                component, IOConfigInterface
            )
            bot.add_io_config(component)

    return bot


def load_behaviour(config: BehaviourConfigBlock) -> BehaviourInterface:
    behaviour = load_component(config)

    assert isinstance(behaviour, BehaviourInterface)

    for trigger_definition in config["triggers"]:
        trigger = load_component(trigger_definition)
        assert isinstance(trigger, TriggerInterface), assert_message(
            trigger, TriggerInterface
        )
        behaviour.add(trigger)

    for condition_definition in config["conditions"]:
        condition = load_component(condition_definition)
        assert isinstance(condition, ConditionInterface), assert_message(
            condition, ConditionInterface
        )
        behaviour.add(condition)

    for action_definition in config["actions"]:
        action = load_component(action_definition)
        assert isinstance(action, ActionInterface), assert_message(action, ActionInterface)
        behaviour.add(action)

    return behaviour


def load_component(config: ConfigBlock) -> Component:
    # Ensure that the object we have been passed contains all required fields.
    if not _REQUIRED_KEYS.issubset(config.keys()):
        raise ValueError(
            f"Config missing some keys: {_REQUIRED_KEYS.difference(config.keys())}"
        )

    # Load the module the component is expected to be in.
    # This happens first as it may cause API versions to be registered for the first time.
    if config["module"] not in sys.modules:
        importlib.import_module(config["module"])

    if not ComponentKind.has_value(config["kind"]):
        raise ValueError(f"Invalid component kind {config['kind']}")

    kind = ComponentKind(config["kind"])
    interface = ComponentKind.interface(kind)

    module = sys.modules[config["module"]]

    if not hasattr(module, config["name"]):
        raise AttributeError(
            f"Unable to find implementation {config['name']} in module {config['module']}"
        )

    target_class: Type[Any] = getattr(module, config["name"])

    # Verify that the implementation class matches the interface we got from
    # the `kind:` hint.
    if not issubclass(target_class, interface):
        raise TypeError(
            f"Class {target_class} does not implement {interface}, requested by {config}"
        )

    component = target_class.__call__(uid=config["uuid"], **config["properties"])

    # Verify the instance implements a valid interface.
    # The second call is to reassure the linter that the types are correct.
    assert isinstance(component, interface), assert_message(component, interface)
    assert isinstance(
        component,
        (
            IOConfigInterface,
            BehaviourInterface,
            TriggerInterface,
            ConditionInterface,
            ActionInterface,
        ),
    )

    return component
