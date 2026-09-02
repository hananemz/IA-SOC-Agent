import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import context_handoff
import skills_rag


class RecordingProvider:
    provider_name = "codex-active-runtime"
    model_name = "GPT-5.6 Luna Medium"

    def __init__(self):
        self.requests = []

    def complete(self, request):
        self.requests.append(request)
        return {"accepted": True, "context_length": len(request.context)}


class ContextHandoffIntegrationTests(unittest.TestCase):
    def _run(self, text, decision):
        rag = skills_rag.search(text, top_k=5, decision=decision)
        envelope = context_handoff.build_context(
            text, decision, rag,
            constraints=["Use only verified router and skill metadata.", "Perform read-only investigation only."],
        )
        provider = RecordingProvider()
        response = context_handoff.handoff(provider, envelope)
        return rag, envelope, provider, response

    def test_splunk_context_reaches_provider_boundary(self):
        text = "Investigate brute-force authentication activity in Splunk."
        decision = {"platform": "splunk", "task": "security_alert_triage", "skill": "splunk-security-alert-triage", "query_language": "SPL", "mcp": "splunk-mcp-server", "mcp_status": "VERIFIED"}
        rag, envelope, provider, response = self._run(text, decision)
        self.assertEqual(rag["status"], "RETRIEVED")
        self.assertTrue(rag["results"])
        self.assertTrue(all(item["platform"] in {"splunk", "any"} for item in rag["results"]))
        self.assertEqual(envelope["selected_skill"], decision["skill"])
        self.assertIn("SOURCE:", envelope["context_text"])
        self.assertIn("PLATFORM: splunk", envelope["context_text"])
        self.assertEqual(len(provider.requests), 1)
        self.assertIn(rag["results"][0]["source"], provider.requests[0].context)
        self.assertTrue(response["accepted"])

    def test_elastic_context_reaches_provider_boundary(self):
        text = "Investigate suspicious authentication activity in Elastic."
        decision = {"platform": "elastic", "task": "authentication", "skill": "elasticsearch-authn", "query_language": "ES|QL/KQL", "mcp": "elastic", "mcp_status": "VERIFIED"}
        rag, envelope, provider, _ = self._run(text, decision)
        self.assertEqual(rag["status"], "RETRIEVED")
        self.assertTrue(all(item["platform"] in {"elastic", "any"} for item in rag["results"]))
        self.assertEqual(envelope["selected_platform"], "elastic")
        self.assertEqual(len(provider.requests), 1)
        self.assertIn("PLATFORM: elastic", provider.requests[0].context)

    def test_ambiguous_request_has_no_platform_context_or_mcp(self):
        text = "Investigate brute-force authentication activity."
        decision = {"platform": "unknown", "status": "AMBIGUOUS", "required_clarification": True}
        rag, envelope, provider, _ = self._run(text, decision)
        self.assertEqual(rag["status"], "AMBIGUOUS")
        self.assertEqual(rag["results"], [])
        self.assertEqual(envelope["operational_retrieved_context"], [])
        self.assertNotIn("splunk", envelope["context_text"].lower())
        self.assertNotIn("elastic", envelope["context_text"].lower())
        self.assertNotIn("mcp", envelope["router_decision"])
        self.assertEqual(len(provider.requests), 1)


if __name__ == "__main__":
    unittest.main()
