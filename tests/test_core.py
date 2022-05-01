from __future__ import annotations

import pytest

from mewbot.core import (
    ComponentKind,
    BehaviourInterface,
    TriggerInterface,
    ConditionInterface,
    ActionInterface,
    IOConfigInterface,
)

# pragma pylint: disable=R0903
#  Disable "too few public methods" for test cases - most test files will be classes used for
#  grouping and then individual tests alongside these
# pragma pylint: disable=R0201
#  Disable "no self use" for functions. These functions will not be used internally as they are
#  automatically called by pytest as it seeks and searches for tests.


class TestComponent:
    def test_hasvalue(self) -> None:
        assert ComponentKind.has_value(ComponentKind.BEHAVIOUR)

    def test_hasvalue_notnull(self) -> None:
        assert ~ComponentKind.has_value("NULL")

    # Test a set of what interface passing succeeds and fails
    def test_componentkind_interface_map_behaviour(self) -> None:
        assert (
            ComponentKind.interface(ComponentKind(ComponentKind.BEHAVIOUR))
            == BehaviourInterface
        )

    def test_componentkind_interface_map_trigger(self) -> None:
        assert (
            ComponentKind.interface(ComponentKind(ComponentKind.TRIGGER)) == TriggerInterface
        )

    def test_componentkind_interface_map_condition(self) -> None:
        assert (
            ComponentKind.interface(ComponentKind(ComponentKind.CONDITION))
            == ConditionInterface
        )

    def test_componentkind_interface_map_action(self) -> None:
        assert ComponentKind.interface(ComponentKind(ComponentKind.ACTION)) == ActionInterface

    def test_componentkind_interface_map_ioconfig(self) -> None:
        assert (
            ComponentKind.interface(ComponentKind(ComponentKind.IO_CONFIG))
            == IOConfigInterface
        )

    def test_componentkind_interface_map_datasource(self) -> None:
        with pytest.raises(ValueError):  # @UndefinedVariable
            _ = ComponentKind.interface(ComponentKind(ComponentKind.DATASOURCE))

    def test_componentkind_interface_map_template(self) -> None:
        with pytest.raises(ValueError):  # @UndefinedVariable
            _ = ComponentKind.interface(ComponentKind(ComponentKind.TEMPLATE))
