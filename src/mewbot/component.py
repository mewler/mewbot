#!/usr/bin/env python3

from __future__ import annotations

from typing import Any, Dict, Type, TypedDict

import importlib
import sys
import uuid

from mewbot.registry import Registry


class ConfigBlock(TypedDict):
    api: str
    kind: str
    uuid: str
    properties: Dict[str, Any]


def load_from_config(config: ConfigBlock) -> Component:
    if set(config.keys()) != {"api", "uuid", "kind", "properties"}:
        raise Exception("Invalid configuration keys")

    if config["api"] not in sys.modules:
        importlib.import_module(config["api"])

    module = sys.modules[config["api"]]

    if not hasattr(module, config["kind"]):
        raise Exception(f"Unable to find {config['kind']} in {config['api']}")

    target_class: Type[Any] = getattr(module, config["kind"])

    if not issubclass(target_class, Component):
        raise Exception("Trying to load a non-registered class from config")

    return target_class(id=config["uuid"], **config["properties"])


class Component(metaclass=Registry):
    """Hello!"""

    def __new__(cls, **properties: Any) -> Component:
        if not issubclass(cls, Component):
            raise Exception("Attempting to create a non registerable class")

        obj: Component = super(Component, cls).__new__(cls)

        _dir = dir(cls)

        for prop, value in properties.items():
            if hasattr(_dir, prop):
                raise Exception(f"No such property {prop} on {cls}")

            if not isinstance(getattr(cls, prop), property):
                raise Exception(f"Property {prop} on {cls} is not a @property")

            if getattr(cls, prop).fset:
                setattr(obj, prop, value)

        if "uuid" in properties:
            obj.uuid = properties["uuid"]
        else:
            obj.uuid = uuid.uuid4().hex

        return obj

    def serialise(self) -> ConfigBlock:
        cls = type(self)

        output: ConfigBlock = {
            "api": cls.__module__,
            "kind": cls.__name__,
            "uuid": self.uuid,
            "properties": {},
        }

        for prop in dir(cls):
            if not isinstance(getattr(cls, prop), property):
                continue

            if getattr(cls, prop).fset:
                output["properties"][prop] = getattr(self, prop)

        return output

    @property
    def uuid(self) -> str:
        return self._id

    @uuid.setter
    def uuid(self, _id: str) -> None:
        if hasattr(self, "_id"):
            raise Exception("Can not set the ID of a component outside of creation")

        self._id = _id

    def __init__(self, **k: Any) -> None:
        pass
