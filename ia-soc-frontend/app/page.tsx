'use client';

import React, { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';
import AgentChatPanel from '@/components/AgentChatPanel';
import { getAlerts, getTickets, getReviewQueue, getClients, Alert, Ticket, ReviewItem, ClientTenant } from '@/lib/api';
import {
  AlertOctagon,
  AlertTriangle,
  Info,
  CheckCircle2,
  Clock,
  Zap,
  ShieldAlert,
  ArrowRight,
  ExternalLink,
  Check,
  X,
  Building2,
  TrendingUp,
  Activity,
  Loader2
} from 'lucide-react';
import Link from 'next/link';

export default function OverviewPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [reviewQueue, setReviewQueue] = useState<ReviewItem[]>([]);
  const [clients, setClients] = useState<ClientTenant[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);

  const loadData = async () => {
    setIsRefreshing(true);
    try {
      const [a, t, r, c] = await Promise.all([getAlerts(), getTickets(), getReviewQueue(), getClients()]);
      setAlerts(a);
      setTickets(t);
      setReviewQueue(r);
      setClients(c);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
      setTimeout(() => setIsRefreshing(false), 500);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const criticalCount = alerts.filter(a => a.severity === 'Critical').length + tickets.filter(t => t.severity === 'Critical').length;
  const highCount = alerts.filter(a => a.severity === 'High').length + tickets.filter(t => t.severity === 'High').length;
  const mediumCount = alerts.filter(a => a.severity === 'Medium').length + tickets.filter(t => t.severity === 'Medium').length;
  const lowCount = alerts.filter(a => a.severity === 'Low').length + tickets.filter(t => t.severity === 'Low').length;

  const slaBreachesCount = tickets.filter(t => t.slaBreach).length;
  const alertVolume24h = 1247;

  const attackCategories = [
    { name: 'Malware / Ransomware', count: 412, percentage: 33, color: 'bg-rose-500' },
    { name: 'Phishing & Credential Harvest', count: 320, percentage: 26, color: 'bg-orange-500' },
    { name: 'Unauthorized Access', count: 215, percentage: 17, color: 'bg-amber-500' },
    { name: 'Suspicious Network Activity', count: 180, percentage: 14, color: 'bg-blue-500' },
    { name: 'Policy Violation', count: 75, percentage: 6, color: 'bg-indigo-500' },
    { name: 'Data Breach / Exfiltration', count: 45, percentage: 4, color: 'bg-purple-500' },
  ];

  const ticketStatusCounts = {
    new: tickets.filter(t => t.status === 'New').length + 12,
    assigned: tickets.filter(t => t.status === 'Assigned').length + 8,
    inProgress: tickets.filter(t => t.status === 'In Progress').length + 15,
    pending: 6,
    escalated: 4,
    resolved: 142
  };
  const totalActiveTickets = Object.values(ticketStatusCounts).reduce((a, b) => a + b, 0);

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-gray-100 flex">
      <Sidebar
        unprocessedAlertsCount={alerts.filter(a => a.status === 'New').length}
        openTicketsCount={tickets.length}
        reviewQueueCount={reviewQueue.length}
        notificationsCount={2}
      />

      <div className="flex-1 ml-64 flex flex-col min-w-0">
        <Header
          title="Overview"
          subtitle="Security operations at a glance – Codex Agent & MCP Orchestrator"
          onRefresh={loadData}
          isRefreshing={isRefreshing}
          onOpenChat={() => setIsChatOpen(true)}
        />

        <main className="flex-1 p-8 space-y-8 overflow-y-auto">
          {isLoading ? (
            <div className="h-96 flex flex-col items-center justify-center space-y-3 text-purple-400">
              <Loader2 className="w-8 h-8 animate-spin" />
              <span className="text-xs font-semibold">Loading telemetry from backend agents...</span>
            </div>
          ) : (
            <>
              {/* Severity Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
                <div className="glass-card rounded-2xl p-5 border-l-4 border-l-rose-500 relative overflow-hidden group hover:border-rose-500/50 transition-all">
                  <div className="absolute top-0 right-0 p-4 text-rose-500/10 group-hover:text-rose-500/20 transition-colors">
                    <AlertOctagon className="w-16 h-16" />
                  </div>
                  <span className="text-[11px] font-bold tracking-wider text-gray-400 uppercase">Critical Severity</span>
                  <div className="text-3xl font-black text-rose-400 mt-2">{criticalCount}</div>
                  <div className="flex items-center space-x-1.5 text-xs text-rose-400/90 mt-2">
                    <span className="font-semibold">+2</span>
                    <span className="text-gray-400">requiring immediate action</span>
                  </div>
                </div>

                <div className="glass-card rounded-2xl p-5 border-l-4 border-l-orange-500 relative overflow-hidden group hover:border-orange-500/50 transition-all">
                  <div className="absolute top-0 right-0 p-4 text-orange-500/10 group-hover:text-orange-500/20 transition-colors">
                    <AlertTriangle className="w-16 h-16" />
                  </div>
                  <span className="text-[11px] font-bold tracking-wider text-gray-400 uppercase">High Severity</span>
                  <div className="text-3xl font-black text-orange-400 mt-2">{highCount}</div>
                  <div className="flex items-center space-x-1.5 text-xs text-orange-400/90 mt-2">
                    <span className="font-semibold">+5</span>
                    <span className="text-gray-400">active triage cases</span>
                  </div>
                </div>

                <div className="glass-card rounded-2xl p-5 border-l-4 border-l-amber-400 relative overflow-hidden group hover:border-amber-400/50 transition-all">
                  <div className="absolute top-0 right-0 p-4 text-amber-400/10 group-hover:text-amber-400/20 transition-colors">
                    <Info className="w-16 h-16" />
                  </div>
                  <span className="text-[11px] font-bold tracking-wider text-gray-400 uppercase">Medium Severity</span>
                  <div className="text-3xl font-black text-amber-300 mt-2">{mediumCount}</div>
                  <div className="flex items-center space-x-1.5 text-xs text-amber-300/90 mt-2">
                    <span className="font-semibold">+12</span>
                    <span className="text-gray-400">processed by RAG skills</span>
                  </div>
                </div>

                <div className="glass-card rounded-2xl p-5 border-l-4 border-l-emerald-500 relative overflow-hidden group hover:border-emerald-500/50 transition-all">
                  <div className="absolute top-0 right-0 p-4 text-emerald-500/10 group-hover:text-emerald-500/20 transition-colors">
                    <CheckCircle2 className="w-16 h-16" />
                  </div>
                  <span className="text-[11px] font-bold tracking-wider text-gray-400 uppercase">Low Severity</span>
                  <div className="text-3xl font-black text-emerald-400 mt-2">{lowCount}</div>
                  <div className="flex items-center space-x-1.5 text-xs text-emerald-400/90 mt-2">
                    <span className="font-semibold">Auto-closed</span>
                    <span className="text-gray-400">by Codex Agent rules</span>
                  </div>
                </div>
              </div>

              {/* Secondary Stats & Ticket Status */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="glass-card rounded-2xl p-6 flex flex-col justify-between border border-purple-500/20">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold uppercase tracking-wider text-gray-400">SLA Breaches</span>
                    <span className="p-2 rounded-xl bg-rose-500/10 text-rose-400">
                      <Clock className="w-5 h-5" />
                    </span>
                  </div>
                  <div className="my-4">
                    <div className="text-4xl font-black text-white">{slaBreachesCount}</div>
                    <p className="text-xs text-rose-400 mt-1 font-medium">⚠️ Requires immediate escalation</p>
                  </div>
                  <Link href="/tickets" className="inline-flex items-center text-xs font-semibold text-purple-400 hover:text-purple-300">
                    <span>View delayed tickets</span>
                    <ArrowRight className="w-4 h-4 ml-1.5" />
                  </Link>
                </div>

                <div className="glass-card rounded-2xl p-6 flex flex-col justify-between border border-purple-500/20">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold uppercase tracking-wider text-gray-400">Alert Volume (24h)</span>
                    <span className="p-2 rounded-xl bg-purple-500/10 text-purple-400">
                      <Zap className="w-5 h-5" />
                    </span>
                  </div>
                  <div className="my-4">
                    <div className="text-4xl font-black text-white">{alertVolume24h.toLocaleString()}</div>
                    <p className="text-xs text-emerald-400 mt-1 font-medium">⚡ 98.2% filtered & triaged by agent</p>
                  </div>
                  <Link href="/alerts" className="inline-flex items-center text-xs font-semibold text-purple-400 hover:text-purple-300">
                    <span>Browse ingested alerts</span>
                    <ArrowRight className="w-4 h-4 ml-1.5" />
                  </Link>
                </div>

                <div className="glass-card rounded-2xl p-6 flex flex-col justify-between border border-purple-500/20">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold uppercase tracking-wider text-gray-400">Ticket Status Distribution</span>
                    <span className="text-xs font-bold text-purple-300">{totalActiveTickets} Total</span>
                  </div>
                  <div className="my-3 space-y-2">
                    <div className="h-3 w-full bg-gray-800 rounded-full overflow-hidden flex">
                      <div style={{ width: `${(ticketStatusCounts.new / totalActiveTickets) * 100}%` }} className="bg-rose-500" />
                      <div style={{ width: `${(ticketStatusCounts.assigned / totalActiveTickets) * 100}%` }} className="bg-amber-500" />
                      <div style={{ width: `${(ticketStatusCounts.inProgress / totalActiveTickets) * 100}%` }} className="bg-purple-500" />
                      <div style={{ width: `${(ticketStatusCounts.pending / totalActiveTickets) * 100}%` }} className="bg-blue-500" />
                      <div style={{ width: `${(ticketStatusCounts.escalated / totalActiveTickets) * 100}%` }} className="bg-indigo-500" />
                      <div style={{ width: `${(ticketStatusCounts.resolved / totalActiveTickets) * 100}%` }} className="bg-emerald-500" />
                    </div>
                  </div>
                  <Link href="/tickets" className="inline-flex items-center text-xs font-semibold text-purple-400 hover:text-purple-300">
                    <span>Open ticket management</span>
                    <ArrowRight className="w-4 h-4 ml-1.5" />
                  </Link>
                </div>
              </div>

              {/* My Open Tickets & Review Queue */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="glass-card rounded-2xl p-6 border border-purple-500/20 space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-base font-bold text-white flex items-center space-x-2">
                      <Activity className="w-5 h-5 text-purple-400" />
                      <span>My Assigned Tickets</span>
                    </h3>
                    <span className="text-xs bg-purple-500/20 text-purple-300 px-2.5 py-0.5 rounded-full font-semibold">
                      {tickets.length} Assigned
                    </span>
                  </div>
                  {tickets.length === 0 ? (
                    <p className="text-xs text-gray-400 py-6 text-center">No assigned tickets found.</p>
                  ) : (
                    <div className="space-y-3">
                      {tickets.map((ticket) => (
                        <div key={ticket.id} className="p-4 rounded-xl bg-[#141420] border border-purple-500/10 flex items-center justify-between">
                          <div className="space-y-1 pr-4">
                            <div className="flex items-center space-x-2">
                              <span className="text-xs font-bold text-purple-400">{ticket.id}</span>
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30">
                                {ticket.severity}
                              </span>
                              <span className="text-[10px] bg-gray-800 text-gray-300 px-2 py-0.5 rounded-full">{ticket.client}</span>
                            </div>
                            <h4 className="text-sm font-semibold text-gray-200">{ticket.title}</h4>
                            <p className="text-[11px] text-gray-400">Opened {ticket.openedDaysAgo}d ago • Status: <span className="text-purple-300">{ticket.status}</span></p>
                          </div>
                          <Link href="/tickets" className="p-2 rounded-lg bg-purple-600/20 text-purple-300 hover:bg-purple-600/30 transition-colors">
                            <ExternalLink className="w-4 h-4" />
                          </Link>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="glass-card rounded-2xl p-6 border border-purple-500/20 space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-base font-bold text-white flex items-center space-x-2">
                      <ShieldAlert className="w-5 h-5 text-amber-400" />
                      <span>Awaiting Review (Evidence Validation)</span>
                    </h3>
                    <Link href="/review-queue" className="text-xs text-purple-400 hover:underline font-semibold">
                      View All ({reviewQueue.length})
                    </Link>
                  </div>
                  {reviewQueue.length === 0 ? (
                    <p className="text-xs text-gray-400 py-6 text-center">No review items pending.</p>
                  ) : (
                    <div className="space-y-3">
                      {reviewQueue.map((item) => (
                        <div key={item.id} className="p-4 rounded-xl bg-[#141420] border border-amber-500/20 space-y-3">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-bold text-amber-400">{item.id}</span>
                            <span className="text-[10px] text-gray-400">{item.timestamp}</span>
                          </div>
                          <p className="text-xs font-medium text-gray-200">{item.title}</p>
                          <p className="text-[11px] text-gray-400 bg-[#0e0e16] p-2 rounded-lg border border-gray-800">
                            <strong className="text-purple-300">Agent Decision:</strong> {item.agentDecision}
                          </p>
                          <div className="flex justify-end space-x-2">
                            <Link href="/review-queue" className="px-3 py-1 rounded-lg bg-emerald-500/20 text-emerald-400 text-xs font-semibold">
                              Review in Queue
                            </Link>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Attack Categories & Clients */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="glass-card rounded-2xl p-6 border border-purple-500/20 space-y-4">
                  <h3 className="text-base font-bold text-white flex items-center space-x-2">
                    <TrendingUp className="w-5 h-5 text-purple-400" />
                    <span>Top Attack Categories</span>
                  </h3>
                  <div className="space-y-3.5 pt-2">
                    {attackCategories.map((cat) => (
                      <div key={cat.name} className="space-y-1.5">
                        <div className="flex justify-between text-xs">
                          <span className="font-semibold text-gray-300">{cat.name}</span>
                          <span className="font-bold text-purple-300">{cat.count} alerts ({cat.percentage}%)</span>
                        </div>
                        <div className="h-2 w-full bg-gray-800 rounded-full overflow-hidden">
                          <div style={{ width: `${cat.percentage}%` }} className={`h-full ${cat.color} rounded-full`} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="glass-card rounded-2xl p-6 border border-purple-500/20 space-y-4">
                  <h3 className="text-base font-bold text-white flex items-center space-x-2">
                    <Building2 className="w-5 h-5 text-purple-400" />
                    <span>Top Affected Clients</span>
                  </h3>
                  <div className="space-y-3">
                    {clients.map((client) => (
                      <div key={client.id} className="p-3.5 rounded-xl bg-[#141420] border border-purple-500/10 flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <div className="w-9 h-9 rounded-xl bg-purple-600/20 border border-purple-500/30 flex items-center justify-center font-bold text-purple-300 text-xs">
                            {client.name.substring(0, 2).toUpperCase()}
                          </div>
                          <div>
                            <h4 className="text-xs font-bold text-white">{client.name}</h4>
                            <p className="text-[10px] text-gray-400">{client.industry}</p>
                          </div>
                        </div>
                        <span className="text-xs font-black text-rose-400">{client.activeAlerts} Alerts</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </>
          )}
        </main>
      </div>

      {/* Global Floating Agent Chat */}
      <AgentChatPanel isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />
    </div>
  );
}
