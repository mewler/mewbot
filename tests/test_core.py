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
    @staticmethod
    def test_componentkind_interface_map_behaviour() -> None:
        assert (
            ComponentKind.interface(ComponentKind(ComponentKind.Behaviour))
            == BehaviourInterface
        )

    @staticmethod
    def test_componentkind_interface_map_trigger() -> None:
        assert (
            ComponentKind.interface(ComponentKind(ComponentKind.Trigger)) == TriggerInterface
        )

    @staticmethod
    def test_componentkind_interface_map_condition() -> None:
        assert (
            ComponentKind.interface(ComponentKind(ComponentKind.Condition))
            == ConditionInterface
        )

    @staticmethod
    def test_componentkind_interface_map_action() -> None:
        assert ComponentKind.interface(ComponentKind(ComponentKind.Action)) == ActionInterface

    @staticmethod
    def test_componentkind_interface_map_ioconfig() -> None:
        assert (
            ComponentKind.interface(ComponentKind(ComponentKind.IOConfig))
            == IOConfigInterface
        )

    @staticmethod
    def test_componentkind_interface_map_datasource() -> None:
        with pytest.raises(ValueError):  # @UndefinedVariable
            _ = ComponentKind.interface(ComponentKind(ComponentKind.DataSource))

    @staticmethod
    def test_componentkind_interface_map_template() -> None:
        with pytest.raises(ValueError):  # @UndefinedVariable
            _ = ComponentKind.interface(ComponentKind(ComponentKind.Template))
