
from __future__ import annotations

import pytest

import yaml
import copy

from mewbot.loader import  (
    load_component
    )
from mewbot.component import (
    ConfigBlock
)
from mewbot.core import (
    ComponentKind,
    BehaviourInterface,
    IOConfigInterface
)

# Experimentation with Pytest
# Looking at the way pytest works and how it does it's thing.

#Tester for mewbot.loader.load_component
# Doesn't work - the file path doesn't work :(
class Test_loader_https_post:
    fname = 'examples/trivial_http_post.yaml'
    config : IOConfigInterface

    # Prereq;
    def setup(self):
        with open(self.fname, "r", encoding="utf-8") as config:
            for document in yaml.load_all(config, Loader=yaml.CSafeLoader):
                if document["kind"] == ComponentKind.IO_CONFIG:
                    self.config = document

    # Test this working
    def test_one(self):
        self.setup()
        # Change the kind of this config, to break it
        this_config = copy.deepcopy(self.config)
        this_config["kind"] = "NULL"
        with pytest.raises(ValueError):  # @UndefinedVariable
            component = load_component(this_config)
            
            
class Test_loader:
    def test_one(self):
        # Build a bad config and give it to the bot
        this_config = ConfigBlock()
        this_config["kind"] = "NULL"
        with pytest.raises(ValueError):  # @UndefinedVariable
            _ = load_component(this_config)
            
class Test_core:
    def test_value(self):
        assert (ComponentKind.has_value(ComponentKind.BEHAVIOUR))
    def test_value2(self):
        assert (~ComponentKind.has_value("NULL"))
    def test_value3(self):
        assert (ComponentKind.interface(ComponentKind(ComponentKind.BEHAVIOUR)) == BehaviourInterface)
    def test_value4(self):
        with pytest.raises(ValueError): # @UndefinedVariable
            _ = ComponentKind.interface(ComponentKind(ComponentKind.DATASOURCE))