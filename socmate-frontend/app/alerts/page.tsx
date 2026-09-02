'use client';

import React, { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';
import AgentChatPanel from '@/components/AgentChatPanel';
import { getAlerts, Alert } from '@/lib/api';
import { Search, Filter, FileCode, Loader2 } from 'lucide-react';

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [severityFilter, setSeverityFilter] = useState<string>('All');
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isChatOpen, setIsChatOpen] = useState(false);

  useEffect(() => {
    getAlerts().then(data => {
      setAlerts(data);
      setIsLoading(false);
    });
  }, []);

  const filteredAlerts = alerts.filter(a => {
    const matchesSearch = a.title.toLowerCase().includes(searchQuery.toLowerCase()) || a.client.toLowerCase().includes(searchQuery.toLowerCase()) || a.source.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesSeverity = severityFilter === 'All' || a.severity === severityFilter;
    return matchesSearch && matchesSeverity;
  });

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-gray-100 flex">
      <Sidebar />
      <div className="flex-1 ml-64 flex flex-col min-w-0">
        <Header
          title="Alerts"
          subtitle="Ingested security telemetry and agent triage status"
          onOpenChat={() => setIsChatOpen(true)}
        />
        <main className="flex-1 p-8 space-y-6 overflow-y-auto">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 glass-card p-4 rounded-2xl">
            <div className="relative w-full sm:w-96">
              <Search className="absolute left-3.5 top-3 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search alerts by title, client, or source..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-[#141420] border border-purple-500/25 rounded-xl pl-10 pr-4 py-2 text-xs text-white focus:outline-none focus:border-purple-500"
              />
            </div>
            <div className="flex items-center space-x-3 w-full sm:w-auto">
              <Filter className="w-4 h-4 text-purple-400" />
              <select
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
                className="bg-[#141420] border border-purple-500/25 rounded-xl px-4 py-2 text-xs text-white focus:outline-none focus:border-purple-500"
              >
                <option value="All">All Severities</option>
                <option value="Critical">Critical</option>
                <option value="High">High</option>
                <option value="Medium">Medium</option>
                <option value="Low">Low</option>
              </select>
            </div>
          </div>

          {isLoading ? (
            <div className="h-64 flex items-center justify-center text-purple-400">
              <Loader2 className="w-6 h-6 animate-spin mr-2" />
              <span>Loading telemetry alerts...</span>
            </div>
          ) : (
            <div className="glass-card rounded-2xl overflow-hidden border border-purple-500/20">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-purple-500/20 bg-[#12121d] text-[11px] font-bold text-gray-400 uppercase tracking-wider">
                      <th className="py-3.5 px-6">Alert ID</th>
                      <th className="py-3.5 px-6">Title & Source</th>
                      <th className="py-3.5 px-6">Client</th>
                      <th className="py-3.5 px-6">Severity</th>
                      <th className="py-3.5 px-6">Agent Status</th>
                      <th className="py-3.5 px-6">Timestamp</th>
                      <th className="py-3.5 px-6 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-purple-500/10 text-xs">
                    {filteredAlerts.map((alert) => (
                      <tr key={alert.id} className="hover:bg-purple-500/[0.03] transition-colors">
                        <td className="py-4 px-6 font-bold text-purple-400">{alert.id}</td>
                        <td className="py-4 px-6">
                          <div className="font-semibold text-white">{alert.title}</div>
                          <div className="text-[10px] text-gray-400">{alert.source}</div>
                        </td>
                        <td className="py-4 px-6 text-gray-300 font-medium">{alert.client}</td>
                        <td className="py-4 px-6">
                          <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${
                            alert.severity === 'Critical' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' : 'bg-orange-500/20 text-orange-400 border border-orange-500/30'
                          }`}>
                            {alert.severity}
                          </span>
                        </td>
                        <td className="py-4 px-6">
                          <span className="px-2.5 py-1 rounded-full text-[10px] font-semibold bg-purple-500/20 text-purple-300 border border-purple-500/30">
                            {alert.status}
                          </span>
                        </td>
                        <td className="py-4 px-6 text-gray-400">{alert.timestamp}</td>
                        <td className="py-4 px-6 text-right">
                          <button
                            onClick={() => setSelectedAlert(alert)}
                            className="px-3 py-1 rounded-lg bg-purple-600/25 hover:bg-purple-600/40 text-purple-300 border border-purple-500/40 text-xs font-semibold transition-colors"
                          >
                            Inspect Raw
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {selectedAlert && (
            <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
              <div className="glass-card w-full max-w-2xl rounded-2xl p-6 border border-purple-500/30 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-bold text-white flex items-center space-x-2">
                    <FileCode className="w-5 h-5 text-purple-400" />
                    <span>Raw Payload for {selectedAlert.id}</span>
                  </h3>
                  <button onClick={() => setSelectedAlert(null)} className="text-gray-400 hover:text-white font-bold">✕</button>
                </div>
                <p className="text-xs text-gray-300 font-medium">{selectedAlert.title}</p>
                <pre className="p-4 rounded-xl bg-[#0a0a0f] border border-purple-500/20 text-emerald-400 font-mono text-xs overflow-x-auto">
                  {selectedAlert.rawPayload}
                </pre>
                <div className="flex justify-end pt-2">
                  <button onClick={() => setSelectedAlert(null)} className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold">
                    Close
                  </button>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
      <AgentChatPanel isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />
    </div>
  );
}
