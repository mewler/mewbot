# Unified test of http and socket parts of mewbot.io
# Loads a file in, sees if it works, and then probes the socket and http class.

from __future__ import annotations

import pytest

import copy
import yaml

from mewbot.loader import  (
    load_component
    )

from mewbot.core import (
    ComponentKind,
    IOConfigInterface
    )
from mewbot.component import (
    ConfigBlock,
    Component
)
from mewbot.io.http import HTTPServlet
from mewbot.io.socket import SocketIO
from mewbot.api.v1 import IOConfig

class Test_io_https_post:
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
            
    def test_check_class(self):
        self.cache_component()
        assert (isinstance(self.component, HTTPServlet))
        assert (isinstance(self.component, SocketIO))
        assert (isinstance(self.component, IOConfig))
        assert (isinstance(self.component, Component))
        
    def test_check_setget(self):
        self.cache_component()
        # Check each set and get
        temp_component = copy.deepcopy(self.component)
        
        new_host = 'nullfailtouse'
        temp_component._host = new_host
        assert(temp_component.host == new_host)
        new_port = 0
        temp_component._port = new_port
        assert(temp_component.port == new_port)
    