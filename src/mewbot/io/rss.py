#!/usr/bin/env python3

from __future__ import annotations

import asyncio
from typing import Optional, Set, Sequence, Type, Any, Union, List, SupportsInt

import dataclasses
import logging
import pprint
from itertools import cycle

import feedparser  # type: ignore

from mewbot.core import InputEvent, OutputEvent

from mewbot.api.v1 import IOConfig, Input, Output

# rss input operates on a polling loop
# feed read attempts are spread out over the interval

# NOTE
# Input - is what you might expect - it parses rss feeds and puts them on the wire
# Output - RSS server running locally - this has various properties -
#          in particular, you can set the number of events to be served ... might be better to back
#          this with a persistent data source
#          when one exists
#          RSS is not a real time protocol - so the number of events to store is quite important.

TITLE_NOT_SET_STR = "TITLE NOT SET BY SOURCE"
LINK_NOT_SET_STR = "LINK NOT SET BY SOURCE"
DESCRIPTION_NOT_SET_STR = "DESCRIPTION NOT SET BY SOURCE"
AUTHOR_NOT_SET_STR = "AUTHOR NOT SET BY SOURCE"
CATEGORY_NOT_SET_STR = "CATEGORY NOT SET BY SOURCE"
COMMENTS_NOT_SET_STR = "COMMENTS (URL) NOT SET BY SOURCE"
ENCLOSURE_NOT_SET_STR = "ENCLOSURE (URL) NOT SET BY SOURCE"
PUBDATE_NOT_SET_STR = "PUBDATE NOT SET BY SOURCE"
SOURCE_NOT_SET_STR = "SRC NOT SET BY SOURCE"


@dataclasses.dataclass
class RSSInputEvent(InputEvent):
    """
    Should contain all the info from the original RSS message.
    Some normalisation might be required, as not all RSS feeds seem to correspond to the standard.
    Spec from https://validator.w3.org/feed/docs/rss2.html#hrelementsOfLtitemgt
    """

    # pylint: disable=too-many-instance-attributes
    # Want to fully represent the core RSS standard

    title: str  # The title of the item.
    link: str  # The URL of the item.
    description: str  # The item synopsis.
    author: str  # Email address of the author of the item
    category: str  # Includes the item in one or more categories.
    comments: str  # URL of a page for comments relating to the item
    enclosure: str  # Optional URL of media associated with the file
    guid: str  # A unique identifier for the item
    pub_date: str  # Indicates when the item was published.
    source: str  # The RSS channel that the item came from.

    site_url: str  # The site according to us
    entry: feedparser.util.FeedParserDict  # raw entry for later processing

    startup: bool  # Was this feed read as part of first read for any given site?


@dataclasses.dataclass
class RSSOutputEvent(OutputEvent):

    # pylint: disable=too-many-instance-attributes
    # Want to fully represent the core RSS standard

    title: str  # The title of the item.
    link: str  # The URL of the item.
    description: str  # The item synopsis.
    author: str  # Email address of the author of the item
    category: str  # Includes the item in one or more categories.
    comments: str  # URL of a page for comments relating to the item
    enclosure: str  # URL of a page for comments relating to the item.
    guid: str  # Describes a media object that is attached to the item.
    pub_date: str  # Indicates when the item was published.
    source: str  # The RSS channel that the item came from.


class RSSIO(IOConfig):

    _input: Optional[RSSInput] = None
    _output: None

    _sites: List[str]  # A list of sites to poll for RSS update events
    _polling_every: int  # Total re-poll time for the sites in the _sites list

    def __init__(
        self,
        *args: Optional[Any],
        polling_every: Union[str, bytes, SupportsInt],
        **kwargs: Optional[Any],
    ) -> None:
        self._logger = logging.getLogger(__name__ + "DesktopNotificationIO")

        # Not entirely sure why, but empty properties in the yaml errors
        self._logger.info("DesktopNotificationIO received args - %s", args)
        self._logger.info("DesktopNotificationIO received kwargs - %s", kwargs)

        self._polling_every = int(polling_every)

    @property
    def sites(self) -> List[str]:
        return self._sites

    @sites.setter
    def sites(self, sites: List[str]) -> None:
        """
        Presented as a property because updating it requires updating the runner as well.
        """
        self._sites = sites
        if not self._input:
            return
        self._input.sites = sites

    def get_inputs(self) -> Sequence[Input]:
        if not self._input:
            self._input = RSSInput(self._sites, self._polling_every)

        return [self._input]

    def get_outputs(self) -> Sequence[Output]:
        return []


class RSSInput(Input):
    """
    Polling RSS Input source -
    """

    _logger: logging.Logger

    _sites: List[str]  # A list of sites to poll for RSS update events
    _polling_every: int  # How often to poll all the given sites (in seconds)
    sites_started: Set[str]  # sites which have undergone startup
    sent_entries: Set[str]  # entries which have been put on the wire

    def __init__(
        self, sites: List[str], polling_every: int, startup_queue_depth: int = 5
    ) -> None:
        super(Input, self).__init__()  # pylint: disable=bad-super-call

        self._sites = sites
        self._sites_iter = cycle(iter(self._sites))

        self._polling_every = polling_every  # The time taken to poll ever site in sites once

        self.startup_queue_depth = (
            startup_queue_depth  # How many RSS articles to retrieve for each site on start?
        )

        self._logger = logging.getLogger(__name__ + "RSSInput")

        # Used to note to the event loop when it's required to restart the monitor loop
        # self._restart_needed = asyncio.Event()

        # logging start
        self._logger.info(
            "RSSInput starting: \nsites\n%s\npolling_every: %s\nstartup_queue_depth: %s",
            pprint.pformat(self._sites),
            self._polling_every,
            self.startup_queue_depth,
        )

        # Internal state variables
        self.sites_started = set()
        self.sent_entries = (
            set()
        )  # Methadology needs to be reworked for long running processess

    @property
    def polling_interval(self) -> Union[float, None]:
        """
        polling_interval is the time that the Input should wait between polling a new site.
        The total time between repoll of each site is polling_every.
        """
        # If we have no sites to poll, then we shall do nothing
        if len(self._sites) == 0:
            return None
        return float(self._polling_every) / float(len(self._sites))

    @property
    def sites(self) -> List[str]:
        return self._sites

    @sites.setter
    def sites(self, new_sites: List[str]) -> None:
        self._sites = new_sites
        self._sites_iter = cycle(iter(self._sites))

    @staticmethod
    def produces_inputs() -> Set[Type[InputEvent]]:
        """
        Defines the set of input events this Input class can produce.
        """
        return {
            RSSInputEvent,
        }

    @property
    def polling_every(self) -> int:
        return self._polling_every

    @polling_every.setter
    def polling_every(self, new_polling_time: int) -> None:
        self._polling_every = new_polling_time

    def _get_entry_uid(self, entry: feedparser.util.FeedParserDict, site_url: str) -> str:
        """
        Returns a unique id (on a system level) for the given entry and site combination.
        Used to determine if entries have been put on the wire or not
        """
        try:
            entry_title = entry.title
        except AttributeError:
            entry_title = TITLE_NOT_SET_STR

        try:
            entry_guid = entry.guid
        except AttributeError:
            self._logger.warning(
                "entry %s did not possess a guid - %s might be producing malformed RSS entries",
                entry,
                site_url,
            )

            # This is not a fantastic fallback - but it should work most of the time
            entry_guid = f"{entry_title}"

        return f"{entry_guid}:{site_url}"

    async def run(self) -> None:
        """
        Fires up an aiohttp app to run the service.
        Token needs to be set by this point.
        """
        self._logger.info(
            "About to start RSS polling - %s will be polled every %s seconds",
            self._sites,
            self._polling_every,
        )

        for target_site in self._sites_iter:

            if target_site not in self.sites_started:
                asyncio.get_running_loop().create_task(self.startup_site_feed(target_site))
                # Delay before getting the next site
                # stagger site reads to prevent overwealming anything
                await asyncio.sleep(self.polling_every)
                continue

            asyncio.get_running_loop().create_task(self.poll_site_feed(target_site))
            # Delay before getting the next site
            # stagger site reads to prevent overwealming anything
            await asyncio.sleep(self.polling_every)

    async def startup_site_feed(self, site_url: str) -> None:
        """
        Preform the first read of a site - there is some information to gather which must be stored.
        The requested number of events must be read and put on the wire.
        """
        self._logger.info(
            "Starting feed for site %s - %s entries will be retrieved",
            site_url,
            self.startup_queue_depth,
        )

        # Read the site feed
        site_newsfeed = feedparser.parse(site_url)
        site_entries = site_newsfeed.entries

        # Read the requested number of entries and put them on the wire
        for _ in range(0, self.startup_queue_depth):

            entry_internal_id = self._get_entry_uid(entry=site_entries[_], site_url=site_url)
            if entry_internal_id in self.sent_entries:
                self._logger.warning(
                    "entry_internal_id - %s - for entry - %s - from site - %s - "
                    "has been seen before!",
                    entry_internal_id,
                    site_entries[_],
                    site_url,
                )
                continue

            try:
                await self._send_entry(entry=site_entries[_], site_url=site_url, startup=True)
            except IndexError:
                # Not enough entries in the retrieved feed to exhaust startup requirements?
                break

            self.sent_entries.add(entry_internal_id)

        self.sites_started.add(site_url)

    async def poll_site_feed(self, site_url: str) -> None:

        self._logger.info("Reading from site %s", site_url)

        # Read the site feed
        site_newsfeed = feedparser.parse(site_url)
        site_entries = site_newsfeed.entries

        # Itterate backwards until we run into an entry which has already been sent
        transmitted_count = 0
        for entry in site_entries:

            entry_uid = self._get_entry_uid(entry, site_url)

            if entry_uid in self.sent_entries:
                break

            await self._send_entry(entry=entry, site_url=site_url, startup=False)
            transmitted_count += 1
            self.sent_entries.add(self._get_entry_uid(entry=entry, site_url=site_url))

        self._logger.info("%s entries from %s transmitted", transmitted_count, site_url)

    @staticmethod
    def _extract_title(entry: feedparser.util.FeedParserDict, problem_list: List[str]) -> str:
        """
        Extract and return the title from an entry.
        Adding any problems to the problem list.
        """
        # title
        try:
            entry_title = entry.title
        except AttributeError:
            problem_list.append("entry did not possess a title attribute")
            entry_title = TITLE_NOT_SET_STR

        return str(entry_title)

    @staticmethod
    def _extract_link(entry: feedparser.util.FeedParserDict, problem_list: List[str]) -> str:
        """
        Extract and return the link from an entry.
        Adding any problems to the problem list.
        """
        # link
        try:
            entry_link = entry.link
        except AttributeError:
            problem_list.append("entry did not possess a link attribute")
            entry_link = LINK_NOT_SET_STR

        return str(entry_link)

    @staticmethod
    def _extract_description(
        entry: feedparser.util.FeedParserDict, problem_list: List[str]
    ) -> str:
        """
        Extract and return the link from an entry.
        Adding any problems to the problem list.
        """
        # description
        try:
            entry_description = entry.description
        except AttributeError:
            problem_list.append("entry did not possess a description attribute")
            entry_description = DESCRIPTION_NOT_SET_STR

        return str(entry_description)

    @staticmethod
    def _extract_author(
        entry: feedparser.util.FeedParserDict, problem_list: List[str]
    ) -> str:
        try:
            entry_author = entry.author
        except AttributeError:
            problem_list.append("entry did not possess an author attribute")
            entry_author = AUTHOR_NOT_SET_STR

        return str(entry_author)

    @staticmethod
    def _extract_category(
        entry: feedparser.util.FeedParserDict, problem_list: List[str]
    ) -> str:
        try:
            entry_category = entry.category
        except AttributeError:
            problem_list.append("entry did not possess a category attribute")
            entry_category = CATEGORY_NOT_SET_STR

        return str(entry_category)

    @staticmethod
    def _extract_comments(
        entry: feedparser.util.FeedParserDict, problem_list: List[str]
    ) -> str:
        try:
            entry_comments = entry.comments
        except AttributeError:
            problem_list.append("entry did not possess a comments attribute")
            entry_comments = COMMENTS_NOT_SET_STR

        return str(entry_comments)

    @staticmethod
    def _extract_enclosure(entry: feedparser.util.FeedParserDict) -> str:
        try:
            entry_enclosure = entry.enclosure
        except AttributeError:
            # No logging as this is an optional attribute
            entry_enclosure = ENCLOSURE_NOT_SET_STR

        return str(entry_enclosure)

    def _extract_guid(
        self, entry: feedparser.util.FeedParserDict, site_url: str, problem_list: List[str]
    ) -> str:

        entry_title = self._extract_title(entry=entry, problem_list=problem_list)

        # guid - there are no rules for this syntax
        # THUS ONLY THE COMBINATION OF GUID AND SITE_URL SHOULD BE ASSUMED UNIQUE
        # This combination is used to determine if events have already been sent
        try:
            entry_guid = entry.guid
        except AttributeError:
            problem_list.append(
                f"entry did not possess a guid - "
                f"{site_url} might be producing malformed RSS entries"
            )

            # This is not a fantastic guid - but one needs to be set for internal tracking
            entry_guid = f"{site_url}:{entry_title}"

        return str(entry_guid)

    @staticmethod
    def _extract_pubdate(
        entry: feedparser.util.FeedParserDict, site_url: str, problem_list: List[str]
    ) -> str:
        # pubDate - if this is not being set, something is badly wrong
        try:
            entry_pubdate = entry.pubDate
        except AttributeError:
            problem_list.append(
                f"entry did not possess a pubDate - "
                f"{site_url} might be producing malformed RSS entries"
            )
            entry_pubdate = PUBDATE_NOT_SET_STR

        return str(entry_pubdate)

    @staticmethod
    def _extract_source(
        entry: feedparser.util.FeedParserDict, problem_list: List[str]
    ) -> str:
        # source
        try:
            entry_source = entry.source
        except AttributeError:
            problem_list.append("entry did not possess a src")
            entry_source = SOURCE_NOT_SET_STR

        return str(entry_source)

    async def _send_entry(
        self, entry: feedparser.util.FeedParserDict, site_url: str, startup: bool = False
    ) -> None:
        """
        Parse an RSS entry and put the OutputEvent representing it on the wire.
        """
        # Some RSS entries do not confirm to the spec - so some creative parsing might be required
        # Starting basic, and building up later

        problem_list: List[str] = []

        # guid - there are no rules for this syntax
        # THUS ONLY THE COMBINATION OF GUID AND SITE_URL SHOULD BE ASSUMED UNIQUE
        # This combination is used to determine if events have already been sent

        input_rss_event = RSSInputEvent(
            title=self._extract_title(entry=entry, problem_list=problem_list),
            link=self._extract_link(entry=entry, problem_list=problem_list),
            description=self._extract_description(entry=entry, problem_list=problem_list),
            author=self._extract_author(entry=entry, problem_list=problem_list),
            category=self._extract_category(entry=entry, problem_list=problem_list),
            comments=self._extract_comments(entry=entry, problem_list=problem_list),
            enclosure=self._extract_enclosure(entry=entry),
            guid=self._extract_guid(
                entry=entry, site_url=site_url, problem_list=problem_list
            ),
            pub_date=self._extract_pubdate(
                entry=entry, site_url=site_url, problem_list=problem_list
            ),
            source=self._extract_source(entry=entry, problem_list=problem_list),
            site_url=site_url,
            startup=startup,
            entry=entry,
        )

        if problem_list:
            self._logger.info(
                "Bad parsing of entry \n%s\n \n%s", entry, "\n".join(problem_list)
            )

        # queue is not initialised - probably
        if not self.queue:
            return

        await self.queue.put(input_rss_event)
