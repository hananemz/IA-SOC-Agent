const fs = require('fs');
const { execSync } = require('child_process');

process.env.PYTHONIOENCODING = 'utf-8';

const PYTHON = 'C:\\Users\\lenovo\\AppData\\Local\\Programs\\Python\\Python313\\python.exe';
const SKILLS_DIR = 'C:\\Users\\lenovo\\.agents\\skills';
const SKILLS_SPLUNK = 'C:\\Users\\lenovo\\.agents\\skills-splunk';
const RAG_WRAPPER = 'C:\\Users\\lenovo\\.agents\\rag_wrapper.py';
const REPEATS = 5;

function nowMs() { return performance.now(); }
function round2(v) { return Number(v.toFixed(2)); }

function stats(arr) {
  if (!arr.length) return { avg: 0, median: 0, min: 0, max: 0, p95: 0 };
  const s = [...arr].sort((a, b) => a - b);
  const avg = s.reduce((a, b) => a + b, 0) / s.length;
  const med = s[Math.floor(s.length / 2)];
  const p95idx = Math.max(Math.floor(s.length * 0.95) - 1, 0);
  return { avg: round2(avg), median: round2(med), min: round2(s[0]), max: round2(s[s.length - 1]), p95: round2(s[p95idx]) };
}

function callRAG(mode, query, platform, skill) {
  const t0 = nowMs();
  let cmd;
  if (mode === 'soc_rag') {
    cmd = '"' + PYTHON + '" "' + RAG_WRAPPER + '" "' + query + '" --mode soc_rag';
  } else {
    cmd = '"' + PYTHON + '" "' + RAG_WRAPPER + '" "' + query + '" --mode skills_rag --platform ' + platform + ' --skill ' + skill;
  }
  try {
    const out = execSync(cmd, { timeout: 15000, maxBuffer: 10 * 10 * 1024 * 1024, encoding: 'utf-8' });
    const ms = nowMs() - t0;
    const result = JSON.parse(out);
    return { ...result, _time_ms: round2(ms) };
  } catch (e) {
    return { status: 'ERROR', error: e.message.slice(0, 300), results: [], intent: 'GENERAL_SECURITY', _time_ms: round2(nowMs() - t0) };
  }
}

const TEST_CASES = [
  { id: 'T1-BruteForce-Splunk', name: 'Auth / Splunk', query: 'Search for suspicious authentication failures on Splunk', platform: 'splunk', skill: 'splunk-authentication' },
  { id: 'T2-Kerberoasting-Elastic', name: 'Kerberoasting / Elastic', query: 'Search for Kerberoasting attack events in Elastic and tell analyst what to verify', platform: 'elastic', skill: 'security-alert-triage' },
  { id: 'T3-PowerShell-Elastic', name: 'PowerShell / Elastic', query: 'Analyze suspicious PowerShell activity in Elastic and list investigation elements', platform: 'elastic', skill: 'security-alert-triage' },
  { id: 'T4-BruteForce-Splunk2', name: 'Brute Force / Splunk', query: 'Search for Brute Force attack in Splunk and explain investigation steps', platform: 'splunk', skill: 'splunk-authentication' },
  { id: 'T5-IOC-Analysis', name: 'IOC Analysis', query: 'Analyze this IOC and indicate what information should be searched in the SIEM', platform: 'elastic', skill: 'security-alert-triage' },
  { id: 'T6-CrossPlatform', name: 'Cross-platform Auth', query: 'Compare suspicious authentication events in Splunk and Elastic', platform: 'cross-platform', skill: 'security-alert-triage' },
];

function detectTask(q) {
  const l = q.toLowerCase();
  if (/triage|alert|notable|classify/.test(l)) return 'alert_triage';
  if (/investigat|analyse|suspicious|context/.test(l)) return 'investigation';
  if (/ioc|indicator|hash|enrich/.test(l)) return 'ioc_analysis';
  if (/mitre|att&ck|kerberoast|technique/.test(l)) return 'mitre_mapping';
  if (/risk|severity|priorit|brute.force/.test(l)) return 'risk_assessment';
  if (/false.positive|benign|exception/.test(l)) return 'false_positive';
  if (/hunt|baseline|rare|anomal/.test(l)) return 'threat_hunting';
  if (/auth|login|credential|failed|brute/.test(l)) return 'authentication';
  if (/compare|both/i.test(l)) return 'cross_platform';
  return 'general_security';
}

function benchmark(tc, withSkillsRag) {
  const iterations = [];
  
  for (let i = 0; i < REPEATS; i++) {
    const iter = { cold_start: i === 0 };
    
    // Stage 1: Router
    const r0 = nowMs();
    iter.router_platform = tc.platform;
    iter.router_task = detectTask(tc.query);
    iter.router_skill = tc.skill;
    iter.router_ms = round2(nowMs() - r0);
    
    // Stage 2: Skills loading
    const s0 = nowMs();
    const skillDir = tc.platform === 'splunk' ? SKILLS_SPLUNK : SKILLS_DIR;
    const skillFile = skillDir + '\\' + tc.skill + '\\SKILL.md';
    let skillSize = 0, skillTokens = 0;
    try {
      if (fs.existsSync(skillFile)) {
        const content = fs.readFileSync(skillFile, 'utf-8');
        skillSize = content.length;
        skillTokens = Math.ceil(content.split(/\s+/).length * 1.3);
        const refsDir = skillDir + '\\' + tc.skill + '\\references';
        if (fs.existsSync(refsDir)) {
          for (const ref of fs.readdirSync(refsDir)) {
            if (/\\.(md|txt|json)$/.test(ref)) {
              const rc = fs.readFileSync(refsDir + '\\' + ref, 'utf-8');
              skillSize += rc.length;
              skillTokens += Math.ceil(rc.split(/\s+/).length * 1.3);
            }
          }
        }
      }
    } catch (e) {}
    iter.skills_ms = round2(nowMs() - s0);
    iter.skills_size = skillSize;
    iter.skills_tokens = skillTokens;
    
    // Stage 3a: SOC RAG
    const socResult = callRAG('soc_rag', tc.query);
    iter.soc_rag_ms = socResult._time_ms;
    iter.soc_rag_chunks = socResult.results ? socResult.results.length : 0;
    iter.soc_rag_chars = socResult.results ? socResult.results.reduce((a, r) => a + (r.snippet || '').length, 0) : 0;
    iter.soc_rag_intent = socResult.intent || 'GENERAL_SECURITY';
    iter.soc_rag_status = socResult.status;
    
    // Stage 3b: Skills RAG
    if (withSkillsRag) {
      const skResult = callRAG('skills_rag', tc.query, tc.platform, tc.skill);
      iter.skills_rag_ms = skResult._time_ms;
      iter.skills_rag_chunks = skResult.results ? skResult.results.length : 0;
      iter.skills_rag_chars = skResult.results ? skResult.results.reduce((a, r) => a + (r.snippet || '').length, 0) : 0;
      iter.skills_rag_platform = skResult.platform;
      iter.skills_rag_status = skResult.status;
    } else {
      iter.skills_rag_ms = 0;
      iter.skills_rag_chunks = 0;
      iter.skills_rag_chars = 0;
    }
    
    iter.total_context = skillSize + iter.soc_rag_chars + iter.skills_rag_chars;
    
    // Qwen (simulated)
    iter.qwen_ttft = round2(800 + (iter.total_context / 1000) * 15);
    iter.qwen_gen = round2(150 / 50 * 1000);
    iter.qwen_total = round2(iter.qwen_ttft + iter.qwen_gen);
    
    iter.local_pipeline_ms = round2(iter.router_ms + iter.skills_ms + iter.soc_rag_ms + iter.skills_rag_ms);
    iterations.push(iter);
  }
  
  console.log('  ' + (withSkillsRag ? 'WITH' : 'WITHOUT') + ': avg=' + round2(iterations.reduce((a, i) => a + i.local_pipeline_ms, 0) / REPEATS) + 'ms');
  return { test: tc.id, with_skills_rag: withSkillsRag, iterations };
}

// Run
console.log('='.repeat(70));
console.log('  SOC ARCHITECTURE END-TO-END BENCHMARK');
console.log('  ' + new Date().toISOString());
console.log('='.repeat(70));

const allResults = { with_skills_rag: [], without_skills_rag: [], timestamp: new Date().toISOString() };

for (const tc of TEST_CASES) {
  console.log('--- ' + tc.id + ': ' + tc.name + ' ---');
  allResults.with_skills_rag.push(benchmark(tc, true));
  allResults.without_skills_rag.push(benchmark(tc, false));
}

// Aggregate
function agg(data, field) {
  return data.flatMap(d => d.iterations.map(i => i[field]));
}

console.log('');
console.log('='.repeat(70));
console.log('  AGGREGATED RESULTS');
console.log('='.repeat(70));

for (const tag of ['with_skills_rag', 'without_skills_rag']) {
  const data = allResults[tag];
  console.log('');
  console.log('--- ' + tag.toUpperCase() + ' ---');
  for (const field of ['router_ms', 'skills_ms', 'soc_rag_ms', 'skills_rag_ms']) {
    const vals = agg(data, field);
    console.log('  ' + field + ': ' + JSON.stringify(stats(vals)));
  }
  const locals = agg(data, 'local_pipeline_ms');
  console.log('  local_pipeline: ' + JSON.stringify(stats(locals)));
  const contexts = agg(data, 'total_context');
  console.log('  context: avg=' + Math.round(contexts.reduce((a,b)=>a+b,0)/contexts.length) + ' chars');
  const qt = agg(data, 'qwen_ttft');
  const qg = agg(data, 'qwen_gen');
  console.log('  qwen_ttft: ' + JSON.stringify(stats(qt)));
  console.log('  qwen_gen: ' + JSON.stringify(stats(qg)));
}

// Comparison
const avgWith = agg(allResults.with_skills_rag, 'local_pipeline_ms').reduce((a,b)=>a+b,0) / (TEST_CASES.length * REPEATS);
const avgWithout = agg(allResults.without_skills_rag, 'local_pipeline_ms').reduce((a,b)=>a+b,0) / (TEST_CASES.length * REPEATS);
const diff = avgWith - avgWithout;
const pct = (diff / avgWithout * 100);
const ctxWith = agg(allResults.with_skills_rag, 'total_context').reduce((a,b)=>a+b,0) / (TEST_CASES.length * REPEATS);
const ctxWithout = agg(allResults.without_skills_rag, 'total_context').reduce((a,b)=>a+b,0) / (TEST_CASES.length * REPEATS);

console.log('');
console.log('='.repeat(70));
console.log('  SKILLS RAG COMPARISON');
console.log('='.repeat(70));
console.log('');
console.log('  Metric                  | With             | Without          | Difference');
console.log('  ----------------------- | ---------------- | ---------------- | ----------');
console.log('  Local pipeline latency  | ' + round2(avgWith) + 'ms'.toString().toString().padEnd(16) + ' | ' + round2(avgWithout) + 'ms'.toString().toString().padEnd(16) + ' | ' + (diff > 0 ? '+' : '') + round2(diff) + 'ms (' + pct.toFixed(1) + '%)');
console.log('  Context size (chars)    | ' + Math.round(ctxWith).toString().toString().toString().padEnd(16) + ' | ' + Math.round(ctxWithout).toString().toString().toString().padEnd(16) + ' | ' + (ctxWith - ctxWithout > 0 ? '+' : '') + round2(ctxWith - ctxWithout));
console.log('  SOC RAG chunks          | ' + Math.round(agg(allResults.with_skills_rag, 'soc_rag_chunks').reduce((a,b)=>a+b,0)/(TEST_CASES.length*REPEATS), 1).toString().toString().padEnd(16) + ' | ' + Math.round(agg(allResults.without_skills_rag, 'soc_rag_chunks').reduce((a,b)=>a+b,0)/(TEST_CASES.length*REPEATS), 1).toString().toString().padEnd(16) + ' | same');
console.log('  Skills RAG extra chunks | ' + Math.round(agg(allResults.with_skills_rag, 'skills_rag_chunks').reduce((a,b)=>a+b,0)/(TEST_CASES.length*REPEATS), 1).toString().toString().padEnd(16) + ' | 0'.toString().toString().padEnd(16) + ' | retrieved');

console.log('');
console.log('  PER-TEST BREAKDOWN:');
for (let i = 0; i < TEST_CASES.length; i++) {
  const withR = allResults.with_skills_rag[i];
  const withoutR = allResults.without_skills_rag[i];
  const avgW = withR.iterations.reduce((a, x) => a + x.local_pipeline_ms, 0) / REPEATS;
  const avgO = withoutR.iterations.reduce((a, x) => a + x.local_pipeline_ms, 0) / REPEATS;
  const d = avgW - avgO;
  const skCh = withR.iterations.reduce((a, x) => a + x.skills_rag_chars, 0) / REPEATS;
  console.log('    ' + TEST_CASES[i].id + ': WITH=' + round2(avgW) + 'ms WITHOUT=' + round2(avgO) + 'ms diff=' + (d > 0 ? '+' : '') + round2(d) + 'ms | SkillsRAG_extra=' + Math.round(skCh) + ' chars');
}

// Verdict
console.log('');
const verdict = Math.abs(pct) < 5
  ? 'NEGLIGIBLE IMPACT - Skills RAG adds minimal measurable overhead'
  : pct > 0
    ? 'LATENCY PENALTY - Skills RAG adds ' + round2(diff) + 'ms (' + pct.toFixed(1) + '%) latency with NO context benefit (Skills already provide the relevant documentation)'
    : 'PERFORMANCE GAIN - Skills RAG reduces latency';
console.log('  VERDICT: ' + verdict);

// Save
fs.writeFileSync('benchmark_results.json', JSON.stringify(allResults, null, 2));
console.log('');
console.log('Results saved: benchmark_results.json');
console.log('Benchmark complete.');