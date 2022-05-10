#!/usr/bin/env python3

"""Tooling for recording the creation of implementation classes, allowing
for lists """

from __future__ import annotations

from typing import List, Type, Any, Dict, Optional, Callable, Iterable, Tuple

import abc
import uuid

from mewbot.core import ComponentKind, Component


# noinspection PyMethodParameters
class ComponentRegistry(abc.ABCMeta):
    """MetaType which reg"""

    registered: List[Type[Any]] = []

    _api_versions: Dict[ComponentKind, Dict[str, Type[Component]]] = {}

    def __new__(cls, name: str, bases: Any, namespace: Any, **k: Any) -> Type[Any]:
        created_type: Type[Any] = super().__new__(cls, name, bases, namespace, **k)

        if created_type.__module__ == cls.__module__:
            return created_type

        api_bases = list(cls._detect_api_versions(created_type))

        if len(api_bases) > 1:
            raise TypeError(
                f"Class {created_type.__module__}.{created_type.__name__} inherits from two APIs"
            )

        ComponentRegistry.registered.append(created_type)
        return created_type

    def __call__(  # type: ignore
        cls: Type[Component], *args: Any, uid: Optional[str] = None, **properties: Any
    ) -> Any:
        if cls not in ComponentRegistry.registered:
            raise TypeError("Attempting to create a non registrable class")

        obj: Any = cls.__new__(cls)  # pylint: disable=no-value-for-parameter
        obj.uuid = uid if uid else uuid.uuid4().hex

        _dir = dir(cls)
        to_delete = []

        for prop, value in properties.items():
            if prop not in _dir:
                continue

            if not isinstance(getattr(cls, prop), property):
                continue

            if getattr(cls, prop).fset:
                setattr(obj, prop, value)
                to_delete.append(prop)

        for prop in to_delete:
            properties.pop(prop)

        obj.__init__(*args, **properties)

        return obj

    @classmethod
    def register_api_version(
        cls, kind: ComponentKind, version: str
    ) -> Callable[[Type[Component]], Type[Component]]:
        def do_register(api: Type[Component]) -> Type[Component]:
            if api not in cls.registered:
                raise TypeError("Can not register an API version from a non-registered class")

            if not isinstance(kind, ComponentKind):
                raise TypeError(
                    f"Component kind '{kind}' not valid (must be one of {ComponentKind.values()})"
                )

            if not issubclass(api, ComponentKind.interface(kind)):
                raise TypeError(f"{api} does not meet the contract of a {kind.value}")

            kind_apis = cls._api_versions.setdefault(kind, {})

            if version in kind_apis:
                raise ValueError(
                    f"Can not register {api} as API version {version} for {kind.value}; "
                    f"already registered by {kind_apis[version]}"
                )

            kind_apis[version] = api

            return api

        return do_register

    @classmethod
    def _detect_api_versions(cls, impl: Type[Any]) -> Iterable[Tuple[ComponentKind, str]]:
        for kind, apis in cls._api_versions.items():
            for version, api in apis.items():
                if issubclass(impl, api):
                    yield kind, version

    @classmethod
    def api_version(cls, component: Component) -> Tuple[ComponentKind, str]:
        for val in cls._detect_api_versions(type(component)):
            return val

        raise ValueError(f"No API version for {component}")

    @classmethod
    def registered_classes(
        cls, implements: ComponentKind, version: Optional[str]
    ) -> Iterable[Type[Component]]:
        pass
