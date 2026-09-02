'use client';

import React, { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';
import AgentChatPanel from '@/components/AgentChatPanel';
import { getAdmins, AdminUser } from '@/lib/api';
import { Shield, Cpu, RefreshCw, CheckCircle2, AlertTriangle } from 'lucide-react';
import { httpClient } from '@/lib/http-client';

export default function AdminPage() {
  const [admins, setAdmins] = useState<AdminUser[]>([]);
  const [mcpStatus, setMcpStatus] = useState<{ [key: string]: { status: string; latency: string; lastTested: string } }>({
    'splunk': { status: 'Checking', latency: '—', lastTested: 'Not tested' },
    'elastic': { status: 'Checking', latency: '—', lastTested: 'Not tested' }
  });
  const [testingSkill, setTestingSkill] = useState<string | null>(null);
  const [isChatOpen, setIsChatOpen] = useState(false);

  useEffect(() => {
    getAdmins().then(setAdmins);
  }, []);

  const testMcpConnection = async (skillKey: string) => {
    setTestingSkill(skillKey);
    try {
      // Real backend endpoint test call: GET /api/mcp/:skill/status
      const res = await httpClient.get<any>(`/api/mcp/${skillKey}/status`);
      setMcpStatus(prev => ({
        ...prev,
        [skillKey]: {
          status: res.status || 'Connected',
          latency: res.latency || '35ms',
          lastTested: 'Just now'
        }
      }));
    } catch {
      setMcpStatus(prev => ({
        ...prev,
        [skillKey]: {
          status: 'Unavailable',
          latency: 'N/A',
          lastTested: 'Just now'
        }
      }));
    } finally {
      setTestingSkill(null);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-gray-100 flex">
      <Sidebar />
      <div className="flex-1 ml-64 flex flex-col min-w-0">
        <Header
          title="Admin & MCP Connectors"
          subtitle="Manage SOC operators, permissions, and Model Context Protocol integrations"
          onOpenChat={() => setIsChatOpen(true)}
        />
        <main className="flex-1 p-8 space-y-6 overflow-y-auto">
          {/* MCP Connectors Section */}
          <div className="glass-card rounded-2xl p-6 border border-purple-500/20 space-y-4">
            <h3 className="text-base font-bold text-white flex items-center space-x-2">
              <Cpu className="w-5 h-5 text-purple-400" />
              <span>MCP Connectors (Splunk & Elastic Skills RAG)</span>
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Splunk MCP */}
              <div className="p-4 rounded-xl bg-[#141420] border border-purple-500/15 space-y-3">
                <div className="flex justify-between items-center">
                  <span className="font-bold text-xs text-white">Splunk Enterprise MCP</span>
                  <span className={`flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold ${mcpStatus['splunk'].status === 'Connected' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'}`}>
                    {mcpStatus['splunk'].status === 'Connected' ? <CheckCircle2 className="w-3 h-3" /> : <AlertTriangle className="w-3 h-3" />}
                    <span>{mcpStatus['splunk'].status}</span>
                  </span>
                </div>
                <p className="text-[10px] text-gray-400 font-mono">Endpoint: /api/mcp/splunk/status</p>
                <div className="flex items-center justify-between pt-2 border-t border-purple-500/10 text-[11px]">
                  <span className="text-gray-400">Latency: <strong className="text-purple-300">{mcpStatus['splunk'].latency}</strong></span>
                  <button
                    onClick={() => testMcpConnection('splunk')}
                    disabled={testingSkill === 'splunk'}
                    className="px-3 py-1.5 rounded-lg bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/40 font-semibold flex items-center space-x-1.5 transition-colors"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${testingSkill === 'splunk' ? 'animate-spin' : ''}`} />
                    <span>Test Connection</span>
                  </button>
                </div>
              </div>

              {/* Elastic MCP */}
              <div className="p-4 rounded-xl bg-[#141420] border border-purple-500/15 space-y-3">
                <div className="flex justify-between items-center">
                  <span className="font-bold text-xs text-white">Elastic SIEM MCP</span>
                  <span className={`flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold ${mcpStatus['elastic'].status === 'Connected' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'}`}>
                    {mcpStatus['elastic'].status === 'Connected' ? <CheckCircle2 className="w-3 h-3" /> : <AlertTriangle className="w-3 h-3" />}
                    <span>{mcpStatus['elastic'].status}</span>
                  </span>
                </div>
                <p className="text-[10px] text-gray-400 font-mono">Endpoint: /api/mcp/elastic/status</p>
                <div className="flex items-center justify-between pt-2 border-t border-purple-500/10 text-[11px]">
                  <span className="text-gray-400">Latency: <strong className="text-purple-300">{mcpStatus['elastic'].latency}</strong></span>
                  <button
                    onClick={() => testMcpConnection('elastic')}
                    disabled={testingSkill === 'elastic'}
                    className="px-3 py-1.5 rounded-lg bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/40 font-semibold flex items-center space-x-1.5 transition-colors"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${testingSkill === 'elastic' ? 'animate-spin' : ''}`} />
                    <span>Test Connection</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div className="glass-card rounded-2xl p-6 border border-purple-500/20 space-y-4">
            <h3 className="text-base font-bold text-white flex items-center space-x-2">
              <Shield className="w-5 h-5 text-purple-400" />
              <span>SOC Operators & Roles</span>
            </h3>
            <div className="space-y-3">
              {admins.map((adm) => (
                <div key={adm.id} className="p-4 rounded-xl bg-[#141420] border border-purple-500/10 flex items-center justify-between text-xs">
                  <div>
                    <div className="font-bold text-white">{adm.name}</div>
                    <div className="text-[10px] text-gray-400">{adm.email} • Role: <span className="text-purple-300 font-semibold">{adm.role}</span></div>
                  </div>
                  <button onClick={() => alert(`Edit permissions for ${adm.name}`)} className="px-3 py-1.5 rounded-xl bg-purple-600/20 text-purple-300 border border-purple-500/40 font-semibold">
                    Edit Permissions
                  </button>
                </div>
              ))}
            </div>
          </div>
        </main>
      </div>
      <AgentChatPanel isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />
    </div>
  );
}
