from __future__ import annotations

import copy
import pytest

from tests.common import BaseTestClassWithConfig, ExampleHttpPostIOConfig

from mewbot.loader import configure_bot, load_behaviour, load_component

from mewbot.bot import Bot
from mewbot.core import ComponentKind, BehaviourInterface, Component
from mewbot.config import ConfigBlock, BehaviourConfigBlock
from mewbot.io.http import HTTPServlet
from mewbot.io.socket import SocketIO
from mewbot.api.v1 import IOConfig

# pylint: disable=R0903
#  Disable "too few public methods" for test cases - most test files will be classes used for
#  grouping and then individual tests alongside these
# pylint: disable=R0201
#  Disable "no self use" for functions. These functions will not be used internally as they are
#  automatically called by pytest as it seeks and searches for tests.


# Tester for mewbot.loader.load_component
class TestLoaderHttpsPost(ExampleHttpPostIOConfig):
    # Test this working
    def test_working(self) -> None:
        self.cache_config()
        component = load_component(self.config)
        assert isinstance(component, IOConfig)

    # Test that the loading is accurate
    def test_loading_component_type(self) -> None:
        self.cache_component()
        assert isinstance(self.component, HTTPServlet)

    def test_loading_component_supertype(self) -> None:
        self.cache_component()
        assert isinstance(self.component, SocketIO)
        assert isinstance(self.component, IOConfig)

    def test_loading_component_values(self) -> None:
        # Protected access overriden here to inspect variables ONLY
        self.cache_component()
        assert self.component._host == "localhost"  # pylint: disable="protected-access"
        assert self.component._port == 12345  # pylint: disable="protected-access"

    # Tests that expose errors
    def test_erroring_kind(self) -> None:
        self.cache_config()
        # Change the kind of this config, to break it
        this_config = copy.deepcopy(self.config)
        this_config["kind"] = "NULL"
        with pytest.raises(ValueError):  # @UndefinedVariable
            _ = load_component(this_config)

    def test_erroring_apiver(self) -> None:
        self.cache_config()
        # Change the kind of this config, to break it
        this_config = copy.deepcopy(self.config)
        this_config["apiVersion"] = "v0"
        with pytest.raises(TypeError):  # @UndefinedVariable
            _ = load_component(this_config)


class TestLoader:
    def test_bad_config(self) -> None:
        # Build a bad config and give it to the bot
        this_config = ConfigBlock()  # type: ignore
        this_config["kind"] = "NULL"
        with pytest.raises(ValueError):  # @UndefinedVariable
            _ = load_component(this_config)


# Test for mewbot.loader.load_behaviour
class TestLoaderBehaviourHttpPost(BaseTestClassWithConfig):
    fname = "examples/trivial_http_post.yaml"
    doctype = ComponentKind.BEHAVIOUR
    config: BehaviourConfigBlock
    component_toload = True
    component: BehaviourInterface

    def cache_component(self) -> None:
        if self.component_toload:
            self.cache_config()
            self.component = load_behaviour(self.config)
            self.component_toload = False

    # Test this working
    def test_working(self) -> None:
        self.cache_config()
        component = load_behaviour(self.config)
        assert isinstance(component, BehaviourInterface)


class TestLoaderConfigureBot:
    fname = "examples/trivial_http_post.yaml"
    component_toload = True
    component: Bot

    def cache_bot(self) -> None:
        if self.component_toload:
            with open(self.fname, "r", encoding="utf-8") as config_file:
                self.component = configure_bot("bot", config_file)
                self.component_toload = False

    # Test this working
    def test_working(self) -> None:
        self.cache_bot()
        assert isinstance(self.component, Bot)
