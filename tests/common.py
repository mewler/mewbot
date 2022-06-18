from __future__ import annotations

from typing import Generic, Optional, Type, TypeVar

from abc import ABC

import yaml

from mewbot.loader import load_component
from mewbot.core import Component
from mewbot.config import ConfigBlock


T_co = TypeVar("T_co", bound=Component, covariant=True)


class BaseTestClassWithConfig(ABC, Generic[T_co]):
    config_file: str
    implementation: Type[T_co]
    _config: Optional[ConfigBlock] = None
    _component: Optional[T_co] = None

    @property
    def config(self) -> ConfigBlock:
        """Returns the YAML-defined config the"""

        if not self._config:
            impl = self.implementation.__module__ + "." + self.implementation.__name__

            with open(self.config_file, "r", encoding="utf-8") as config:
                self._config = next(
                    document
                    for document in yaml.load_all(config, Loader=yaml.CSafeLoader)
                    if document["implementation"] == impl
                )

        return self._config

    @property
    def component(self) -> T_co:
        """Returns the component loaded from the config block"""

        if not self._component:
            component = load_component(self.config)
            assert isinstance(component, self.implementation), "Config loaded incorrect type"
            self._component = component

        return self._component
