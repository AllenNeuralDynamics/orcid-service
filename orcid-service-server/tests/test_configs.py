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

    @patch.dict(os.environ, {"ORCID_REQUEST_TIMEOUT": "5"}, clear=True)
    def test_timeout_from_env(self):
        """Tests the request timeout can be set without a release"""
        self.assertEqual(5.0, Settings().request_timeout)

    @patch.dict(os.environ, {}, clear=True)
    def test_default_settings(self):
        """Tests the public ORCID hosts are used by default"""
        settings = Settings()
        self.assertEqual("https://pub.orcid.org/", str(settings.api_host))
        self.assertEqual("https://orcid.org/", str(settings.summary_host))
        self.assertEqual(30.0, settings.request_timeout)


if __name__ == "__main__":
    unittest.main()
