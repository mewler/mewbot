#!/usr/bin/env python3

from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Type, TypedDict

import abc

# import inspect
import uuid

from mewbot.core import ComponentKind


class ConfigBlock(TypedDict):
    kind: str
    apiVersion: str
    module: str
    name: str
    uuid: str
    properties: Dict[str, Any]


class BehaviourConfigBlock(ConfigBlock):
    triggers: List[ConfigBlock]
    conditions: List[ConfigBlock]
    actions: List[ConfigBlock]


# noinspection PyMethodParameters
class ComponentRegistry(abc.ABCMeta):
    registered: List[Type[Any]] = []

    _api_versions: Dict[ComponentKind, Dict[str, Type[Component]]] = {}

    def __new__(cls, name: str, bases: Any, namespace: Any, **k: Any) -> Type[Any]:
        created_type: Type[Any] = super().__new__(cls, name, bases, namespace, **k)

        if created_type.__module__ == cls.__module__:
            return created_type

        if not issubclass(created_type, Component):
            raise TypeError(
                f"ComponentRegistry can not be used with "
                f"non-Component class {created_type.__module__}.{created_type.__name__}"
            )

        api_bases = list(cls._detect_api_versions(created_type))

        if len(api_bases) > 1:
            raise TypeError(
                f"Class {created_type.__module__}.{created_type.__name__} inherits from two APIs"
            )

        # if not inspect.isabstract(created_type) and not api_bases:
        #     raise TypeError(
        #         f"Non-abstract class {created_type.__module__}.{created_type.__name__} "
        #         f"must inherit from an API base"
        #     )

        # if not created_type.__doc__:
        #    raise Exception(f"No docs? No service! ({name})")

        ComponentRegistry.registered.append(created_type)
        return created_type

    def __call__(  # type: ignore
        cls: Type[Component], *args: Any, uid: Optional[str] = None, **properties: Any
    ) -> Any:
        if cls not in ComponentRegistry.registered:
            raise Exception("Attempting to create a non registrable class")

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

            # if not inspect.isabstract(api):
            #     raise TypeError("Can not register an API version from a non-abstract class")

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
    def has_api_version(cls, kind: ComponentKind, version: str) -> bool:
        return version in cls._api_versions.get(kind, {})

    @classmethod
    def _detect_api_versions(
        cls, impl: Type[Component]
    ) -> Iterable[Tuple[ComponentKind, str]]:
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


class Component(metaclass=ComponentRegistry):
    """Hello!"""

    _id: str

    def serialise(self) -> ConfigBlock:
        cls = type(self)

        api = ComponentRegistry.api_version(self)

        output: ConfigBlock = {
            "kind": api[0],
            "apiVersion": api[1],
            "module": cls.__module__,
            "name": cls.__name__,
            "uuid": self.uuid,
            "properties": {},
        }

        for prop in dir(cls):
            if not isinstance(getattr(cls, prop), property):
                continue

            if prop == "uuid":
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
