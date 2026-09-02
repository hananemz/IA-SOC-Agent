import unittest

import evidence_validation as ev


class EvidenceValidationTests(unittest.TestCase):
    def test_fully_proven_process_claim(self):
        result = ev.validate_evidence([{"host.name": "WIN-SRV01", "user.name": "admin", "process.name": "powershell.exe", "process.command_line": "powershell -enc X", "@timestamp": "2026-08-30T10:00:00Z"}], platform="elastic")
        claims = result["claims"]
        self.assertEqual(result["evidence_confidence"], "MEDIUM")  # inferred suspicion is also surfaced
        self.assertTrue(any(item["status"] == ev.PROVEN and "PowerShell" in item["claim"] or item["status"] == ev.PROVEN and "powershell.exe" in item["claim"] for item in claims))
        self.assertTrue(all(refs for item in claims if item["status"] == ev.PROVEN for refs in [item["evidence_refs"]]))

    def test_partially_supported_and_inferred_claims(self):
        result = ev.validate_evidence([{"process": "powershell.exe", "user": "admin"}, {"process": "powershell.exe", "host": "WIN-01"}], claims=["The activity may be suspicious", "Data exfiltration occurred"])
        by_claim = {item["claim"]: item for item in result["claims"]}
        self.assertEqual(by_claim["The activity may be suspicious"]["status"], ev.INFERRED)
        self.assertEqual(by_claim["Data exfiltration occurred"]["status"], ev.UNKNOWN)
        self.assertTrue(any(item["status"] == ev.SUPPORTED for item in result["claims"]))

    def test_missing_network_and_endpoint_evidence(self):
        result = ev.validate_evidence([{"process.name": "cmd.exe"}], claims=["A network connection occurred", "Persistence was established", "Data exfiltration occurred"])
        statuses = {item["claim"]: item for item in result["claims"]}
        self.assertEqual(statuses["A network connection occurred"]["status"], ev.UNKNOWN)
        self.assertIn("network telemetry", statuses["A network connection occurred"]["missing_evidence"])
        self.assertIn("endpoint configuration evidence", statuses["Persistence was established"]["missing_evidence"])
        self.assertIn("DLP telemetry", statuses["Data exfiltration occurred"]["missing_evidence"])

    def test_conflicting_evidence_is_not_resolved(self):
        result = ev.validate_evidence([{"host": "A"}, {"host": "B"}])
        claim = next(item for item in result["claims"] if item["claim"] == "Host was observed")
        self.assertEqual(claim["status"], ev.UNKNOWN)
        self.assertEqual(claim["evidence_refs"], ["EVIDENCE-1", "EVIDENCE-2"])

    def test_empty_and_malformed_results_do_not_create_evidence(self):
        result = ev.validate_evidence([None, "not a record", {}])
        self.assertEqual(result["evidence_count"], 0)
        self.assertEqual(result["malformed_evidence_count"], 3)
        self.assertEqual(result["claims"][0]["evidence_refs"], [])
        self.assertEqual(result["evidence_confidence"], "UNKNOWN")

    def test_elastic_and_splunk_records_are_provider_neutral(self):
        elastic = ev.validate_evidence([{"_id": "elastic-1", "host.name": "es-host", "process.name": "powershell.exe"}], platform="elastic")
        splunk = ev.validate_evidence([{"_time": "2026-08-30T10:00:00Z", "host": "splunk-host", "process": "bash"}], platform="splunk")
        self.assertEqual(elastic["claims"][0]["evidence_refs"], ["elastic-1"])
        self.assertEqual(splunk["capabilities"]["platform"], "splunk")
        self.assertNotIn("network connection", splunk["capabilities"]["can_establish"])

    def test_summary_contains_all_sections_and_provenance(self):
        summary = ev.format_summary(ev.validate_evidence([]))
        for label in ("PROVEN", "SUPPORTED", "INFERRED", "UNKNOWN", "MISSING_EVIDENCE", "EVIDENCE CONFIDENCE"):
            self.assertIn(label, summary)


if __name__ == "__main__":
    unittest.main()
