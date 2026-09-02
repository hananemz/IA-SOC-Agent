'use client';

import React, { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';
import AgentChatPanel from '@/components/AgentChatPanel';
import { getClients, ClientTenant } from '@/lib/api';
import { Plus } from 'lucide-react';

export default function ClientsPage() {
  const [clients, setClients] = useState<ClientTenant[]>([]);
  const [isChatOpen, setIsChatOpen] = useState(false);

  useEffect(() => {
    getClients().then(setClients);
  }, []);

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-gray-100 flex">
      <Sidebar />
      <div className="flex-1 ml-64 flex flex-col min-w-0">
        <Header
          title="Client Tenants"
          subtitle="Multi-tenant SOC management – isolated telemetry, rules, and agents per client"
          onOpenChat={() => setIsChatOpen(true)}
        />
        <main className="flex-1 p-8 space-y-6 overflow-y-auto">
          <div className="flex justify-between items-center">
            <span className="text-xs text-purple-300 font-semibold">{clients.length} Active Client SOCs</span>
            <button
              onClick={() => alert('Onboard new client tenant modal triggered')}
              className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold flex items-center space-x-2 shadow-lg shadow-purple-500/30"
            >
              <Plus className="w-4 h-4" />
              <span>Onboard New Client</span>
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {clients.map((cli) => (
              <div key={cli.id} className="glass-card rounded-2xl p-6 border border-purple-500/25 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="w-10 h-10 rounded-xl bg-purple-600/20 border border-purple-500/30 flex items-center justify-center font-bold text-purple-300 text-sm">
                    {cli.name.substring(0, 2).toUpperCase()}
                  </div>
                  <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full ${
                    cli.riskScore === 'Critical' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' : 'bg-orange-500/20 text-orange-400 border border-orange-500/30'
                  }`}>
                    {cli.riskScore} Risk
                  </span>
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">{cli.name}</h3>
                  <p className="text-xs text-gray-400">{cli.industry} • MCP Engine: <span className="text-purple-300 font-semibold">{cli.mcpProvider}</span></p>
                </div>
                <div className="grid grid-cols-2 gap-3 pt-2">
                  <div className="p-3 rounded-xl bg-[#141420] border border-purple-500/10">
                    <span className="text-[10px] text-gray-400 uppercase">Active Alerts</span>
                    <div className="text-lg font-black text-rose-400 mt-0.5">{cli.activeAlerts}</div>
                  </div>
                  <div className="p-3 rounded-xl bg-[#141420] border border-purple-500/10">
                    <span className="text-[10px] text-gray-400 uppercase">Open Tickets</span>
                    <div className="text-lg font-black text-purple-300 mt-0.5">{cli.openTickets}</div>
                  </div>
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
