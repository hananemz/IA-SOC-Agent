'use client';

import React, { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';
import AgentChatPanel from '@/components/AgentChatPanel';
import { getReviewQueue, ReviewItem } from '@/lib/api';
import { Check, X } from 'lucide-react';

export default function ReviewQueuePage() {
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [isChatOpen, setIsChatOpen] = useState(false);

  useEffect(() => {
    getReviewQueue().then(setItems);
  }, []);

  const handleAction = (id: string, action: string) => {
    alert(`Successfully ${action}ed item ${id}`);
    setItems(items.filter(i => i.id !== id));
  };

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-gray-100 flex">
      <Sidebar />
      <div className="flex-1 ml-64 flex flex-col min-w-0">
        <Header
          title="Review Queue"
          subtitle="Human validation gate for Codex Agent critical actions & Evidence Validation pipeline"
          onOpenChat={() => setIsChatOpen(true)}
        />
        <main className="flex-1 p-8 space-y-6 overflow-y-auto">
          <div className="flex justify-between items-center">
            <span className="text-xs text-amber-400 font-semibold">{items.length} Pending Approvals Required</span>
          </div>

          <div className="grid grid-cols-1 gap-6">
            {items.map((item) => (
              <div key={item.id} className="glass-card rounded-2xl p-6 border border-amber-500/30 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <span className="text-xs font-bold text-amber-400">{item.id}</span>
                    <span className="text-xs font-bold text-white bg-purple-500/20 px-2.5 py-0.5 rounded-full">{item.client}</span>
                    <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30">{item.severity}</span>
                  </div>
                  <span className="text-xs text-gray-400">{item.timestamp}</span>
                </div>

                <div>
                  <h3 className="text-base font-bold text-white mb-1">{item.title}</h3>
                  <p className="text-xs text-purple-300 font-semibold">Recommended Action: {item.recommendedAction}</p>
                </div>

                <div className="p-4 rounded-xl bg-[#141420] border border-purple-500/20 space-y-2">
                  <span className="text-[11px] font-bold text-gray-400 uppercase">Agent Decision Rationale & Evidence:</span>
                  <p className="text-xs text-gray-200">{item.agentDecision}</p>
                  <p className="text-[11px] text-gray-400 font-mono">Evidence summary: {item.evidenceSummary}</p>
                </div>

                <div className="flex items-center justify-between pt-2">
                  <span className="text-xs text-emerald-400 font-semibold">Agent Confidence: {(item.confidence * 100).toFixed(0)}%</span>
                  <div className="flex space-x-3">
                    <button
                      onClick={() => handleAction(item.id, 'approve')}
                      className="px-4 py-2 rounded-xl bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 border border-emerald-500/40 text-xs font-semibold flex items-center space-x-1.5 transition-colors"
                    >
                      <Check className="w-4 h-4" />
                      <span>Approve & Execute</span>
                    </button>
                    <button
                      onClick={() => handleAction(item.id, 'reject')}
                      className="px-4 py-2 rounded-xl bg-rose-500/20 hover:bg-rose-500/30 text-rose-400 border border-rose-500/40 text-xs font-semibold flex items-center space-x-1.5 transition-colors"
                    >
                      <X className="w-4 h-4" />
                      <span>Reject</span>
                    </button>
                  </div>
                </div>
              </div>
            ))}
            {items.length === 0 && (
              <div className="glass-card rounded-2xl p-12 text-center text-gray-400">
                All agent decisions and evidence validations have been reviewed successfully!
              </div>
            )}
          </div>
        </main>
      </div>
      <AgentChatPanel isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />
    </div>
  );
}
