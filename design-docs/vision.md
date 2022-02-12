# Vision

The purpose of mew bot is to create an open-source infrastructure for building
multifunction 'chatbots' that are fully features, scalable, and customisable
without any coding knowledge.

## Rationale and Goals

The original cause of designing this framework was the convergence of a number
of different problems with bot toolchains in the Discord and Twitch spaces.
One of the major bots in Twitch, called NightBot, runs as a 

## Key Design Philosophies

The separation of the code that is written, the configuration of a bot, and
the data created, stored and used by a bot is key to ensuring the system is
testable and easy for users to deploy, maintain, and upgrade.

 - Configuration, code, and data are three distinct silos
 - Components, which are code defined by configuration, should not store data
   themselves (i.e. be stateless)
 - Data should be passed between components via message queues
 - Components and Data should only be aware of their own configuration, and not other Components.

Deployment and configuration should be accessible to all users, and adding
additional functionality should not bear the burden of years of prior coding
experience

 - The code must be designed to run self-hosted on consumer hardware
 - It must also be designed such that multiple bots code run as part of a
   service provider solution.
 - A user with only 'lay-person' computing experience should be able to
   reach and edit configuration of the bot.
 - 
