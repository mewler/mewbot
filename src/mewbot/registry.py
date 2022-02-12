#!/usr/bin/env python3

from __future__ import annotations

from typing import Type, Any, List, Generator

import abc
import inspect


class Registry(abc.ABCMeta):
    registered: List[Type[Any]] = []
    mi_limits: List[Type[Any]] = []

    def __new__(cls, name: str, bases: Any, namespace: Any, **k: Any) -> Type[Any]:
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


def limit_multi_inheritence(cls: Type[Any]) -> Type[Any]:
    Registry.mi_limits.append(cls)
    return cls
