from __future__ import annotations

from abc import ABC

import yaml

from mewbot.loader import load_component
from mewbot.core import ComponentKind
from mewbot.component import ConfigBlock
from mewbot.io.http import HTTPServlet


class BaseTestClassWithConfig(ABC):
    # pylint: disable=R0903
    # Too few public methods, because this is always used elsewhere
    fname: str
    config: ConfigBlock
    doctype: ComponentKind
    config_toload = True

    def cache_config(self) -> None:
        if self.config_toload:
            with open(self.fname, "r", encoding="utf-8") as config:
                for document in yaml.load_all(config, Loader=yaml.CSafeLoader):
                    if document["kind"] == self.doctype:
                        self.config = document
                        self.config_toload = False


class ExampleHttpPostIOConfig(BaseTestClassWithConfig):
    fname = "examples/trivial_http_post.yaml"
    doctype = ComponentKind.IO_CONFIG
    config: ConfigBlock
    component_toload = True
    component: HTTPServlet

    def cache_component(self) -> None:
        if self.component_toload:
            self.cache_config()
            this_component = load_component(self.config)
            assert isinstance(this_component, HTTPServlet)
            self.component = this_component
            self.component_toload = False
