import json
import os
import unittest
from unittest.mock import patch

os.environ["LANGSMITH_TRACING"] = "false"
os.environ["OPENAI_API_KEY"] = "test-key"

from gtm_agent import data_service
from gtm_agent.gtm_agent import build_prospect_profile, get_prospect, score_prospect
from gtm_agent.gtm_records import OFFERINGS, PROSPECTS


class FakeScoreResult:
    def model_dump(self):
        return {"score": 1}


class FakeScoringLLM:
    def __init__(self):
        self.messages = None

    def invoke(self, messages):
        self.messages = messages
        return FakeScoreResult()


class PrivacyBoundaryTests(unittest.TestCase):
    def setUp(self):
        data_service._PROFILES.clear()

    def test_get_prospect_allowlist_covers_every_fixture(self):
        allowed = {"prospect_id", "name", "email", "disqualified"}
        for prospect_id in PROSPECTS:
            result = get_prospect.invoke({"prospect_id": prospect_id})
            self.assertEqual(set(result["prospect"]), allowed)

    def test_build_profile_allowlist_covers_every_fixture(self):
        allowed = set(data_service.PROFILE_FIELDS)
        for prospect_id in PROSPECTS:
            result = build_prospect_profile.invoke({"prospect_id": prospect_id})
            self.assertEqual(set(result["prospect_profile"]), allowed)
            self.assertNotIn("billing_qualification", result["prospect_profile"])

    def test_cached_legacy_profile_is_sanitized_before_read(self):
        prospect_id = next(iter(PROSPECTS))
        data_service._PROFILES[prospect_id] = {
            **PROSPECTS[prospect_id],
            "prospect_id": prospect_id,
        }

        result = build_prospect_profile.invoke({"prospect_id": prospect_id})

        self.assertNotIn("billing_qualification", result["prospect_profile"])
        self.assertNotIn("billing_qualification", data_service._PROFILES[prospect_id])

    def test_score_payload_allowlist_covers_every_fixture(self):
        offering = next(iter(OFFERINGS.values()))
        fake_llm = FakeScoringLLM()
        with patch("gtm_agent.gtm_agent._scoring_llm", fake_llm):
            for prospect_id, record in PROSPECTS.items():
                score_prospect.invoke({
                    "prospect_profile": {**record, "prospect_id": prospect_id},
                    "offering": offering,
                })
                payload = json.loads(fake_llm.messages[1]["content"].split("\n\nProspect profile:\n", 1)[1])
                self.assertEqual(
                    set(payload),
                    {"prospect_id", "name", "annual_revenue", "tech_stack", "account_details"},
                )
                self.assertNotIn("billing_qualification", payload)


if __name__ == "__main__":
    unittest.main()
