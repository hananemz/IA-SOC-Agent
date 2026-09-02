import unittest

import local_rag


class LocalRagTests(unittest.TestCase):
    def test_tokenization_is_case_insensitive(self):
        self.assertEqual(local_rag.tokens("Elastic ES|QL"), ["elastic", "es", "ql"])

    def test_only_operational_corpus_is_indexed(self):
        index = local_rag.build_index()
        sources = {doc["source"] for doc in index["documents"]}
        self.assertTrue(sources)
        self.assertEqual(index["kind"], "operational_knowledge_rag")
        self.assertFalse(any("SKILL.md" in str(doc) for doc in index["documents"]))

    def test_search_returns_relevant_router_evidence(self):
        results = local_rag.search("Investigate suspicious PowerShell execution", top_k=5, decision={"platform": "elastic", "skill": "security-alert-triage"})
        self.assertTrue(results)
        self.assertTrue(any(item["type"] in {"investigation_pattern", "query_example", "troubleshooting"} for item in results["results"]))

    def test_platform_and_skill_isolation(self):
        splunk = local_rag.search("authentication brute force", decision={"platform": "splunk", "skill": "splunk-authentication"})
        self.assertTrue(all(item["platform"] in {"splunk", "any"} for item in splunk["results"]))
        elastic = local_rag.search("authentication brute force", decision={"platform": "elastic", "skill": "elasticsearch-authn"})
        self.assertTrue(all(item["platform"] in {"elastic", "any"} for item in elastic["results"]))

    def test_adaptive_result_budget_is_configurable(self):
        result = local_rag.search("authentication failed login", top_k=8, decision={"platform": "elastic", "skill": "elasticsearch-authn"})
        self.assertLessEqual(len(result["results"]), 8)
        self.assertLessEqual(sum(len(item["snippet"]) for item in result["results"]), 6000)

    def test_no_decision_means_no_retrieval(self):
        self.assertEqual(local_rag.search("Investigate suspicious PowerShell") ["results"], [])

    def test_skill_context_is_deduplicated(self):
        initial = local_rag.search("PowerShell telemetry gap troubleshooting", decision={"platform": "elastic", "skill": "security-alert-triage"})
        result = local_rag.search("PowerShell telemetry gap troubleshooting", decision={"platform": "elastic", "skill": "security-alert-triage"}, skill_context=initial["results"][0]["snippet"])
        self.assertNotIn(initial["results"][0]["id"], {item["id"] for item in result["results"]})

    def test_empty_result_does_not_invent_context(self):
        result = local_rag.search("florp zibble", decision={"platform": "elastic", "skill": "security-alert-triage"})
        self.assertEqual(result["status"], "NO_RELEVANT_CONTEXT")
        self.assertEqual(result["results"], [])

    def test_result_contract_has_no_authority_or_evidence_fields(self):
        result = local_rag.search("PowerShell investigation", decision={"platform": "elastic", "skill": "security-alert-triage"})
        for item in result["results"]:
            self.assertNotIn("mcp", item)
            self.assertNotIn("evidence", item)
            self.assertNotIn("schema", item)
        self.assertEqual(result["role"], "advisory operational context")


if __name__ == "__main__":
    unittest.main()
