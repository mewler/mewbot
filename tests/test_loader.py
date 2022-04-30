
from __future__ import annotations

import pytest

import yaml
import copy

from mewbot.loader import  (
    configure_bot,
    load_behaviour,
    load_component
    )

from mewbot.bot import (
    Bot
)
from mewbot.core import (
    ComponentKind,
    BehaviourInterface,
    IOConfigInterface
    )
from mewbot.component import (
    ConfigBlock,
    Component
)
from mewbot.io.http import HTTPServlet
from mewbot.io.socket import SocketIO
from mewbot.api.v1 import IOConfig


#Tester for mewbot.loader.load_component
class Test_loader_https_post:
    fname = 'examples/trivial_http_post.yaml'
    config_toload = True
    config : IOConfigInterface
    component_toload = True
    component : Component

    # Prereq;
    def cache_config(self):
        if self.config_toload:
            with open(self.fname, "r", encoding="utf-8") as config:
                for document in yaml.load_all(config, Loader=yaml.CSafeLoader):
                    if document["kind"] == ComponentKind.IO_CONFIG:
                        self.config = document
                        self.config_toload = False
    
    def cache_component(self):
        if self.component_toload:
            self.cache_config()
            self.component = load_component(self.config)
            self.component_toload = False


    # Test this working
    def test_working(self):
        self.cache_config()
        component = load_component(self.config)
        assert (isinstance(component, Component))
        
    # Test that the loading is accurate
    def test_loading_component_type(self):
        self.cache_component()
        assert (isinstance(self.component, HTTPServlet))
    def test_loading_component_supertype(self):
        self.cache_component()
        assert (isinstance(self.component, SocketIO))
        assert (isinstance(self.component, IOConfig))
    def test_loading_component_values(self):
        self.cache_component()
        assert (self.component._host == "localhost")
        assert (self.component._port == 12345)
        
    # Tests that expose errors
    def test_erroring_kind(self):
        self.cache_config()
        # Change the kind of this config, to break it
        this_config = copy.deepcopy(self.config)
        this_config["kind"] = "NULL"
        with pytest.raises(ValueError):  # @UndefinedVariable
            _ = load_component(this_config)
    def test_erroring_apiver(self):
        self.cache_config()
        # Change the kind of this config, to break it
        this_config = copy.deepcopy(self.config)
        this_config["apiVersion"] = "v0"
        with pytest.raises(TypeError):  # @UndefinedVariable
            _ = load_component(this_config)
            
class Test_loader:
    def test_bad_config(self):
        # Build a bad config and give it to the bot
        this_config = ConfigBlock()
        this_config["kind"] = "NULL"
        with pytest.raises(ValueError):  # @UndefinedVariable
            _ = load_component(this_config)
            
# Test for mewbot.loader.load_behaviour
class Test_loader_behaviour_http_post:
    fname = 'examples/trivial_http_post.yaml'
    config_toload = True
    config : IOConfigInterface
    component_toload = True
    component : Component
    
    def cache_config(self):
        if self.config_toload:
            with open(self.fname, "r", encoding="utf-8") as config:
                for document in yaml.load_all(config, Loader=yaml.CSafeLoader):
                    if document["kind"] == ComponentKind.BEHAVIOUR:
                        self.config = document
                        self.config_toload = False
    
    def cache_component(self):
        if self.component_toload:
            self.cache_config()
            self.component = load_behaviour(self.config)
            self.component_toload = False
            
    # Test this working
    def test_working(self):
        self.cache_config()
        component = load_behaviour(self.config)
        assert (isinstance(component, BehaviourInterface))
       
    # TODO: does this load_behaviour actually work?
        
class Test_loader_configure_bot:
    fname = 'examples/trivial_http_post.yaml'
    component_toload = True
    component : Component
    
    def cache_bot(self):
        if self.component_toload:
            with open(self.fname, "r", encoding="utf-8") as config_file:
                self.component = configure_bot("bot",config_file)
                self.component_toload = False
            
    # Test this working
    def test_working(self):
        self.cache_bot()
        assert (isinstance(self.component, Bot))