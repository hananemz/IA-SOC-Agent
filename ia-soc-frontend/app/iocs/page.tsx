'use client';

import React, { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';
import AgentChatPanel from '@/components/AgentChatPanel';
import { getIOCs, IOC } from '@/lib/api';
import { Search } from 'lucide-react';

export default function IOCsPage() {
  const [iocs, setIOCs] = useState<IOC[]>([]);
  const [search, setSearch] = useState('');
  const [isChatOpen, setIsChatOpen] = useState(false);

  useEffect(() => {
    getIOCs().then(setIOCs);
  }, []);

  const filtered = iocs.filter(i => i.value.toLowerCase().includes(search.toLowerCase()) || i.source.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-gray-100 flex">
      <Sidebar />
      <div className="flex-1 ml-64 flex flex-col min-w-0">
        <Header
          title="Indicators of Compromise (IOCs)"
          subtitle="Threat intelligence indicators extracted by SOC RAG & MCP feeds"
          onOpenChat={() => setIsChatOpen(true)}
        />
        <main className="flex-1 p-8 space-y-6 overflow-y-auto">
          <div className="flex items-center justify-between glass-card p-4 rounded-2xl">
            <div className="relative w-96">
              <Search className="absolute left-3.5 top-3 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search IOC value or source..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full bg-[#141420] border border-purple-500/25 rounded-xl pl-10 pr-4 py-2 text-xs text-white focus:outline-none focus:border-purple-500"
              />
            </div>
            <span className="text-xs text-purple-300 font-semibold">{filtered.length} Active IOCs</span>
          </div>

          <div className="glass-card rounded-2xl overflow-hidden border border-purple-500/20">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-purple-500/20 bg-[#12121d] text-[11px] font-bold text-gray-400 uppercase tracking-wider">
                  <th className="py-3.5 px-6">Type</th>
                  <th className="py-3.5 px-6">IOC Value</th>
                  <th className="py-3.5 px-6">Source</th>
                  <th className="py-3.5 px-6">Confidence</th>
                  <th className="py-3.5 px-6">Threat Actor</th>
                  <th className="py-3.5 px-6">Last Seen</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-purple-500/10 text-xs">
                {filtered.map((ioc) => (
                  <tr key={ioc.id} className="hover:bg-purple-500/[0.03] transition-colors">
                    <td className="py-4 px-6 font-bold text-purple-400">{ioc.type}</td>
                    <td className="py-4 px-6 font-mono text-white">{ioc.value}</td>
                    <td className="py-4 px-6 text-gray-300">{ioc.source}</td>
                    <td className="py-4 px-6 font-semibold text-emerald-400">{ioc.confidence}%</td>
                    <td className="py-4 px-6 text-gray-300">{ioc.threatActor || 'Unknown'}</td>
                    <td className="py-4 px-6 text-gray-400">{ioc.lastSeen}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </main>
      </div>
      <AgentChatPanel isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />
    </div>
  );
}
