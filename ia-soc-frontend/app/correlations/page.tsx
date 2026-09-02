'use client';

import React, { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';
import AgentChatPanel from '@/components/AgentChatPanel';
import { getCorrelations, Correlation } from '@/lib/api';

export default function CorrelationsPage() {
  const [correlations, setCorrelations] = useState<Correlation[]>([]);
  const [isChatOpen, setIsChatOpen] = useState(false);

  useEffect(() => {
    getCorrelations().then(setCorrelations);
  }, []);

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-gray-100 flex">
      <Sidebar />
      <div className="flex-1 ml-64 flex flex-col min-w-0">
        <Header
          title="Correlations"
          subtitle="Agent-driven multi-vector correlation graph & intelligence chains"
          onOpenChat={() => setIsChatOpen(true)}
        />
        <main className="flex-1 p-8 space-y-6 overflow-y-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {correlations.map((corr) => (
              <div key={corr.id} className="glass-card rounded-2xl p-6 border border-purple-500/25 space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-purple-400">{corr.id}</span>
                  <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30">
                    Risk Score: {corr.riskScore}/100
                  </span>
                </div>
                <h3 className="text-base font-bold text-white">{corr.title}</h3>
                <p className="text-xs text-gray-300">{corr.summary}</p>
                <div className="space-y-2 pt-2">
                  <span className="text-[11px] font-bold text-gray-400 uppercase">Correlated Entities:</span>
                  <div className="flex flex-wrap gap-2">
                    {corr.entities.map((entity, i) => (
                      <span key={i} className="text-xs font-mono bg-[#141420] border border-purple-500/20 px-2.5 py-1 rounded-lg text-purple-300">
                        {entity}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="flex items-center justify-between pt-2 text-[11px] text-gray-400 border-t border-purple-500/10">
                  <span>Confidence: {(corr.confidence * 100).toFixed(0)}%</span>
                  <span>{corr.timestamp}</span>
                </div>
              </div>
            ))}
          </div>
        </main>
      </div>
      <AgentChatPanel isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />
    </div>
  );
}
