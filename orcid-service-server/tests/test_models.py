"""Tests models module"""

import unittest

from orcid_service_server.models import ExpandedSearch, RecordSummary


class TestExpandedSearch(unittest.TestCase):
    """Tests the expanded-search response model"""

    def test_parses_results(self):
        """Tests aliased fields are read from the ORCID payload"""
        search = ExpandedSearch(
            **{
                "expanded-result": [
                    {
                        "orcid-id": "0000-0000-0000-0011",
                        "given-names": "Researcher",
                        "family-names": "One",
                        "institution-name": ["Allen Institute"],
                    }
                ],
                "num-found": 1,
            }
        )
        self.assertEqual(1, search.num_found)
        self.assertEqual(
            "0000-0000-0000-0011", search.expanded_result[0].orcid_id
        )
        self.assertEqual(
            ["Allen Institute"], search.expanded_result[0].institution_name
        )

    def test_handles_null_results(self):
        """Tests ORCID sending null rather than an empty list"""
        search = ExpandedSearch(**{"expanded-result": None, "num-found": 0})
        self.assertIsNone(search.expanded_result)


class TestRecordSummary(unittest.TestCase):
    """Tests the record summary model"""

    def test_parses_email_domains(self):
        """Tests verified email domains are read"""
        summary = RecordSummary(
            **{
                "emailDomains": [
                    {"value": "alleninstitute.org", "verificationDate": None}
                ]
            }
        )
        self.assertEqual(
            "alleninstitute.org", summary.email_domains[0]["value"]
        )

    def test_handles_missing_email_domains(self):
        """Tests a record with no verified domains"""
        summary = RecordSummary(**{})
        self.assertEqual([], summary.email_domains)


if __name__ == "__main__":
    unittest.main()
