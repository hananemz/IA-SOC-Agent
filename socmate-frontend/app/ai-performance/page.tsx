'use client';

import React, { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';
import AgentChatPanel from '@/components/AgentChatPanel';
import { getPerformanceMetrics, AIPerformanceMetrics } from '@/lib/api';
import { Activity, ShieldCheck, Zap, ThumbsUp, ThumbsDown, MessageSquare } from 'lucide-react';

export default function AIPerformancePage() {
  const [metrics, setMetrics] = useState<AIPerformanceMetrics | null>(null);
  const [isChatOpen, setIsChatOpen] = useState(false);

  useEffect(() => {
    getPerformanceMetrics().then(setMetrics);
  }, []);

  if (!metrics) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] text-gray-100 flex items-center justify-center">
        Loading AI telemetry and feedback summary...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-gray-100 flex">
      <Sidebar />
      <div className="flex-1 ml-64 flex flex-col min-w-0">
        <Header
          title="AI Performance & Feedback Summary"
          subtitle="Real-time telemetry on Codex Agent precision, false positive rate, skill latency, and human feedback loop"
          onOpenChat={() => setIsChatOpen(true)}
        />
        <main className="flex-1 p-8 space-y-8 overflow-y-auto">
          {/* Top KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-6">
            <div className="glass-card rounded-2xl p-6 border border-purple-500/20 space-y-2">
              <span className="text-xs font-bold uppercase tracking-wider text-gray-400">Overall Agent Accuracy</span>
              <div className="text-4xl font-black text-emerald-400">{metrics.overallAccuracy}%</div>
              <p className="text-xs text-gray-400">Based on human operator feedback</p>
            </div>
            <div className="glass-card rounded-2xl p-6 border border-purple-500/20 space-y-2">
              <span className="text-xs font-bold uppercase tracking-wider text-gray-400">False Positive Rate</span>
              <div className="text-4xl font-black text-purple-400">{metrics.falsePositiveRate}%</div>
              <p className="text-xs text-gray-400">Filtered automatically before escalation</p>
            </div>
            <div className="glass-card rounded-2xl p-6 border border-purple-500/20 space-y-2">
              <span className="text-xs font-bold uppercase tracking-wider text-gray-400">Positive Feedback</span>
              <div className="text-4xl font-black text-emerald-400 flex items-center space-x-2">
                <ThumbsUp className="w-6 h-6 mr-1" />
                <span>{metrics.feedbackSummary.positiveCount}</span>
              </div>
              <p className="text-xs text-gray-400">Correct agent skill executions</p>
            </div>
            <div className="glass-card rounded-2xl p-6 border border-purple-500/20 space-y-2">
              <span className="text-xs font-bold uppercase tracking-wider text-gray-400">Negative Feedback</span>
              <div className="text-4xl font-black text-rose-400 flex items-center space-x-2">
                <ThumbsDown className="w-6 h-6 mr-1" />
                <span>{metrics.feedbackSummary.negativeCount}</span>
              </div>
              <p className="text-xs text-gray-400">Requires skill re-training</p>
            </div>
          </div>

          {/* Feedback Summary Block & Skill Accuracies */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="glass-card rounded-2xl p-6 border border-purple-500/20 space-y-4">
              <h3 className="text-base font-bold text-white flex items-center space-x-2">
                <ThumbsUp className="w-5 h-5 text-purple-400" />
                <span>Skill Perceived Accuracy (Feedback Loop)</span>
              </h3>
              <div className="space-y-4 pt-2">
                {metrics.feedbackSummary.skillAccuracies.map((item) => (
                  <div key={item.skill} className="space-y-1.5">
                    <div className="flex justify-between text-xs">
                      <span className="font-semibold text-gray-300">{item.skill}</span>
                      <span className="font-bold text-emerald-400">{item.accuracy}%</span>
                    </div>
                    <div className="h-2 w-full bg-gray-800 rounded-full overflow-hidden">
                      <div style={{ width: `${item.accuracy}%` }} className="h-full bg-gradient-to-r from-purple-600 to-emerald-500 rounded-full" />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="glass-card rounded-2xl p-6 border border-purple-500/20 space-y-4">
              <h3 className="text-base font-bold text-white flex items-center space-x-2">
                <MessageSquare className="w-5 h-5 text-purple-400" />
                <span>Recent Human Comments on Agent Actions</span>
              </h3>
              <div className="space-y-3 pt-2">
                {metrics.feedbackSummary.recentComments.map((com) => (
                  <div key={com.id} className="p-3.5 rounded-xl bg-[#141420] border border-purple-500/10 space-y-1 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-purple-300">{com.itemTitle}</span>
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        com.verdict === 'correct' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
                      }`}>
                        {com.verdict === 'correct' ? '👍 Correct' : '👎 Incorrect'}
                      </span>
                    </div>
                    <p className="text-gray-200">"{com.comment}"</p>
                    <div className="text-[10px] text-gray-400">By {com.author} • {com.timestamp}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </main>
      </div>
      <AgentChatPanel isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />
    </div>
  );
}
