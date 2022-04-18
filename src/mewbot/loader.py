#!/use/bin/env python3

from __future__ import annotations

from typing import Type, Any, TextIO

import importlib
import sys
import yaml

from mewbot.bot import Bot
from mewbot.core import (
    ComponentKind,
    IOConfigInterface,
    BehaviourInterface,
    TriggerInterface,
    ConditionInterface,
    ActionInterface,
)
from mewbot.component import (
    ConfigBlock,
    BehaviourConfigBlock,
    Component,
    ComponentRegistry,
)

_REQUIRED_KEYS = set(ConfigBlock.__annotations__.keys())  # pylint: disable=no-member


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
            assert isinstance(component, IOConfigInterface)
            bot.add_io_config(component)

    return bot


def load_behaviour(config: BehaviourConfigBlock) -> BehaviourInterface:
    behaviour = load_component(config)

    assert isinstance(behaviour, BehaviourInterface)

    for trigger_definition in config["triggers"]:
        trigger = load_component(trigger_definition)
        assert isinstance(trigger, TriggerInterface)
        behaviour.add(trigger)

    for condition_definition in config["conditions"]:
        condition = load_component(condition_definition)
        assert isinstance(condition, ConditionInterface)
        behaviour.add(condition)

    for action_definition in config["actions"]:
        action = load_component(action_definition)
        assert isinstance(action, ActionInterface)
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


    module = sys.modules[config["module"]]

    if not hasattr(module, config["name"]):
        raise Exception(f"Unable to find {config['name']} in {config['module']}")

    target_class: Type[Any] = getattr(module, config["name"])

    if not issubclass(target_class, Component):
        raise Exception("Trying to load a non-registered class from config")

    component = target_class.__call__(uid=config["uuid"], **config["properties"])

    assert isinstance(component, Component)

    return component
