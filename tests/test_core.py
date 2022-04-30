from __future__ import annotations

import pytest

from mewbot.core import (
    ComponentKind,
    BehaviourInterface,
    TriggerInterface,
    ConditionInterface,
    ActionInterface,
    IOConfigInterface
)

class Test_component:
    def test_hasvalue(self):
        assert (ComponentKind.has_value(ComponentKind.BEHAVIOUR))
    def test_hasvalue_notnull(self):
        assert (~ComponentKind.has_value("NULL"))
        
    # Test a set of what interface passing succeeds and fails
    def test_componentkind_interface_map_behaviour(self):
        assert (ComponentKind.interface(ComponentKind(ComponentKind.BEHAVIOUR)) == BehaviourInterface)
    def test_componentkind_interface_map_trigger(self):
        assert (ComponentKind.interface(ComponentKind(ComponentKind.TRIGGER)) == TriggerInterface)
    def test_componentkind_interface_map_condition(self):
        assert (ComponentKind.interface(ComponentKind(ComponentKind.CONDITION)) == ConditionInterface)
    def test_componentkind_interface_map_action(self):
        assert (ComponentKind.interface(ComponentKind(ComponentKind.ACTION)) == ActionInterface)
    def test_componentkind_interface_map_ioconfig(self):
        assert (ComponentKind.interface(ComponentKind(ComponentKind.IO_CONFIG)) == IOConfigInterface)
        
    def test_componentkind_interface_map_datasource(self):
        with pytest.raises(ValueError): # @UndefinedVariable
            _ = ComponentKind.interface(ComponentKind(ComponentKind.DATASOURCE))
    def test_componentkind_interface_map_template(self):
        with pytest.raises(ValueError): # @UndefinedVariable
            _ = ComponentKind.interface(ComponentKind(ComponentKind.TEMPLATE))