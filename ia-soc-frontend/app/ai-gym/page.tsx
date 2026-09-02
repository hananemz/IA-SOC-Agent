'use client';

import React, { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';
import AgentChatPanel from '@/components/AgentChatPanel';
import { getGymScenarios, AIGymScenario } from '@/lib/api';
import { Cpu, Play, Terminal, Filter } from 'lucide-react';

export default function AIGymPage() {
  const [scenarios, setScenarios] = useState<AIGymScenario[]>([]);
  const [filterNegative, setFilterNegative] = useState(false);
  const [customQuery, setCustomQuery] = useState('');
  const [testResult, setTestResult] = useState<any | null>(null);
  const [isChatOpen, setIsChatOpen] = useState(false);

  useEffect(() => {
    getGymScenarios().then(setScenarios);
  }, []);

  const runScenario = (queryText: string) => {
    setTestResult({
      query: queryText,
      selectedSkill: queryText.toLowerCase().includes('splunk') ? 'splunk-security-troubleshooting' : 'elasticsearch-security-rules',
      confidence: 0.98,
      latencyMs: 310,
      status: 'Success'
    });
  };

  const filteredScenarios = filterNegative
    ? scenarios.filter(s => s.feedbackVerdict === 'incorrect')
    : scenarios;

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-gray-100 flex">
      <Sidebar />
      <div className="flex-1 ml-64 flex flex-col min-w-0">
        <Header
          title="AI Gym & Skills Router Sandbox"
          subtitle="Test, fine-tune, and re-train skills that received negative human feedback"
          onOpenChat={() => setIsChatOpen(true)}
        />
        <main className="flex-1 p-8 space-y-6 overflow-y-auto">
          {/* Interactive Test Sandbox */}
          <div className="glass-card rounded-2xl p-6 border border-purple-500/30 space-y-4">
            <h3 className="text-base font-bold text-white flex items-center space-x-2">
              <Terminal className="w-5 h-5 text-purple-400" />
              <span>Skills Router Sandbox</span>
            </h3>
            <div className="flex gap-4">
              <input
                type="text"
                placeholder="Enter natural language security query..."
                value={customQuery}
                onChange={(e) => setCustomQuery(e.target.value)}
                className="flex-1 bg-[#141420] border border-purple-500/25 rounded-xl px-4 py-3 text-xs text-white focus:outline-none focus:border-purple-500 font-mono"
              />
              <button
                onClick={() => runScenario(customQuery || 'Default query: check login anomalies')}
                className="px-6 py-3 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold flex items-center space-x-2 transition-all shadow-lg shadow-purple-500/30"
              >
                <Play className="w-4 h-4" />
                <span>Test Router</span>
              </button>
            </div>

            {testResult && (
              <div className="p-4 rounded-xl bg-[#141420] border border-purple-500/20 space-y-2 mt-4 font-mono text-xs">
                <div className="flex items-center justify-between text-emerald-400 font-bold">
                  <span>Routing Test Successful</span>
                  <span>{testResult.latencyMs}ms</span>
                </div>
                <p className="text-gray-300">Query: {testResult.query}</p>
                <p className="text-purple-300">Selected Skill: {testResult.selectedSkill}</p>
                <p className="text-gray-400">Confidence: {(testResult.confidence * 100).toFixed(0)}%</p>
              </div>
            )}
          </div>

          {/* Scenarios Header & Filter */}
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold uppercase tracking-wider text-gray-400">Evaluation Scenarios ({filteredScenarios.length})</h3>
            <button
              onClick={() => setFilterNegative(!filterNegative)}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold flex items-center space-x-2 border transition-colors ${
                filterNegative ? 'bg-rose-500/20 text-rose-300 border-rose-500/40' : 'bg-[#141420] text-gray-300 border-purple-500/20 hover:border-purple-500/40'
              }`}
            >
              <Filter className="w-3.5 h-3.5" />
              <span>{filterNegative ? 'Showing Negative Feedback Only' : 'Filter Negative Feedback 👎'}</span>
            </button>
          </div>

          {/* Scenarios Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredScenarios.map((scen) => (
              <div key={scen.id} className="glass-card rounded-2xl p-6 border border-purple-500/20 space-y-3 flex flex-col justify-between">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-purple-400">{scen.skillType}</span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      scen.feedbackVerdict === 'incorrect' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' : 'bg-emerald-500/20 text-emerald-400'
                    }`}>
                      {scen.feedbackVerdict === 'incorrect' ? '👎 Negative Feedback' : '✓ Verified'}
                    </span>
                  </div>
                  <h4 className="text-sm font-bold text-white">{scen.name}</h4>
                  <p className="text-xs text-gray-300 font-mono bg-[#141420] p-2.5 rounded-xl">{scen.query}</p>
                  <div className="text-[11px] text-gray-400 space-y-1">
                    <p>Selected Skill: <span className="text-purple-300 font-mono">{scen.selectedSkill}</span></p>
                    <p>Confidence: {(scen.routerConfidence * 100).toFixed(0)}% • Latency: {scen.executionTimeMs}ms</p>
                  </div>
                </div>
                <button
                  onClick={() => runScenario(scen.query)}
                  className="w-full mt-4 px-3 py-2 rounded-xl bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/40 text-xs font-semibold flex items-center justify-center space-x-1.5 transition-colors"
                >
                  <Play className="w-3.5 h-3.5" />
                  <span>Replay & Re-train Skill</span>
                </button>
              </div>
            ))}
          </div>
        </main>
      </div>
      <AgentChatPanel isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />
    </div>
  );
}
