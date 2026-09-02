import sys, json, unittest
sys.path.insert(0, r"C:\Users\lenovo\.agents\skills-router\security-skill-router\skills-rag")
import skills_rag
import context_handoff

class RegressionTests(unittest.TestCase):
    def test_splunk_routes_to_splunk(self):
        result = skills_rag.search("authentication", decision={"platform": "splunk"})
        for item in result["results"]:
            self.assertEqual(item["platform"], "splunk")

    def test_elastic_routes_to_elastic(self):
        result = skills_rag.search("authentication", decision={"platform": "elastic"})
        for item in result["results"]:
            self.assertEqual(item["platform"], "elastic")

    def test_splunk_skill_selection(self):
        result = skills_rag.search("authentication", decision={"platform": "splunk", "skill": "splunk-authentication"})
        for item in result["results"]:
            self.assertEqual(item["skill"], "splunk-authentication")

    def test_elastic_skill_selection(self):
        result = skills_rag.search("authentication", decision={"platform": "elastic", "skill": "elasticsearch-authn"})
        for item in result["results"]:
            self.assertEqual(item["skill"], "elasticsearch-authn")

    def test_splunk_no_elastic_leak(self):
        result = skills_rag.search("security investigation", decision={"platform": "splunk"})
        for item in result["results"]:
            self.assertNotIn("elastic", item["platform"].lower())

    def test_elastic_no_splunk_leak(self):
        result = skills_rag.search("security investigation", decision={"platform": "elastic"})
        for item in result["results"]:
            self.assertNotIn("splunk", item["platform"].lower())

    def test_context_required_fields(self):
        decision = {"platform": "elastic", "task": "auth", "skill": "elasticsearch-authn", "query_language": "ES|QL", "mcp": "elastic", "mcp_status": "VERIFIED"}
        rag = skills_rag.search("auth", decision=decision)
        env = context_handoff.build_context("test", decision, rag)
        required = ["schema_version", "user_request", "router_decision", "selected_platform", "selected_skill", "query_language", "retrieval_status", "retrieved_context", "llm_instructions", "context_text"]
        for field in required:
            self.assertIn(field, env, "Missing field: " + field)

    def test_mcp_routing_in_context(self):
        decision = {"platform": "splunk", "mcp": "splunk-mcp-server", "mcp_status": "VERIFIED"}
        rag = skills_rag.search("auth", decision=decision)
        env = context_handoff.build_context("test", decision, rag)
        self.assertEqual(env["router_decision"].get("mcp"), "splunk-mcp-server")

    def test_read_only_instructions(self):
        env = context_handoff.build_context("test", {"platform": "elastic"}, {"status": "NO_RELEVANT_CONTEXT"})
        self.assertIn("read-only", env["llm_instructions"].lower())

    def test_no_fabricated_evidence(self):
        env = context_handoff.build_context("test", {"platform": "elastic"}, {"status": "NO_RELEVANT_CONTEXT"})
        self.assertEqual(env["evidence_results"], [])

    def test_provider_independent(self):
        env = context_handoff.build_context("test", {"platform": "elastic"}, {"status": "NO_RELEVANT_CONTEXT"})
        self.assertNotIn("openrouter", env.get("schema_version", "").lower())
        self.assertNotIn("gpt", env.get("schema_version", "").lower())

    def test_cross_platform(self):
        result = skills_rag.search("authentication", decision={"platform": "cross-platform"})
        platforms = set(item["platform"] for item in result["results"])
        self.assertTrue(platforms <= {"elastic", "splunk"})

    def test_ambiguous_no_platform(self):
        result = skills_rag.search("test", decision={"platform": "unknown", "status": "AMBIGUOUS"})
        self.assertEqual(result["results"], [])

    def test_rag_evidence_separation(self):
        env = context_handoff.build_context("test", {"platform": "elastic"}, {"status": "NO_RELEVANT_CONTEXT"})
        self.assertNotIn("LIVE MCP EVIDENCE", env["context_text"])

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(RegressionTests)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    print("PASS_COUNT:", result.testsRun - len(result.failures) - len(result.errors))
    print("FAIL_COUNT:", len(result.failures))
    print("ERROR_COUNT:", len(result.errors))
