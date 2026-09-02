#!/usr/bin/env python3
"""
SOC Architecture End-to-End Benchmark
Pipeline: USER -> ROUTER -> SKILLS -> SOC RAG -> MCP -> SPLUNK/ELASTIC -> ANSWER
Compares Config A (WITHOUT Skills RAG) vs Config B (WITH Skills RAG)

Usage:
  python benchmark_end_to_end.py
  Results: benchmark_results.json + benchmark_report.md
"""
from __future__ import annotations
import json, math, os, re, statistics, sys, time
from pathlib import Path
from typing import Any

# ---- Paths Setup ----
PYTHON_PATH = r"C:\Users\lenovo\AppData\Local\Programs\Python\Python313\python.exe"
WORKSPACE = Path(os.getcwd())
ROUTER_DIR = Path(r"C:\Users\lenovo\.agents\skills-router\security-skill-router")
SKILLS_DIR = Path(r"C:\Users\lenovo\.agents\skills")
SKILLS_SPLUNK_DIR = Path(r"C:\Users\lenovo\.agents\skills-splunk")
SOC_RAG_DIR = ROUTER_DIR / "skills-rag"
REPEATS = 5

# Import Skills RAG after setting up the path
sys.path.insert(0, str(SOC_RAG_DIR))
import skills_rag
import soc_rag

def now_ms():
    return time.perf_counter() * 1000

def round2(v):
    return round(v, 2)

def stats_list(arr):
    if not arr:
        return {"avg": 0, "median": 0, "min": 0, "max": 0, "p95": 0}
    s = sorted(arr)
    avg = statistics.mean(s)
    med = statistics.median(s)
    min_v = s[0]
    max_v = s[-1]
    p95 = s[max(math.ceil(len(s) * 0.95) - 1, 0)]
    return {"avg": round2(avg), "median": round2(med), "min": round2(min_v), "max": round2(max_v), "p95": round2(p95)}

def estimate_tokens(text):
    return math.ceil(len(text.split()) * 1.3)

# ---- Platform Detection (Router Logic) ----
def detect_platform(query):
    q = query.lower()
    splunk_indicators = ["splunk", "spl ", "index=", "sourcetype=", "_internal", "saved search", "notable event", "enterprise security", "correlation search"]
    elastic_indicators = ["elasticsearch", "kibana", "es|ql", "|ql", "kql", "detection rule", "elastic security", "endpoint", "kerberoasting", "powershell"]
    
    splunk_count = sum(1 for ind in splunk_indicators if ind in q)
    elastic_count = sum(1 for ind in elastic_indicators if ind in q)
    
    cross_indicators = ["compare", "compar", "both", "les deux"]
    if any(ci in q for ci in cross_indicators) and splunk_count > 0 and elastic_count > 0:
        return "cross-platform", splunk_count, elastic_count
    
    if splunk_count > elastic_count:
        return "splunk", splunk_count, elastic_count
    if elastic_count > splunk_count:
        return "elastic", elastic_count, splunk_count
    if splunk_count > 0:
        return "splunk", splunk_count, elastic_count
    if elastic_count > 0:
        return "elastic", elastic_count, splunk_count
    return "unknown", 0, 0

def detect_task(query):
    q = query.lower()
    task_signals = {
        "alert_triage": ["triage", "alert", "notable", "classify"],
        "investigation": ["investigat", "analyse", "suspicious", "analyser", "recherche les evenements"],
        "ioc_analysis": ["ioc", "indicator", "hash", "enrich"],
        "mitre_mapping": ["mitre", "att&ck", "kerberoast", "technique"],
        "risk_assessment": ["risk", "severity", "priorit", "brute force", "eve", "probable"],
        "false_positive": ["false positive", "benign", "exception"],
        "threat_hunting": ["hunt", "baseline", "rare", "anomal"],
        "authentication": ["auth", "login", "credential", "ech", "authentication", "brute"],
    }
    for task, signals in task_signals.items():
        if any(s in q for s in signals):
            return task
    return "general_security"

def select_skill(platform, task):
    skill_map = {
        "splunk": {
            "alert_triage": "splunk-security-alert-triage",
            "investigation": "splunk-search",
            "authentication": "splunk-authentication",
            "ioc_analysis": "splunk-search",
            "mitre_mapping": "splunk-security-alert-triage",
            "risk_assessment": "splunk-authentication",
        },
        "elastic": {
            "alert_triage": "security-alert-triage",
            "investigation": "security-alert-triage",
            "authentication": "elasticsearch-authn",
            "ioc_analysis": "security-alert-triage",
            "mitre_mapping": "security-alert-triage",
            "risk_assessment": "security-alert-triage",
        }
    }
    return (skill_map.get(platform) or {}).get(task) or "unknown"

# ---- Test Cases ----
TEST_CASES = [
    {
        "id": "T1-BruteForce-Splunk",
        "name": "Authentication / Splunk - Brute Force",
        "query": "Recherche les echecs d'authentification suspects sur Splunk.",
        "platform": "splunk",
        "task": "authentication",
        "skill": "splunk-authentication",
        "mcp": "splunk-mcp-server",
    },
    {
        "id": "T2-Kerberoasting-Elastic",
        "name": "Kerberoasting / Elastic",
        "query": "Recherche les evenements lies a une attaque Kerberoasting dans Elastic et indique ce que l'analyste doit verifier.",
        "platform": "elastic",
        "task": "mitre_mapping",
        "skill": "security-alert-triage",
        "mcp": "elastic",
    },
    {
        "id": "T3-PowerShell-Elastic",
        "name": "PowerShell / Elastic",
        "query": "Analyse une activite PowerShell suspecte dans Elastic et indique les elements a verifier.",
        "platform": "elastic",
        "task": "investigation",
        "skill": "security-alert-triage",
        "mcp": "elastic",
    },
    {
        "id": "T4-BruteForce-Splunk",
        "name": "Brute Force / Splunk - Investigation",
        "query": "Recherche une eventuelle attaque Brute Force dans Splunk et explique comment l'investiguer.",
        "platform": "splunk",
        "task": "risk_assessment",
        "skill": "splunk-authentication",
        "mcp": "splunk-mcp-server",
    },
    {
        "id": "T5-IOC-Analysis",
        "name": "IOC Analysis",
        "query": "Analyse cet IOC et indique Quelles informations doivent etre recherchees dans le SIEM.",
        "platform": "elastic",
        "task": "ioc_analysis",
        "skill": "security-alert-triage",
        "mcp": "elastic",
    },
    {
        "id": "T6-CrossPlatform",
        "name": "Cross-platform Authentication Comparison",
        "query": "Compare les evenements d'authentification suspects presents dans Splunk et Elastic.",
        "platform": "cross-platform",
        "task": "investigation",
        "skill": "security-alert-triage",
        "mcp": "both",
    }
]

# ---- Benchmark Functions ----

def benchmark_router(query):
    \"\"\"Stage 1: Security Skill Router\"\"\"
    t0 = now_ms()
    platform, splunk_c, elastic_c = detect_platform(query)
    task = detect_task(query)
    skill = select_skill(platform, task)
    t1 = now_ms()
    return {
        \"time_ms\": round2(t1 - t0),
        \"platform\": platform,
        \"task\": task,
        \"skill\": skill,
    }

def benchmark_skills(platform, skill):
    \"\"\"Stage 2: Skills Loading (read real SKILL.md files)\"\"\"
    t0 = now_ms()
    total_size = 0
    total_tokens = 0
    files_loaded = []
    
    root_dir = SKILLS_SPLUNK_DIR if platform == \"splunk\" else SKILLS_DIR
    skill_file = root_dir / skill / \"SKILL.md\"
    
    if skill_file.exists():
        content = skill_file.read_text(encoding=\"utf-8\")
        total_size += len(content)
        total_tokens += estimate_tokens(content)
        files_loaded.append({\"path\": str(skill_file), \"size\": len(content)})
        
        # Check for references directory
        refs_dir = root_dir / skill / \"references\"
        if refs_dir.exists():
            for ref in sorted(refs_dir.iterdir()):
                if ref.is_file() and ref.suffix.lower() in {\".md\", \".txt\", \".json\"}:
                    try:
                        rc = ref.read_text(encoding=\"utf-8\")
                        total_size += len(rc)
                        total_tokens += estimate_tokens(rc)
                        files_loaded.append({\"path\": str(ref), \"size\": len(rc)})
                    except Exception:
                        pass
    
    t1 = now_ms()
    return {
        \"time_ms\": round2(t1 - t0),
        \"total_size\": total_size,
        \"total_tokens\": total_tokens,
        \"files_count\": len(files_loaded),
        \"skill\": skill,
    }

def benchmark_soc_rag(query):
    \"\"\"Stage 3a: SOC Analyst RAG (real Python call)\"\"\"
    t0 = now_ms()
    try:
        result = soc_rag.search(query, top_k=6)
    except Exception as e:
        result = {\"status\": \"ERROR\", \"error\": str(e), \"results\": [], \"intent\": \"GENERAL_SECURITY\"}
    t1 = now_ms()
    
    soc_chars = sum(len(r.get(\"snippet\", \"\")) for r in result.get(\"results\", []))
    return {
        \"time_ms\": round2(t1 - t0),
        \"status\": result.get(\"status\", \"ERROR\"),
        \"intent\": result.get(\"intent\", \"GENERAL_SECURITY\"),
        \"intent_confidence\": result.get(\"intent_confidence\", 0),
        \"chunks\": len(result.get(\"results\", [])),
        \"context_chars\": soc_chars,
        \"retrieval_status\": result.get(\"status\", \"ERROR\"),
    }

def benchmark_skills_rag(query, decision):
    \"\"\"Stage 3b: Skills RAG - skills_rag.py (real Python call)\"\"\"
    t0 = now_ms()
    try:
        result = skills_rag.search(query, decision=decision)
    except Exception as e:
        result = {\"status\": \"ERROR\", \"error\": str(e), \"results\": []}
    t1 = now_ms()
    
    sk_chars = sum(len(r.get(\"snippet\", \"\")) for r in result.get(\"results\", []))
    return {
        \"time_ms\": round2(t1 - t0),
        \"status\": result.get(\"status\", \"ERROR\"),
        \"chunks\": len(result.get(\"results\", [])),
        \"context_chars\": sk_chars,
        \"platform_detected\": result.get(\"platform\", \"unknown\"),
        \"skill_matched\": result.get(\"skill\", \"unknown\"),
    }

# ---- Orchestrator ----
def run_test_case(test_case, with_skills_rag, iteration):
    \"\"\"Run a single benchmark iteration for one test case.\"\"\"
    chrono = {}
    t_start = now_ms()
    
    # Stage 1: Router
    t0 = now_ms()
    router = benchmark_router(test_case[\"query\"])
    chrono[\"router\"] = round2(now_ms() - t0)
    
    # Stage 2: Skills Loading
    t1 = now_ms()
    skills = benchmark_skills(test_case[\"platform\"], test_case[\"skill\"])
    chrono[\"skills\"] = round2(now_ms() - t1)
    
    # Stage 3a: SOC Analyst RAG
    t2 = now_ms()
    soc_rag_result = benchmark_soc_rag(test_case[\"query\"])
    chrono[\"soc_rag\"] = round2(now_ms() - t2)
    
    # Stage 3b: Skills RAG (only in Config B)
    skills_rag_result = None
    if with_skills_rag:
        t3 = now_ms()
        decision = {
            \"platform\": test_case[\"platform\"],
            \"skill\": test_case[\"skill\"],
            \"task\": test_case[\"task\"],
        }
        skills_rag_result = benchmark_skills_rag(test_case[\"query\"], decision)
        chrono[\"skills_rag\"] = round2(now_ms() - t3)
    
    # Total context calculation
    total_context = skills[\"total_size\"] + soc_rag_result[\"context_chars\"]
    if skills_rag_result:
        total_context += skills_rag_result[\"context_chars\"]
    
    # Stage 5: Qwen (simulated - no API endpoint)
    qwen = simulate_qwen(total_context)
    
    total_time = now_ms() - t_start
    
    return {
        \"iteration\": iteration,
        \"cold_start\": iteration == 1,
        \"router\": {**chrono, **router},
        \"skills\": {**chrono, **skills},
        \"soc_rag\": {**chrono, **soc_rag_result},
        \"skills_rag\": chrono.get(\"skills_rag\") or 0,
        \"skills_rag_detail\": skills_rag_result,
        \"qwen\": qwen,
        \"total_context_chars\": total_context,
        \"local_pipeline_ms\": round2(chrono[\"router\"] + chrono[\"skills\"] + chrono[\"soc_rag\"] + (chrono.get(\"skills_rag\") or 0)),
    }

def simulate_qwen(context_size):
    \"\"\"Simulated Qwen-2.5-72B-Instruct timing (no API endpoint available).\"\"\"
    input_tokens = math.ceil(context_size / 4)
    output_tokens = 150  # Typical SOC analyst response
    ttft = 800 + (context_size / 1000) * 15
    generation_time = output_tokens / 50 * 1000
    return {
        \"ttft\": round2(ttft),
        \"generation_ms\": round2(generation_time),
        \"total_ms\": round2(ttft + generation_time),
        \"input_tokens\": input_tokens,
        \"output_tokens\": output_tokens,
        \"note\": \"SIMULATED - no Qwen API endpoint available\",
    }

def run_full_benchmark():
    \"\"\"Run all test cases with both configurations.\"\"\"
    print(\"\\n\" + \"=\" * 70)
    print(\"  SOC ARCHITECTURE END-to-END BENCHMARK\")
    print(f\"  {time.strftime('%Y-%m-%d %H:%M:%S %Z')}\")
    print(\"=\" * 70)
    print(f\"\\nPython: {PYTHON_PATH}\")
    print(f\"Repeats per test: {REPEATS}\")
    print(f\"Test cases: {len(TEST_CASES)}\")
    print(f\"Configurations: WITH Skills RAG, WITHOUT Skills RAG\")
    
    all_results = {
        \"with_skills_rag\": [],
        \"without_skills_rag\": [],
        \"timestamp\": time.strftime(\"%Y-%m-%dT%H:%M:%S\"),
        \"python\": PYTHON_PATH,
    }
    
    for tc in TEST_CASES:
        print(f\"\\n--- {tc['id']}: {tc['name']} ---\")
        
        # Config B: WITH Skills RAG
        print(\"  Config B: WITH Skills RAG...\")
        iterations_with = []
        for i in range(REPEATS):
            result = run_test_case(tc, with_skills_rag=True, iteration=i+1)
            iterations_with.append(result)
            print(f\"    Iteration {i+1}: local={result['local_pipeline_ms']:.1f}ms\")
        
        all_results[\"with_skills_rag\"].append({
            \"test_case\": tc[\"id\"],
            \"test_name\": tc[\"name\"],
            \"platform\": tc[\"platform\"],
            \"iterations\": iterations_with,
        })
        
        # Config A: WITHOUT Skills RAG
        print(\"  Config A: WITHOUT Skills RAG...\")
        iterations_without = []
        for i in range(REPEATS):
            result = run_test_case(tc, with_skills_rag=False, iteration=i+1)
            iterations_without.append(result)
            print(f\"    Iteration {i+1}: local={result['local_pipeline_ms']:.1f}ms\")
        
        all_results[\"without_skills_rag\"].append({
            \"test_case\": tc[\"id\"],
            \"test_name\": tc[\"name\"],
            \"platform\": tc[\"platform\"],
            \"iterations\": iterations_without,
        })
    
    return all_results

# ---- Report Generator ----
def generate_report(all_results):
    \"\"\"Generate aggregated report from all benchmark results.\"\"\"
    with_data = all_results[\"with_skills_rag\"]
    without_data = all_results[\"without_skills_rag\"]
    
    # Collect all latencies per component
    def collect_latencies(data, component):
        values = []
        for run in data:
            for iter in run[\"iterations\"]:
                if component in iter:
                    if isinstance(iter[component], dict):
                        values.append(iter[component].get(\"time_ms\", 0))
                    else:
                        values.append(iter[component])
        return values
    
    report = {
        \"summary\": {
            \"timestamp\": all_results[\"timestamp\"],
            \"python\": all_results[\"python\"],
            \"test_cases\": len(TEST_CASES),
            \"repeats\": REPEATS,
            \"total_executions\": len(TEST_CASES) * REPEATS * 2,
            \"cold_starts\": len(TEST_CASES) * 2,
            \"warm_starts\": len(TEST_CASES) * (REPEATS - 1) * 2,
        },
        \"latency\": {},
        \"comparison\": {},
        \"analysis\": {},
    }
    
    # Aggregated latency stats for both configs
    for config_key, config_label in [(\"with_skills_rag\", \"with_skills_rag\"), (\"without_skills_rag\", \"without_skills_rag\")]:
        data = all_results.get(config_key, [])
        latency_stats = {}
        
        # Router
        router_vals = collect_latencies(data, \"router\")
        latency_stats[\"router\"] = stats_list(router_vals)
        
        # Skills
        skills_vals = collect_latencies(data, \"skills\")
        latency_stats[\"skills\"] = stats_list(skills_vals)
        
        # SOC RAG
        soc_vals = collect_latencies(data, \"soc_rag\")
        latency_stats[\"soc_rag\"] = stats_list(soc_vals)
        
        # Skills RAG (only for WITH config)
        if config_key == \"with_skills_rag\":
            sk_vals = collect_latencies(data, \"skills_rag\")
            latency_stats[\"skills_rag\"] = stats_list(sk_vals)
        
        # Qwen (simulated)
        qwen_ttft = []
        qwen_gen = []
        for run in data:
            for iter in run[\"iterations\"]:
                qwen_ttft.append(iter[\"qwen\"][\"ttft\"])
                qwen_gen.append(iter[\"qwen\"][\"generation_ms\"])
        latency_stats[\"qwen\"] = {
            \"ttft\": stats_list(qwen_ttft),
            \"generation\": stats_list(qwen_gen),
        }
        
        # End-to-end local (real measured)
        local_vals = []
        for run in data:
            for iter in run[\"iterations\"]:
                local_vals.append(iter[\"local_pipeline_ms\"])
        latency_stats[\"end_to_end_local\"] = stats_list(local_vals)
        
        report[\"latency\"][config_label] = latency_stats
    
    # Skills RAG comparison
    avg_with = sum(
        run[\"local_pipeline_ms\"]
        for run in with_data
        for iter in run[\"iterations\"]
    ) / (len(TEST_CASES) * REPEATS)
    
    avg_without = sum(
        run[\"local_pipeline_ms\"]
        for run in without_data
        for iter in run[\"iterations\"]
    ) / (len(TEST_CASES) * REPEATS)
    
    avg_context_with = sum(
        iter[\"total_context_chars\"]
        for run in with_data
        for iter in run[\"iterations\"]
    ) / (len(TEST_CASES) * REPEATS)
    
    avg_context_without = sum(
        iter[\"total_context_chars\"]
        for run in without_data
        for iter in run[\"iterations\"]
    ) / (len(TEST_CASES) * REPEATS)
    
    # Chunk counts
    avg_soc_chunks_with = sum(
        iter[\"soc_rag\"][\"chunks\"]
        for run in with_data
        for iter in run[\"iterations\"]
    ) / (len(TEST_CASES) * REPEATS)
    
    avg_skills_rag_chunks = sum(
        iter[\"skills_rag_detail\"][\"chunks\"]
        for run in with_data
        for iter in run[\"iterations\"]
        if iter.get(\"skills_rag_detail\")
    ) / max(1, sum(
        1
        for run in with_data
        for iter in run[\"iterations\"]
        if iter.get(\"skills_rag_detail\")
    ))
    
    diff = avg_with - avg_without
    pct_change = (diff / avg_without * 100) if avg_without > 0 else 0
    
    report[\"comparison\"] = {
        \"end_to_end_latency\": {
            \"with_skills_rag\": round2(avg_with),
            \"without_skills_rag\": round2(avg_without),
            \"difference_ms\": round2(diff),
            \"pct_change\": round(pct_change, 1),
        },
        \"context_size\": {
            \"with_skills_rag\": round(avg_context_with),
            \"without_skills_rag\": round(avg_context_without),
            \"difference_chars\": round(avg_context_with - avg_context_without),
        },
        \"retrieval\": {
            \"avg_soc_chunks_with\": round(avg_soc_chunks_with, 1),
            \"avg_skills_rag_extra_chunks\": round(avg_skills_rag_chunks, 1),
        },
    }
    
    # Verdict
    if abs(pct_change) < 5 and abs(avg_context_with - avg_context_without) < 500:
        verdict = \"NEGLIGIBLE - Skills RAG a un impact mesurable minimal sur la latence et le contexte\"
    elif pct_change > 0:
        verdict = f\"PENAUXEE DE LATENCE - Skills RAG ajoute {round2(pct_change)}% de latence avec +{round(avg_context_with - avg_context_without)} caracteres de contexte\"
    elif pct_change < 0:
        verdict = f\"GAIN DE PERF - Skills RAG reduit la latence de {round2(abs(pct_change))}%\"
    else:
        verdict = \"NEEDS_FURTHER_ANALYSIS\"
    
    # Analysis
    biggest = {}
    for comp, vals in report[\"latency\"][\"with_skills_rag\"].items():
        if isinstance(vals, dict) and \"avg\" in vals:
            biggest[comp] = vals[\"avg\"]
    
    biggest_comp = max(biggest.items(), key=lambda x: x[1])[0] if biggest else \"NONE\"
    
    report[\"analysis\"] = {
        \"biggest_latency_contributor\": biggest_comp,
        \"skills_rag_latency_impact_ms\": round2(diff),
        \"skills_rag_context_impact_chars\": round(avg_context_with - avg_context_without),
        \"verdict\": verdict,
    }
    
    return report

# ---- Entry Point ----
if __name__ == \"__main__\":
    print(\"\\nStarting benchmark...\")
    all_results = run_full_benchmark()
    
    # Save raw results
    results_path = WORKSPACE / \"benchmark_results.json\"
    with open(results_path, \"w\", encoding=\"utf-8\") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f\"\\nRaw results saved: {results_path}\")
    
    # Generate & save report
    report = generate_report(all_results)
    report_path = WORKSPACE / \"benchmark_analysis.json\"
    with open(report_path, \"w\", encoding=\"utf-8\") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f\"Analysis saved: {report_path}\")
    
    # Print Summary
    print(\"\\n\" + \"=\" * 70)
    print(\"  BENCHMARK SUMMARY\")
    print(\"=\" * 70)
    print(f\"\\nTest cases: {report['summary']['test_cases']}\")
    print(f\"Total executions: {report['summary']['total_executions']}\")
    print(f\"Configurations: WITH Skills RAG, WITHOUT Skills RAG\")
    
    print(\"\\n--- Latency With Skills RAG ---\")
    for comp, s in report[\"latency\"][\"with_skills_rag\"].items():
        if isinstance(s, dict) and \"avg\" in s:
            print(f\"  {comp}: avg={s['avg']}ms  median={s['median']}ms  min={s['min']}ms  max={s['max']}ms  p95={s['p95']}ms\")
    
    print(\"\\n--- Latency Without Skills RAG ---\")
    for comp, s in report[\"latency\"][\"without_skills_rag\"].items():
        if isinstance(s, dict) and \"avg\" in s:
            print(f\"  {comp}: avg={s['avg']}ms  median={s['median']}ms  min={s['min']}ms  max={s['max']}ms  p95={s['p95']}ms\")
    
    comp = report[\"comparison\"][\"end_to_end_latency\"]
    print(\"\\n--- Skills RAG Comparison ---\")
    print(f\"  With Skills RAG:   {comp['with_skills_rag']}ms avg\")
    print(f\"  Without Skills RAG: {comp['without_skills_rag']}ms avg\")
    print(f\"  Difference: {comp['difference_ms']}ms ({comp['pct_change']}%)\")
    
    ctx = report[\"comparison\"][\"context_size\"]
    print(f\"\\n  Context (with):   {ctx['with_skills_rag']} chars\")
    print(f\"  Context (without): {ctx['without_skills_rag']} chars\")
    print(f\"  Context diff: {ctx['difference_chars']} chars\")
    
    print(f\"\\n--- VERDICT ---\")
    print(f\"  {report['analysis']['verdict']}\")
    
    print(\"\\nDone. Files:\")
    print(f\"  {results_path.name}, {report_path.name}\")
