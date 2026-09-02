'use client';

import React, { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';
import AgentChatPanel from '@/components/AgentChatPanel';
import { getPlaybooks, PlaybookTemplate } from '@/lib/api';
import { Plus, Play } from 'lucide-react';

export default function PlaybooksPage() {
  const [playbooks, setPlaybooks] = useState<PlaybookTemplate[]>([]);
  const [isChatOpen, setIsChatOpen] = useState(false);

  useEffect(() => {
    getPlaybooks().then(setPlaybooks);
  }, []);

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-gray-100 flex">
      <Sidebar />
      <div className="flex-1 ml-64 flex flex-col min-w-0">
        <Header
          title="Playbook Templates"
          subtitle="Automated agent playbooks executable via Skills RAG & MCP"
          onOpenChat={() => setIsChatOpen(true)}
        />
        <main className="flex-1 p-8 space-y-6 overflow-y-auto">
          <div className="flex justify-between items-center">
            <span className="text-xs text-purple-300 font-semibold">{playbooks.length} Active Templates</span>
            <button
              onClick={() => alert('Create new playbook modal triggered')}
              className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold flex items-center space-x-2 transition-all shadow-lg shadow-purple-500/30"
            >
              <Plus className="w-4 h-4" />
              <span>New Playbook Template</span>
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {playbooks.map((pb) => (
              <div key={pb.id} className="glass-card rounded-2xl p-6 border border-purple-500/25 space-y-4 flex flex-col justify-between">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-purple-400">{pb.version}</span>
                    <span className="text-[10px] bg-purple-500/20 text-purple-300 px-2.5 py-0.5 rounded-full font-semibold">{pb.category}</span>
                  </div>
                  <h3 className="text-base font-bold text-white">{pb.name}</h3>
                  <p className="text-xs text-gray-400"><strong className="text-gray-300">Trigger:</strong> {pb.triggers}</p>
                  <div className="space-y-1.5 pt-2">
                    <span className="text-[11px] font-bold text-gray-400 uppercase">Skills Sequence:</span>
                    <div className="space-y-1">
                      {pb.skillsSequence.map((skill, i) => (
                        <div key={i} className="text-xs font-mono bg-[#141420] border border-purple-500/15 px-3 py-1.5 rounded-xl text-purple-300 flex items-center justify-between">
                          <span>{i+1}. {skill}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
                <div className="flex items-center justify-between pt-4 border-t border-purple-500/10">
                  <span className="text-[11px] text-emerald-400 font-semibold">{pb.autoExecute ? '⚡ Auto-Execute' : '👤 Manual Review'}</span>
                  <button
                    onClick={() => alert(`Test run for playbook ${pb.id}`)}
                    className="px-3 py-1.5 rounded-xl bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/40 text-xs font-semibold flex items-center space-x-1"
                  >
                    <Play className="w-3.5 h-3.5" />
                    <span>Test Run</span>
                  </button>
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
