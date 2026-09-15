"""Tests configs module"""

import os
import unittest
from unittest.mock import patch

from orcid_service_server.configs import Settings


class TestSettings(unittest.TestCase):
    """Test methods in Settings Class"""

    @patch.dict(
        os.environ,
        {
            "ORCID_API_HOST": "http://example.com/pub",
            "ORCID_SUMMARY_HOST": "http://example.com",
        },
        clear=True,
    )
    def test_get_settings(self):
        """Tests settings can be set via env vars"""
        settings = Settings()
        expected_settings = Settings(
            api_host="http://example.com/pub",
            summary_host="http://example.com",
        )
        self.assertEqual(expected_settings, settings)

    @patch.dict(os.environ, {}, clear=True)
    def test_default_settings(self):
        """Tests the public ORCID hosts are used by default"""
        settings = Settings()
        self.assertEqual("https://pub.orcid.org/", str(settings.api_host))
        self.assertEqual("https://orcid.org/", str(settings.summary_host))


if __name__ == "__main__":
    unittest.main()
