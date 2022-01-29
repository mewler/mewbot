# Data Flow

```
  Input                             Behaviour
                      Processor                               Processor      Output
            Input                                  Output
  Input     Event                   Behaviour      Event
            Queue                                  Queue
                      Processor
  Input                             Behaviour                 Processor      Output


                                    DataSource
```

## Inputs

As inputs are expecting to be working as async agents,
each one is in its own thread (group).
It will put Events onto the InputEventQueue

## InputEventQueue

This will be a thread safe queue containing DataClass style messages.
The class of each event will be used to determine which Behaviours will see it.

Events will be consumed by the processor threads, which will offer them out
to Behaviours

## Input Processing Threads

This is a processing pool that takes events off the queue.
It will look at the type of the Event, and then offer it to all Behaviours
that support that event time (so, a Behaviour which has a Matcher that
accepts a TwitchMessage won't need to be called for web hooks or discord
messages etc.

If there are multiple bots, then they will have their own queue and processor.

Note: When building the bot's configuration, Behaviours may group themselves
into a BehaviourDispatcher. From the point of view of the ProcessingThread,
this behaves as a single complex Behaviour.
An example use case of this is a large number of distinct plink commands --
the same basic logic is used for a Matcher matching `!help`, `!game`,
and so forth, and these can be combined into one logical operation.

The Processing thread is the thread that handles processing of all the
behaviours in the message. Behaviours MUST NOT do I/O things or async work
except via the DataSource and Logging interfaces, and should put
output events into the output queue.

## Output Event Queue + Processor

Like the input event queue, the queue consists of data only messages,
where the class of the message is indicative of what kind of action is being
taken.

The output processor will match the message type to an output the bot has,
and then attempt to use them in priority order (class heirarachy first, then
by order of definition in the bot). A later output will only be called if
all the ones before it report that they could not process the event.

Two basic built in Outputs are going to be needed: one is a catch all that
logs the failure to send the event, and the other is an outgoing webhook,
which allows the bot to send data to somewhere else on the internet.
