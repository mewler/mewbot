<!--
SPDX-FileCopyrightText: 2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>

SPDX-License-Identifier: BSD-2-Clause
-->

# Kitteh's Bot Framework/Infrastructure

## Introduction

`mewbot` is a proposed bot infrastructure which will attempt to provide a
generic framework for writing "bots" — namely automated messaging systems
running in social spaces such as Twitch chats, Discords, and so forth.

The codebase will be able to run multiple "bots", which can be configured
via an API or Web GUI. The configuration will be stored as JSON/YAML (tbd)
in a way not dissimilar to Kubernetes configuration.

Python is the language chosen for development, as it allows for the clever
registration of classes via metaclasses, and in-built help with presenting
type information.

### A Bot's Context

"What is the scope of a bot?" is an interesting question when building a
generic bot system.

A Twitch bot makes an excellent example: there are generally at least two
different twitch accounts involved in a twitch bot:

 - The streamer (e.g. `BurgerOni`)
 - The bot (e.g. `NightBot`)

The streamer may have multiple bots, and the bot can be running for
multiple streamers, all with a different configurations.
(In fact, NightBot is at time of writing the most common bot on Twitch).

The combination of a bot account and a space for it to run in is the
basis of a bot's context, and where configuration is bound to.
In this infrastructure, a `Bot` is collection of behaviours (things
the bot does) that is bound to one or more contexts.

### Intentional Design Limitations

#### Languages

English-language only: features where the system is providing text
information are only designed to work in English, with no support
for translations provided.

This will affect defaults / fall backs — error messages, the admin
UI, logging, and so forth.

TODO: explicitly call out that the default pronouns will be in english
and how that works either here on in the text replacements section.

## Primary Components

TODO: ERD goes here

### Bot

The top level of data structure in the system is the Bot, which represents
a group of bot contexts that have the same configuration.

The purpose of this class is to tie together the Input/Output configuration
(which defines the [context of the bot](#a-bots-context)) with the
behaviours the bot performs.
To support this there are also the data stores, which store state,
and the access control settings, which defines what users can edit the
configuration.

```python
class Bot:
  name: str                        # The bot's name
  io: List[IOConfig]               # Connections to bot makes to other services
  behaviours: List[Behaviour]      # All the things the bot does
  datastores: Map[str, DataStore]  # Datastores for this bot


class Behaviour:
  triggers:   List[Trigger]     # This of things that can trigger this behaviour
  conditions: List[Condition]   # conditions on the action being called when it is matched (e.g. "is subscribed")
  actions:    List[Action]      # the things to do if an event matches, and the conditions are met
```

Trigger's, Condition's and Action's can all have properties, which can be edited in the UI

### IOConfig / Input / Output

A "bot" is a fundamentally transformative process — input is accepted
in the form of commands, messages, etc. and then some output is generated
(such as a reply).

For some systems, this will be one unified API — Discord bots need only
one key to interact with all guilds and perform all the things they want to.

On the other hand, an advanced twitch bot requires multiple inputs and
(potentially) multiple outputs. In order to read and respond to chat,
tokens must be generated for the bot account itself; in order to look
for other events such as followers, subscriptions, rewards, and raids,
tokens have to be made for the streamer's account — which is generally
a different user/channel to the bot.

Other inputs might include API calls/webhooks to the management system itself,
allowing for devices like stream decks to be configured to directly interact
with the bot.

#### IOConfig

From an implementation perspective, these will be configured as inputs/outputs
(so cases like discord where one connection is both don't require two to be
configured). These configurations will then present a list of Inputs and Outputs
which can be used in Triggers.

```python
from mewbot.api.v1 import *

class Discord(IOConfig):
	@property
	def oauth_token(self) -> str:
		"""The oAuth token used to interact with the Discord API"""
		...

	@property
	def guilds(self) -> Optional[Set[str]]:
		"""Which Guild IDs to connect this bot to.

		If empty, will bind to all guilds that the bot has access to"""
		...

	def get_inputs(self) -> Sequence[Input]:
		...

	def get_outputs(self) -> Sequence[Output]:
		...
```

#### Input

The `Input` class surfaces events into the core event loop.
These will be associated with an output for the "reply" logic.

#### Output

The `Output` class will not be used a lot, but will be available for giving
a target for "replies" to events triggered by time passing or webhooks.

Outputs will be responsible for string replacements — `${user}` gives full
username, `${@user}` @s them, `${user()}` gives the username but tries to
contextually remove trailing things in brackets (e.g. pronouns)
which aren't part of the 'name' per se.

TODO: Pronouns — there should be a special datastore for pronouns, and a
pre-built config that supplied !pronouns to get and set them.
If possible, having better twitch's and discord roles as data sources for this.
This would then allow a `${user_they}` to return they, she, he etc. if the
pronoun has been set, or if the bot is able to auto detect it, otherwise
just use the user name.
`${they}` will go for just a pronoun, using "they" by default, but be
discouraged (I can see cases where a name wouldn't scan, but maybe this should
not be included in the spec).

### Behaviour

```python
class Behaviour:
  triggers:   List[Trigger]     # This of things that can trigger this behaviour
  conditions: List[Condition]   # conditions on the action being called when it is matched (e.g. "is subscribed")
  actions:    List[Action]      # the things to do if an event matches, and the conditions are met
```

#### Template

Behaviours are going to be big and complicated, so modules should
provide Templates which help users quickly create them based on common
use cases.

Like the other elements, these have a number of properties that can
be presented to the UI/API, but the `Template` is not stored as part
of the `Bot` configuration — instead it is used to generate the
`Behaviour` and add it to the bot.

### Datastore

A datastore is a represents all persistent user-defined parts of bot state,
which can then the used by Behaviours. The data stored in these datastores
is typed.

#### Single-Valued Datastore

The most trivial kind of datastore stores a single value, and has a getter
and setter.
```python
from typing import *

T = TypeVar("T")

class DataRecord(Generic[T]):
  value: T
  modified_at: datetime.datetime
  modified_by: str

class Datastore(Generic[T]):
  name: str

  def get(self) -> DataRecord[T]:
    ...

  def set(self, value: Optional[T]) -> None:
    ...

  def clear(self) -> None:
    self.set(None)
```

The `name` of the datastore is a unique-per-bot name which is used to bind it
to behaviours in the UI.

In some cases, the setter may be not implemented, but it must never throw
an exception. This might be useful for a RandomNumberDataSource (which returns
a different pseudo-random number each call), or a DataSource that is wrapping
an external API.

When the `set` is not implemented, `clear` should likewise be a no-op. `clear`
should also be a valid operation if `set` is, but may use a differnt default
value. `set` may reject `None` as a value, if having an undefined value does not
make sense for the datastore.

#### List Datastores

One other Datasource contract is defined as part of the specification, which
is the `List` equivalent of the above datasource.

```python
from typing import *

T = TypeVar("T")

class ListDatastore(Generic[List[T]]):
  def __getitem__(self, key) -> DataRecord[T]:
    ...

  def __setitem__(self, key, value: Optional[T]) -> None:
    ...

  def __delitem__(self, key) -> None:
    ...

  def __len__(self) -> int:
    ...

  def random_entry(self) -> DataRecord[T]:
    ...

  def random_entries(count: int) -> Sequence[DataRecord[T]]:
    ...

  def get() -> DataRecord[T]:
    """Should function like an iterator, returning the next value each time."""

  def set() -> DataRecord[T]:
    """If __setitem__ is defined, and this is an incrementing list, this
       should function as per list.append()"""

   def clear() -> DataRecord[T]:
     """If __delitem__ is defined, this should delete all items"""
```

The generic List Datastore is only defined for 0-based contiguous lists.
When designing custom implementation that extend this class, you should
be aware that behaviours that are looking for any list storage could be
using your specific implementation, and design around that.

As with the single valued version, having the datastore be writable is
optional; this is for when the datastore is wrapping some other external
or immutable source of data.

One of `random_entry()` or `__getitem__` must be defined. If `__getitem__`
is defined, `__len__` must be as well. If `random_entry` is defined,
then either `__len__` must be defined, or `random_entries` needs a custom
implementation, as the default one will rely on knowning the length.

#### DataRecord Audit Information

As part of the built in format for data stores, each record will record
when it was modified and some contextual information for what by.

TODO: Determine the exact format of what should be recorded as part of
this record, and update the function signatures above.

This data includes the behaviour that made the change (or if it was made
via the UI), and an (optional) username for context. In behaviours that
are triggered off of chat messages, this will be the name of the user
who sent the message. For changes in the UI, this will be the user who
was logged into the UI.

#### Data Moderation

TODO: Determine if this is to be a built-in feature of _all_ list APIs.
TODO: Should this in fact be a part of the DataRecord, and include who
      did the moderation action?

Datastores which are using user-submitted data may want to undergo
moderation, and have records stored in the dataset which will not be
returned by a random() or a get() call.

#### Data Persistence

As well as the abstract classes outlined here, implementations will be
provided that can store datastores of the primitive types in an SQLite
database. This will use one table for all of the single valued
datastores (indexed by the datastore name), and a table per list
datastore, named after the datastore (to optimise length and other calls).

TODO: Decide whether this should explicitly be able to handle any
JSON-encodable structure, rather than just the primitive types. Storing
the data as JSON also means there is only one column type to deal with.

These are expected to be the primary datastores in use, except for wrapping
external calls (such as to APIs), or certain complex data types.

### Trigger

### Conditions

### Actions

### Context Flow

An event that is triggering a behaviour must come with

## Configuration + Discoverability

### Registry

- Validation — modules will need to have a validate function. Where possible, this should check real things (e.g., if one of your configuration options is a discord channel, does that channel exist).
- The discord channel thing raises the question of actual valid vs. presentation value. Discord channels are actually long numbers, not names....

### Properties

### Human Readable Descriptions

Each component will need to present a human readable text string;
e.g. a Trigger might have "When a user sends the chat command !help",
a condition might be "the user is a moderator", and an action might be
"send the message "I don't need any help from you, ${@user}"".
When you're not actively editing the behaviour, rather than show the panels,
all parts of the behaviour will be put together into an sentence/paragraph
description of the behaviour (user story style)

When the behaviour is edited in the UI, this will accordian out into the
main edit view with the inputs.

### Yaml Representation

### Version Control

## User Interface

### Login + ACL

### Behaviour Editing UI

```
+-------------------------------+------------------------------+------------------------------+
|         Triggers              |         Conditions           |           Actions            |
+-------------------------------+------------------------------+------------------------------+
| +--------------------------+  |                              | +--------------------------+ |
| | Chat Command             |  |                              | | Static Text Reply        | |
| |  text: | plan |          |  |                              | |  text: | Do the thing |  | |
| +--------------------------+  |                              | +--------------------------+ |
| +--------------------------+  |                              |                              |
| | Chat Command             |  |                              |                              |
| |  text: | flan |          |  |                              |                              |
| +--------------------------+  |                              |                              |
+-------------------------------+------------------------------+------------------------------+
| +--------------------------+  | +--------------------------+ | +--------------------------+ |
| | Chat Command             |  | | Is Moderator             | | | Static Text Reply        | |
| |  text: | sass |          |  | +--------------------------+ | |  text: | foolish Ben |   | |
| +--------------------------+  |                              | +--------------------------+ |
+-------------------------------+------------------------------+------------------------------+
```

### Datastore Editing UI

- Datastores will need to be editable in the UI. Esepecially moderated datastores
- Datastore moderated
- Clear button

### Reviewing Logs

### Testing + Committing Changes

Test mode — because stuff will be in version control, there should be a
button to apply your changes temporarily without committing them.
This should force your to keep the test tab open and "active" otherwise
it'll revert to the known config.

## Bot Runner

### Event Queue

### Compiling Triggers

### Scheduling Triggers

## Logging

### Change Logs (Version Control)

### Text Logs

### Prometheus Metrics

## User Stories

### Basic call-and-response

### Randomised Responses

### Shoutouts for Raids and VIPs

Core modules I think that will be needed: a StartedChattingTrigger (first message in over an hour)

### Post Periodic Reminders with Live Streaming

a PeriodicWhilstActiveTrigger (for things like snerge).

### Counters

```
Data Stores
|-------|--------|---------|
| Name  | Type   | Default |
|-------|--------|---------|
| falls | Number |       0 |
|-------|--------|---------|


Behaviours
|--------------------------|--------------|-------------------------------------|
| Chat command(text=fall)  | Is Moderator | - increment 'falls' datastore       |
|--------------------------|--------------|-------------------------------------|
| Chat command(text=falls) |              | - reply-all with 'falls' data store |
|--------------------------|--------------|-------------------------------------|
```

### Quote Database

### Reacting to Subscriptions

### Competitions

```
| Chat command(text=startgiveaway)     | Is Moderator   | - Clear 'giveaway' datastore               |
|                                      |                | - Set datastore 'gphrase' to arg[1]        |
|--------------------------------------|----------------|--------------------------------------------|
| Chat command(text=datstore[gphrase]) |                | - Add user to 'giveaway' datastore         |
|--------------------------------------|----------------|--------------------------------------------|
| Chat command(text=stopgiveaway)      | Is Moderator   | - Clear datastore 'gphrase'                |
|--------------------------------------|----------------|--------------------------------------------|
| Chat command(text=drawwinner)        | Is Moderator   | - Get random item for datastore 'giveaway' |
```

### Give game details based on current streamed game

### Cute Animal Pictures

### Go Live Notifications
