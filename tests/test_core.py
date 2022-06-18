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


class TestComponent:
    # Test a set of what interface passing succeeds and fails
    def test_componentkind_interface_map_behaviour(self) -> None:
        assert (
            ComponentKind.interface(ComponentKind(ComponentKind.Behaviour))
            == BehaviourInterface
        )

    def test_componentkind_interface_map_trigger(self) -> None:
        assert (
            ComponentKind.interface(ComponentKind(ComponentKind.Trigger)) == TriggerInterface
        )

    def test_componentkind_interface_map_condition(self) -> None:
        assert (
            ComponentKind.interface(ComponentKind(ComponentKind.Condition))
            == ConditionInterface
        )

    def test_componentkind_interface_map_action(self) -> None:
        assert ComponentKind.interface(ComponentKind(ComponentKind.Action)) == ActionInterface

    def test_componentkind_interface_map_ioconfig(self) -> None:
        assert (
            ComponentKind.interface(ComponentKind(ComponentKind.IOConfig))
            == IOConfigInterface
        )

    def test_componentkind_interface_map_datasource(self) -> None:
        with pytest.raises(ValueError):  # @UndefinedVariable
            _ = ComponentKind.interface(ComponentKind(ComponentKind.DataSource))

    def test_componentkind_interface_map_template(self) -> None:
        with pytest.raises(ValueError):  # @UndefinedVariable
            _ = ComponentKind.interface(ComponentKind(ComponentKind.Template))
