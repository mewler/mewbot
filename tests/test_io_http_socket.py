# Unified test of http and socket parts of mewbot.io
# Loads a file in, sees if it works, and then probes the socket and http class.

from __future__ import annotations

from typing import Type

import copy

from tests.common import BaseTestClassWithConfig

from mewbot.io.http import HTTPServlet
from mewbot.io.socket import SocketIO
from mewbot.api.v1 import IOConfig

# pylint: disable=R0903
#  Disable "too few public methods" for test cases - most test files will be classes used for
#  grouping and then individual tests alongside these


class TestIoHttpsPost(BaseTestClassWithConfig[HTTPServlet]):
    config_file: str = "examples/trivial_http_post.yaml"
    implementation: Type[HTTPServlet] = HTTPServlet

    def test_check_class(self) -> None:
        assert isinstance(self.component, HTTPServlet)
        assert isinstance(self.component, SocketIO)
        assert isinstance(self.component, IOConfig)

    def test_check_setget(self) -> None:
        # Check each set and get
        temp_component = copy.deepcopy(self.component)

        new_host = "nullfailtouse"
        temp_component.host = new_host
        assert temp_component.host == new_host

        new_port = 0
        temp_component.port = new_port
        assert temp_component.port == new_port
