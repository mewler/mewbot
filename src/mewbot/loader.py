from __future__ import annotations

import importlib
import sys
from typing import Type, Any

from mewbot.core import ComponentKind
from mewbot.component import ConfigBlock, Component, ComponentRegistry


def load_component_from_yaml(config: ConfigBlock) -> Component:
    required_keys = ConfigBlock.__annotations__.keys()  # pylint: disable=no-member

    if set(config.keys()) != set(required_keys):
        raise ValueError("Invalid configuration keys")

    if not ComponentKind.has_value(config["kind"]):
        raise ValueError(f"Invalid component kind {config['kind']}")

    kind = ComponentKind(config["kind"])

    if not ComponentRegistry.has_api_version(kind, config["apiVersion"]):
        raise TypeError(
            f"API Version {config['apiVersion']} for {config['kind']} not registered"
        )

    if config["module"] not in sys.modules:
        importlib.import_module(config["module"])

    module = sys.modules[config["module"]]

    if not hasattr(module, config["name"]):
        raise Exception(f"Unable to find {config['name']} in {config['module']}")

    target_class: Type[Any] = getattr(module, config["name"])

    if not issubclass(target_class, Component):
        raise Exception("Trying to load a non-registered class from config")

    component = target_class.__call__(uid=config["uuid"], **config["properties"])

    assert isinstance(component, Component)

    return component
