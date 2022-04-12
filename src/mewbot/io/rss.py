#!/usr/bin/env python3

from __future__ import annotations

import asyncio
from typing import Optional, Set, Sequence, Type, Any, Union, List, AnyStr

import dataclasses
import logging
import pprint
import sys
import subprocess
from itertools import cycle

import feedparser

from mewbot.core import InputEvent, OutputEvent

from mewbot.core import OutputEvent
from mewbot.api.v1 import IOConfig, Input, Output

# rss input operates on a polling loop
# feed read attempts are spread out over the interval

# NOTE
# Input - is what you might expect - it parses rss feeds and puts them on the wire
# Output - RSS server running locally - this has various properties - in particular, you can set the number of events
#          to be served ... might be better to back this with a persistent data source - when one exists
#          RSS is not a real time protocol - so the number of events to store is quite important.


@dataclasses.dataclass
class RSSInputEvent(InputEvent):
    """
    Should contain all the info from the original RSS message.
    Some normalisation might be required, as not all RSS feeds seem to correspond to the standard.
    Spec from https://validator.w3.org/feed/docs/rss2.html#hrelementsOfLtitemgt
    """

    title: str  # The title of the item.
    link: str  # The URL of the item.
    description: str  # The item synopsis.
    author: str  # Email address of the author of the item
    category: str  # Includes the item in one or more categories.
    comments: str  # URL of a page for comments relating to the item
    enclosure: str  # URL of a page for comments relating to the item.
    guid: str  # Describes a media object that is attached to the item.
    pubDate: str  # Indicates when the item was published.
    source: str  # The RSS channel that the item came from.

    startup: bool  # Was this feed read as part of first read for any given site?


@dataclasses.dataclass
class DiscordOutputEvent(OutputEvent):

    title: str  # The title of the item.
    link: str  # The URL of the item.
    description: str  # The item synopsis.
    author: str  # Email address of the author of the item
    category: str  # Includes the item in one or more categories.
    comments: str  # URL of a page for comments relating to the item
    enclosure: str  # URL of a page for comments relating to the item.
    guid: str  # Describes a media object that is attached to the item.
    pubDate: str  # Indicates when the item was published.
    source: str  # The RSS channel that the item came from.


class RSSIO(IOConfig):

    _input: Optional[RSSInput] = None
    _output: Optional[DiscordOutput] = None

    _sites: list  # A list of sites to poll for RSS update events
    _polling_every: int  # Total re-poll time for the sites in the _sites list

    def __init__(self, *args: Optional[Any], **kwargs: Optional[Any]) -> None:
        self._logger = logging.getLogger(__name__ + "DesktopNotificationIO")

        # Not entirely sure why, but empty properties in the yaml errors
        self._logger.info("DesktopNotificationIO received args - %s", args)
        self._logger.info("DesktopNotificationIO received kwargs - %s", kwargs)

        self._polling_every = kwargs["polling_every"]

    @property
    def sites(self):
        return self._sites

    @sites.setter
    def sites(self, sites: list) -> None:
        """
        Presented as a property because updating it requires updating the runner as well.
        """
        self._sites = sites
        if not self._input:
            return
        self._input.update_sites(sites)

    def get_inputs(self) -> Sequence[Input]:
        if not self._input:
            self._input = RSSInput(self._sites, self._polling_every)

        return [self._input]

    def get_outputs(self) -> Sequence[Output]:
        if not self._output:
            self._output = DiscordOutput()

        return [self._output]


class RSSInput(Input):
    """
    Polling RSS Input source -
    """

    _logger: logging.Logger

    _sites: List[str]  # A list of sites to poll for RSS update events
    _polling_every: int  # How often to poll all the given sites (in seconds)

    def __init__(self, sites: List[str], polling_every: int, startup_queue_depth: int = 5) -> None:
        super(Input, self).__init__()  # pylint: disable=bad-super-call

        self._sites = sites
        self._sites_iter = cycle(iter(self._sites))

        self._polling_every = polling_every  # The time taken to poll ever site in sites once

        self.startup_queue_depth = startup_queue_depth # How many RSS articles to retrieve for each site on start

        self._logger = logging.getLogger(__name__ + "DiscordInput")
        # If we have no sites to poll, then we shall do nothing
        if len(self._sites) == 0:
            self._polling_interval = None
        else:
            self._polling_interval = float(self._polling_every) / float(len(self._sites))

        # Used to note to the event loop when it's required to restart the monitor loop
        self._restart_needed = asyncio.Event()

        # Record start
        self._logger.info("RSSInput starting: \nsites\n%s\npolling_every: %s\nstartup_queue_depth: %s",
                          pprint.pformat(self._sites), self._polling_every, self.startup_queue_depth
                          )

        self.sites_started = set()

    @property
    def sites(self):
        return self._sites

    @sites.setter
    def sites(self, new_sites):
        self._sites = new_sites
        self._sites_iter = cycle(iter(self._sites))

    @staticmethod
    def produces_inputs() -> Set[Type[InputEvent]]:
        """
        Defines the set of input events this Input class can produce.
        """
        return {RSSInputEvent, }

    @property
    def polling_every(self):
        return self._polling_every

    @polling_every.setter
    def polling_every(self, new_polling_time):
        self._polling_every = new_polling_time

        # If we have no sites to poll, then we shall do nothing
        if len(self._sites) == 0:
            self._polling_interval = None
        else:
            self._polling_interval = float(self._polling_every / float(len(self._sites)))

    @property
    def polling_interval(self) -> Union[float, None]:
        """
        Trying to spread the calls to sites evenly out over the whole loop.
        Should never be directly set, being calculated from the number of sites to poll and the
        """
        return self._polling_interval

    async def run(self) -> None:
        """
        Fires up an aiohttp app to run the service.
        Token needs to be set by this point.
        """
        self._logger.info(
            "About to start RSS polling - %s will be polled every %s seconds", self._sites, self._polling_every
        )

        for target_site in self._sites_iter:
            if target_site not in self.sites_started:
                asyncio.get_running_loop().create_task(self.startup_site_feed(target_site))
                await asyncio.sleep(self.polling_every)
                continue

            asyncio.get_running_loop().create_task(self.process_site(target_site))

            # Delay before getting the next site - stagger site reads to prevent overwealming anything
            await asyncio.sleep(self.polling_every)

    async def startup_site_feed(self, site_url: str):
        """
        Preform the first read of a site - there is some information to gather which must be stored.
        The requested number of events must be read and put on the wire.
        """
        self._logger.info("Starting feed for site %s - %s entries will be retrieved")

        # Read the site feed
        site_newsfeed = feedparser.parse(site_url)
        site_entries = site_newsfeed.entries

        # Read the requested number of entries and put them on the wire
        for _ in range(0, self.startup_queue_depth):
            try:
                print(site_entries[_].title)
            except IndexError:  # Probably not enough entries in the retrieved feed to exhaust the startup requirements
                break

        self.sites_started.add(site_url)

    async def process_site(self, site_url:str ) -> None:
        print("Here we are")

    async def _send_entry(self, entry, site_url, starting) -> None:
        ...









class DiscordOutput(Output):
    @staticmethod
    def consumes_outputs() -> Set[Type[OutputEvent]]:
        """
        Defines the set of output events that this Output class can consume
        :return:
        """
        return {DiscordOutputEvent}

    async def output(self, event: OutputEvent) -> bool:
        """
        Does the work of transmitting the event to the world.
        :param event:
        :return:
        """

        if not isinstance(event, DiscordOutputEvent):
            return False

        if event.use_message_channel:
            await event.message.channel.send(event.text)
            return True

        raise NotImplementedError("Currently can only respond to a message")