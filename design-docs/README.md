<!--
SPDX-FileCopyrightText: 2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>

SPDX-License-Identifier: BSD-2-Clause
-->

# Kitteh's Bot Framework/Infrastructure

fds

# Primary Components

The

## Input / Output

ERD goes here

```
Bot:
  - id / keys'n'stuff    # All the things to make the bot connect
  - List[Behaviour]      # All the things the bot does
  - Map[str, DataStore]  # Datastores for this bot

Behaviour:
  - List[Trigger]     # This of things that can trigger this behaviour (matches input events, returns arguments for the action)
  - List[Condition]   # conditions on the action being called when it is matched (e.g. "is subscribed")
  - List[Action]      # the things to do if an event matches, and the conditions are met

Trigger's, Condition's and Action's can all have properties, which can be edited in the UI
```

## Datastore

len()
randomEntry()
randomEntries()
next()
reset()

## Trigger

## Conditions

## Actions

## Behaviour

### Template

## Context Flow

An event that is triggering a behaviour must come with

# Configuration + Discoverability

## Registry

## Properties

## Human Readable Descriptions

## Yaml Representation

## Version Control

# User Interface

## Login + ACL

## Behaviour Editing UI

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

## Reviewing Logs

## Testing + Committing Changes

# Bot Runner

## Event Queue

## Compiling Triggers

## Scheduling Triggers

# Logging

## Change Logs (Version Control)

## Text Logs

## Prometheus Metrics

# User Stories

## Basic call-and-response

## Randomised Responses

## Shoutouts for Raids and VIPs

## Counters

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

## Quote Database

## Reacting to Subscriptions

## Competitions

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

## Give game details based on current streamed game

## Cute Animal Pictures

## Go Live Notifications

# Scratch Pad

 - DataStores -- should have who last changed, when, and from where for any piece of data. it may not matter for counters, but it'll matter for other things
 - String replacements -- ${user} gives full username, ${@user} at-s them, ${user()} gives the username but tries to contextually remove trailing things in brackets (e.g. pronouns) which aren't part of the 'name' per se
 - Pronouns -- there should be a special datastore for pronouns, and a pre-built config that supplied !pronouns to get and set them. If possible, having better twitch's and discord roles as data sources for this. This would then allow a ${user_they} to return they, he, she etc. if the pronoun has been set, or if the bot is able to auto detect it, otherwise just use the full name. ${they} will go for just a pronoun, using "they" by default, but be discouraged (I can see cases where a name wouldn't scan)
 - Inputs and Outputs. I've realised that Trigger/Condition/Action describes bot rules very well, but leaves something to be desired in actually setting up a bot. For this, there should be the notion of Inputs and Outputs. Discord is just one giant Input and Output, but a twitch chat is just an input and a twitch chatbot is just an output -- they don't even have to be looking at the same channel. And then there's things like Twitch rewards, which use a different system, and the possiblity of having things like a streamer's stream deck point directly at the bot. Triggers will have input filters, so you can turn a trigger off even if it is compatible with an input (I'm imagining this will be hidden in a more advanced view). When the standard command blocks are 'compiled', they'll be compiled per input.
 - UI stuff -- each component will need to present a human readable text string; e.g. a Trigger might have "When a user sends the chat command !help", a condition might be "the user is a moderator", and an action might be "send the message "I don't need any help from you, ${@user}"". when you're not actively editing a bot rule, rather than show the panels, it'll string it together into an english sentence. It'll accordian out when you want to edit it.
 - Datastores will need to be editable in the UI. Esepecially moderated datastores
 - Validation -- modules will need to have a validate function. Where possible, this should check real things (e.g., if one of your configuration options is a discord channel, does that channel exist).
 - The discord channel thing raises the question of actual valid vs. presentation value. Discord channels are actually long numbers, not names....
 - Test mode -- because stuff will be in version control, there should be a button to apply your changes temporarily without committing them. This should force your to keep the test tab open and "active" otherwise it'll revert to the known config.
 - The cat/dog API can be a datastore -- a ListDataStore primarily needs a count() and random() function, and for these it probably won't matter to just return count of 0 or 1 or some such. That means that those APIs don't need to be custom actions, and could be used as other kinds of actions.
 - Core modules I think that will be needed: a StartedChattingTrigger (first message in other an hour); a PeriodicWhilstActiveTrigger (for things like snerge).


