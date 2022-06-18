# Unified test of http and socket parts of mewbot.io
# Loads a file in, sees if it works, and then probes the socket and http class.

from __future__ import annotations

import copy

from tests.common import ExampleHttpPostIOConfig

from mewbot.core import Component
from mewbot.io.http import HTTPServlet
from mewbot.io.socket import SocketIO
from mewbot.api.v1 import IOConfig

# pylint: disable=R0903
#  Disable "too few public methods" for test cases - most test files will be classes used for
#  grouping and then individual tests alongside these
# pylint: disable=R0201
#  Disable "no self use" for functions. These functions will not be used internally as they are
#  automatically called by pytest as it seeks and searches for tests.


class TestIoHttpsPost(ExampleHttpPostIOConfig):
    def test_check_class(self) -> None:
        self.cache_component()
        assert isinstance(self.component, HTTPServlet)
        assert isinstance(self.component, SocketIO)
        assert isinstance(self.component, IOConfig)
        assert isinstance(self.component, Component)

    def test_check_setget(self) -> None:
        self.cache_component()
        # Check each set and get
        temp_component = copy.deepcopy(self.component)

        new_host = "nullfailtouse"
        temp_component.host = new_host
        assert temp_component.host == new_host
        new_port = 0
        temp_component.port = new_port
        assert temp_component.port == new_port
