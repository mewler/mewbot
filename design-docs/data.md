# Data Storage

A lot of bot functionality relies on persistent or external data;
even the most basic call-and-response command may want to have a
way to easily edit the response.
The objects of the type `DataSource` and `DataStore` offer persistent
storage outside of a bot's primary configuration.

## DataSource

`DataSource`s are read-only sources of data that can be used by `Triggers`,
`Conditions`, and `Actions` to provide configuration values that are not
stored as part of the configuration.

```python
class DataSource(Generic[T]):
  """A source of data for use in behaviours.
  A data source can contains any number of items with a common primitive type.

  The source can be accessed as if it is an array, dictionary, or single value;
  each subclass must support one of these, but may support any combination
  thereof.
  """

  get(self) -> T:
    """Returns an item in this Source. The source can choose if this is the
    first item, a random item, or the next in the iteration of this source (or
    any other semantics that make sense for the source). This function may
    raise an IOException if there is a problem communicating with the backing
    store for this source, or a DataSourceEmpty exception if there is no data
    to return."""

  __len__(self) -> int:
    """Returns the number of items in this DataStore.

	This may return -1 to indicte that the length is unknown, otherwise it
	should return an a usable value that matches the length of .keys()
	(for sources that work like dictionary) or the maximum slice value
	(for sources that work like a sequence)."""

  __getitem__(self, key: Union[int, str]) -> T:
    """Allows access to a value in this DataStore via a key.
	If key is of an inappropriate type, TypeError may be raised;
	this includes if this source is a single value.
	If the value is outside the index range, IndexError should be raised.
	For mapping types, if key is missing (not in the container),
	KeyError should be raised."""

  keys() -> Sequence[str]:
  	"""All the keys for a dictionary accessed source."""

  random() -> T:
    """Gets a random item from this source."""
```

## DataStore

A `DataStore` extends a `DataSource` by allowing the bot to add, update,
replace, or delete data at runtime. This allows the bot to have 'memory'.

All records in a `DataStore` have associated metadata, including a
moderation status, an updated timestamp, and information on where the
value was created from.

Functions which are inherited from `DataSource` will not return the metadata
in order to maintain compatibility. They must not return records in the
REJECTED moderation state, and the store may choose to also exclude pending
items from these functions.

```python
enum DataModerationState:
	APPROVED =  1
	PENDING  =  0
	REJECTED = -1


class DataRecord(Generic[T]):
	value: T
	created: datetime.datetime
	status: DataModerationState
	source: str


class DataStore(Generic[T], DataSource[T]):
	
