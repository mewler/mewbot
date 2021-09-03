<!--
SPDX-FileCopyrightText: 2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>

SPDX-License-Identifier: BSD-2-Clause
-->

# Kitteh's Bot Framework/Infrastructure

- Write a bot in python
- 

## Primary Components

ERD goes here

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

A "bot" is a fundemtnally transformative process -- input is accept in the form
of commands, messages, etc. and then some output is generated (such as a reply).

For some systems, this will be one unified API -- Discord bots need only one
key to interact with all guilds and perform all the things they want to.

On the other hand, an advanced twitch bot requires multiple inputs and
(potentially) multiple outputs. In order to read and respond to chat, tokens
must be generated for the bot account itself; in order to look for other events
such as followers, subscriptions, rewards, and raids, tokens have to be made
for the streamer's account -- which is generally a different user/channel
to the bot.

Other inputs might include API calls/webhooks to the management system itself,
allowing for devices like stream decks to be configured to directly interact
with the bot.

#### IOConfig

From an implementation perspective, these will be configures as inputs/outputs
(so cases like discord where one connection is both don't require two to be
configured). These configurations will then present a list of Inputs and Outputs
which can be used in Triggers.

```python
class Discord(IOConfig):
	@property
	def oauth_token(self) -> str:
		"""The oAuth token used to interact with the Discord API"""
		...

	@property
	def guilds(self) -> Optional[Set[str]]:
		"""Which Guild IDs to connect this bot to.

		If empty, will bind to all guilds that the bot has accces to"""
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

Outputs will be responsible for string replacements -- `${user}` gives full
username, `${@user}` @s them, `${user()}` gives the username but tries to
contextually remove trailing things in brackets (e.g. pronouns)
which aren't part of the 'name' per se.

Pronouns -- there should be a special datastore for pronouns, and a pre-built config that supplied !pronouns to get and set them. If possible, having better twitch's and discord roles as data sources for this. This would then allow a ${user_they} to return they, he, she etc. if the pronoun has been set, or if the bot is able to auto detect it, otherwise just use the full name. ${they} will go for just a pronoun, using "they" by default, but be discouraged (I can see cases where a name wouldn't scan)

### Datastore

Should have who last changed, when, and from where for
any piece of data. it may not matter for counters, but it'll matter for other things

len()
randomEntry()
randomEntries()
next()
reset()

### Trigger

### Conditions

### Actions

### Behaviour

#### Template

### Context Flow

An event that is triggering a behaviour must come with

## Configuration + Discoverability

### Registry

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

### Reviewing Logs

### Testing + Committing Changes

Test mode -- because stuff will be in version control, there should be a
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

## Scratch Pad

 - Datastores will need to be editable in the UI. Esepecially moderated datastores
 - Validation -- modules will need to have a validate function. Where possible, this should check real things (e.g., if one of your configuration options is a discord channel, does that channel exist).
 - The discord channel thing raises the question of actual valid vs. presentation value. Discord channels are actually long numbers, not names....
 - The cat/dog API can be a datastore -- a ListDataStore primarily needs a count() and random() function, and for these it probably won't matter to just return count of 0 or 1 or some such. That means that those APIs don't need to be custom actions, and could be used as other kinds of actions.


