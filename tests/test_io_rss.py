from typing import Type

from tests.common import BaseTestClassWithConfig

from mewbot.io.rss import RSSIO
from mewbot.api.v1 import IOConfig


class TestRSSIO(BaseTestClassWithConfig[RSSIO]):
    config_file: str = "examples/rss_input.yaml"
    implementation: Type[RSSIO] = RSSIO

    def test_check_class(self) -> None:
        assert isinstance(self.component, RSSIO)
        assert isinstance(self.component, IOConfig)

    def test_direct_set_polling_every_property_fails(self) -> None:
        """
        Test that directly setting the "polling_every" fails.
        """
        try:
            self.component.polling_every = 4
        except AttributeError:
            pass

    def test_get_set_sites_property(self) -> None:
        """
        Tests that the "sites" property can be read and set.
        """
        test_sites = self.component.sites
        assert isinstance(test_sites, list)

        # Attempt to set sites to be a string
        try:
            setattr(self.component, "sites", "")  # To stop mypy complaining
        except AttributeError:
            pass

        self.component.sites = []
