#!/usr/bin/env python3

"""Module that contains the Python schema for the YAML configuration"""

from __future__ import annotations

from typing import TypedDict, Dict, Any, List


class ConfigBlock(TypedDict):
    """Common YAML Block for all components"""

    kind: str
    implementation: str
    uuid: str
    properties: Dict[str, Any]


class BehaviourConfigBlock(ConfigBlock):
    """YAML block for a behaviour, which includes the subcomponents"""

    triggers: List[ConfigBlock]
    conditions: List[ConfigBlock]
    actions: List[ConfigBlock]
