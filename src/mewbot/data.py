#!/usr/bin/env python3

from __future__ import annotations

from typing import Union, Generic, Sequence, TypeVar

import dataclasses
import datetime
import enum

DataType = TypeVar("DataType")


class DataSource(Generic[DataType]):
    """A source of data for use in behaviours.
    A data source can contains any number of items with a common primitive type.

    The source can be accessed as if it is an array, dictionary, or single value;
    each subclass must support one of these, but may support any combination
    thereof.
    """

    def get(self) -> DataType:
        """Returns an item in this Source. The source can choose if this is the
        first item, a random item, or the next in the iteration of this source (or
        any other semantics that make sense for the source). This function may
        raise an IOException if there is a problem communicating with the backing
        store for this source, or a DataSourceEmpty exception if there is no data
        to return."""

    def __len__(self) -> int:
        """Returns the number of items in this DataStore.

        This may return -1 to indicte that the length is unknown, otherwise it
        should return an a usable value that matches the length of .keys()
        (for sources that work like dictionary) or the maximum slice value
        (for sources that work like a sequence)."""

    def __getitem__(self, key: Union[int, str]) -> DataType:
        """Allows access to a value in this DataStore via a key.
        If key is of an inappropriate type, TypeError may be raised;
        this includes if this source is a single value.
        If the value is outside the index range, IndexError should be raised.
        For mapping types, if key is missing (not in the container),
        KeyError should be raised."""

    def keys(self) -> Sequence[str]:
        """All the keys for a dictionary accessed source."""

    def random(self) -> DataType:
        """Gets a random item from this source."""


class DataModerationState(enum.IntEnum):
    APPROVED = 1
    PENDING = 0
    REJECTED = -1


@dataclasses.dataclass
class DataRecord(Generic[DataType]):
    value: DataType
    created: datetime.datetime
    status: DataModerationState
    source: str


class DataStore(Generic[DataType], DataSource[DataRecord[DataType]]):
    pass
