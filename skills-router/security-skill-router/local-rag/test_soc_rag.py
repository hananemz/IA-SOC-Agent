import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import context_handoff
import local_rag
import soc_rag
import recommendations


class SocRagTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = soc_rag.build_index()

    def search(self, query, decision=None, top_k=6):
        return soc_rag.search(query, top_k=top_k, index=self.index)

    def test_index_has_extensible_schema_and_attribution(self):
        self.assertGreater(self.index["document_count"], 0)
        self.assertGreaterEqual(self.index["chunk_count"], self.index["document_count"])
        doc = self.index["documents"][0]
        for field in ("id", "title", "category", "topic", "source", "source_url", "platform", "tactic", "technique", "severity", "tags", "content"):
            self.assertIn(field, doc)
        self.assertTrue(all(doc["platform"] == "any" for doc in self.index["documents"]))

    def test_supported_intents(self):
        expected = {
            "TRIAGE": "Investigate this security alert",
            "MITRE_MAPPING": "Map suspicious PowerShell to MITRE ATT&CK",
            "IOC_ANALYSIS": "Analyze this IOC hash and domain",
            "INVESTIGATION": "Investigate suspicious process activity",
            "FALSE_POSITIVE": "Is this alert a false positive?",
            "INCIDENT_RESPONSE": "What are the incident response next actions?",
            "THREAT_HUNTING": "Threat hunt for rare process behavior",
            "RISK_ASSESSMENT": "Assess the severity and risk",
            "DETECTION": "Tune this detection rule",
        }
        for intent, query in expected.items():
            self.assertEqual(soc_rag.detect_intent(query)["intent"], intent, query)

    def test_ai_intents_and_metadata(self):
        cases = {
            "AI_SECURITY": "AI security monitoring for an LLM system",
            "PROMPT_INJECTION_ANALYSIS": "analyze a prompt injection attempt",
            "RAG_SECURITY_ANALYSIS": "investigate RAG poisoning in a vector database",
            "AI_AGENT_SECURITY": "agent called an unauthorized tool",
            "AI_DATA_LEAKAGE": "AI leaked another user's data",
            "AI_THREAT_HUNTING": "hunt abnormal token consumption against baseline",
            "AI_INCIDENT_RESPONSE": "AI incident response containment",
            "AI_DETECTION_ENGINEERING": "build an AI detection correlation rule",
        }
        for intent, query in cases.items():
            self.assertEqual(soc_rag.detect_intent(query)["intent"], intent, query)
        result = self.search("malicious instruction inside RAG document")
        self.assertEqual(result["intent"], "RAG_SECURITY_ANALYSIS")
        self.assertTrue(result["results"])
        self.assertEqual(result["results"][0]["category"], "ai_security")
        self.assertIn("attack_status", result["results"][0])
        self.assertIn("related_framework", result["results"][0])

    def test_ai_queries_rank_ai_documents_above_traditional_documents(self):
        for query in (
            "prompt injection attempt",
            "agent called an unauthorized tool",
            "AI leaked another user's data",
            "abnormal token consumption",
            "system prompt extraction attempt",
        ):
            result = self.search(query)
            self.assertTrue(result["results"], query)
            self.assertEqual(result["results"][0]["category"], "ai_security", query)

    def test_low_confidence_falls_back_to_general_security(self):
        result = soc_rag.detect_intent("security")
        self.assertEqual(result["intent"], "GENERAL_SECURITY")
        self.assertTrue(result["fallback"])

    def test_triage_retrieval(self):
        result = self.search("triage suspicious alert and compare baseline evidence")
        self.assertEqual(result["intent"], "TRIAGE")
        self.assertTrue(any("triage" in item["category"] or "risk" in item["category"] for item in result["results"]))

    def test_mitre_mapping_retrieval(self):
        result = self.search("Map Kerberoasting T1558.003 to MITRE ATT&CK")
        self.assertEqual(result["intent"], "MITRE_MAPPING")
        self.assertTrue(any(item["technique"] == "T1558.003" for item in result["results"]))

    def test_ioc_retrieval(self):
        result = self.search("Analyze an IOC hash domain and correlate it with evidence")
        self.assertEqual(result["intent"], "IOC_ANALYSIS")
        self.assertTrue(any(item["category"] == "ioc_analysis" for item in result["results"]))

    def test_investigation_retrieval(self):
        result = self.search("Investigate suspicious PowerShell execution and collect process network evidence")
        self.assertEqual(result["intent"], "INVESTIGATION")
        self.assertTrue(any("PowerShell" in item["tags"] for item in result["results"]))

    def test_false_positive_retrieval(self):
        result = self.search("Could this suspicious PowerShell alert be a false positive from SCCM?")
        self.assertEqual(result["intent"], "FALSE_POSITIVE")
        self.assertTrue(any(item["category"] == "false_positive" for item in result["results"]))

    def test_incident_response_retrieval(self):
        result = self.search("What incident response next actions and escalation are recommended?")
        self.assertEqual(result["intent"], "INCIDENT_RESPONSE")
        self.assertTrue(any(item["category"] == "incident_response" for item in result["results"]))

    def test_threat_hunting_retrieval(self):
        result = self.search("Threat hunt for rare new network behavior against a baseline")
        self.assertEqual(result["intent"], "THREAT_HUNTING")
        self.assertTrue(any(item["category"] == "threat_hunting" for item in result["results"]))

    def test_risk_assessment_retrieval(self):
        result = self.search("Assess alert risk severity and confidence with corroborating evidence")
        self.assertEqual(result["intent"], "RISK_ASSESSMENT")
        self.assertTrue(any(item["category"] == "risk_assessment" for item in result["results"]))

    def test_kerberoasting_and_brute_force_signals(self):
        kerb = self.search("What should the analyst do after detecting Kerberoasting?")
        brute = self.search("Is this authentication alert likely brute force?")
        self.assertTrue(any(item["technique"] == "T1558.003" for item in kerb["results"]))
        self.assertTrue(any(item["technique"] == "T1110" for item in brute["results"]))

    def test_threshold_redundancy_budget_and_deterministic_order(self):
        first = self.search("suspicious network connection investigation evidence", top_k=8)
        second = self.search("suspicious network connection investigation evidence", top_k=8)
        self.assertEqual(first["results"], second["results"])
        self.assertLessEqual(len(first["results"]), 8)
        self.assertLessEqual(sum(len(item["snippet"]) for item in first["results"]), 4200)
        snippets = [item["snippet"] for item in first["results"]]
        self.assertEqual(len(snippets), len(set(snippets)))

    def test_empty_and_malformed_documents_are_safe(self):
        index = soc_rag.build_index([
            {"id": "valid", "title": "Valid", "category": "investigation", "content": "Collect evidence.", "source": "test"},
            {"id": "missing-content", "title": "Malformed"},
            "not a document",
            {"id": "missing-metadata", "title": "Defaults", "content": "Review evidence."},
        ])
        self.assertEqual(index["document_count"], 2)
        self.assertEqual(index["skipped_documents"], 2)
        empty = soc_rag.search("", index=index)
        self.assertEqual(empty["results"], [])
        self.assertEqual(empty["status"], "NO_RELEVANT_CONTEXT")

    def test_platform_independence(self):
        elastic = self.search("Investigate suspicious PowerShell in Elastic")
        splunk = self.search("Investigate suspicious PowerShell in Splunk")
        self.assertTrue(elastic["results"])
        self.assertTrue(splunk["results"])
        self.assertTrue(all(item["platform"] == "any" for item in elastic["results"] + splunk["results"]))

    def test_soc_skills_and_mcp_sections_are_separate(self):
        request = "Investigate suspicious PowerShell execution in Elastic"
        decision = {"platform": "elastic", "skill": "security-alert-triage", "query_language": "ES|QL", "mcp": "elastic", "mcp_status": "VERIFIED"}
        skills = local_rag.search(request, decision=decision)
        soc = self.search(request)
        envelope = context_handoff.build_context(request, decision, skills, soc_result=soc, evidence_results=[{"event.action": "process_started"}])
        text = envelope["context_text"]
        self.assertIn("[OPERATIONAL_RAG]", text)
        self.assertIn("[SOC_ANALYST_RAG]", text)
        self.assertIn("[MCP_EVIDENCE]", text)
        self.assertIn("GUIDANCE_ONLY: true", text)
        self.assertIn("[EVIDENCE 1]", text)
        self.assertLess(text.index("[SOC_ANALYST_RAG]"), text.index("[MCP_EVIDENCE]"))
        self.assertEqual(envelope["evidence_results"], [{"event.action": "process_started"}])
        self.assertIn("recommendations", envelope)
        self.assertIn("[SOC_RECOMMENDATIONS]", text)
        self.assertNotIn("automatic actions", envelope["recommendations"]["recommended_containment"][0].lower())

    def test_unified_recommendations_are_structured_and_evidence_first(self):
        for query, expected_type in (
            ("Investigate suspicious PowerShell execution on endpoint", "INVESTIGATION"),
            ("Malware detected on workstation", "CONTAINMENT"),
            ("Endpoint communicating with suspicious external IP", "CORRELATION"),
            ("Multiple failed logins followed by successful authentication", "INVESTIGATION"),
            ("prompt injection attempt", "INVESTIGATION"),
        ):
            result = self.search(query)
            structured = recommendations.build_recommendations(result)
            self.assertIn(structured["verdict"], {"SUSPICIOUS", "UNKNOWN"})
            self.assertEqual(structured["confidence"], "LOW" if result["results"] else "UNKNOWN")
            self.assertTrue(any(item["type"] == expected_type for item in structured["recommendations"]))
            self.assertTrue(structured["evidence_gaps"])
        unknown = recommendations.build_recommendations({"status": "NO_RELEVANT_CONTEXT", "results": []})
        self.assertEqual(unknown["verdict"], "UNKNOWN")
        self.assertTrue(any("Clarify" in item["action"] for item in unknown["recommendations"]))

    def test_recommend_api_preserves_retrieval_and_is_advisory(self):
        result = soc_rag.recommend("suspicious PowerShell execution on endpoint")
        self.assertTrue(result["retrieval_aware"])
        self.assertEqual(result["retrieval_status"], "RETRIEVED")
        self.assertTrue(result["knowledge_sources"])
        self.assertTrue(all(item["type"] != "AUTOMATED_ACTION" for item in result["recommendations"]))

    def test_lexical_mode_and_hybrid_deduplicate_exact_chunk(self):
        lexical = self.search("T1558.003 Kerberoasting", top_k=4)
        self.assertEqual(lexical["retrieval_mode"], "LEXICAL_ONLY")
        item = {"id": "doc-1", "chunk_id": "0", "title": "Exact", "technique": "T1059.001", "event_ids": [], "keywords": [], "score": 10.0, "snippet": "exact guidance"}
        vector_item = {**item, "score": 0.9}
        merged = soc_rag.HybridRetriever().fuse([item], [vector_item], "T1059.001", 4)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["retrieval_sources"], ["lexical", "vector"])
        self.assertGreater(merged[0]["score"], 1.0)
        vector_only = soc_rag.search("T1059.001", top_k=4, mode="vector")
        self.assertEqual(vector_only["retrieval_mode"], "VECTOR_UNAVAILABLE")

    def test_vector_failure_is_safe_and_does_not_replace_lexical(self):
        vector = soc_rag.VectorRetriever({"enabled": False})
        result = vector.search("prompt injection", 3)
        self.assertEqual(result["status"], "UNAVAILABLE")
        lexical = self.search("prompt injection attempt")
        self.assertTrue(lexical["results"])

    def test_qdrant_configuration_and_retriever_components(self):
        config = soc_rag.load_config()["qdrant"]
        self.assertEqual(config["collection"], "soc_knowledge")
        self.assertEqual(config["vector_size"], 384)
        self.assertAlmostEqual(config["lexical_weight"] + config["vector_weight"], 1.0)
        self.assertIsInstance(soc_rag.LexicalRetriever(), soc_rag.LexicalRetriever)
        self.assertIsInstance(soc_rag.VectorRetriever(), soc_rag.VectorRetriever)
        self.assertIsInstance(soc_rag.HybridRetriever(), soc_rag.HybridRetriever)


if __name__ == "__main__":
    unittest.main()
