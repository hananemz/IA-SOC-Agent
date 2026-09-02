'use client';

import React, { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';
import AgentChatPanel from '@/components/AgentChatPanel';
import { getTickets, submitAgentFeedback, Ticket } from '@/lib/api';
import { Ticket as TicketIcon, Clock, CheckCircle2, ShieldAlert, Cpu, MessageSquare, ThumbsUp, ThumbsDown, Send, FileText, Check, AlertTriangle } from 'lucide-react';

export default function TicketsPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [feedbackInput, setFeedbackInput] = useState<{ [key: string]: string }>({});
  const [newNote, setNewNote] = useState('');

  const loadTickets = async () => {
    setIsLoading(true);
    try {
      const data = await getTickets();
      setTickets(data);
      if (data.length > 0) setSelectedTicket(data[0]);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadTickets();
  }, []);

  const handleFeedback = async (itemId: string, verdict: 'correct' | 'incorrect') => {
    const comment = feedbackInput[itemId] || '';
    await submitAgentFeedback(itemId, verdict, comment);
    // Update local state feedback
    if (selectedTicket) {
      const updatedTimeline = selectedTicket.timeline.map(t => t.id === itemId ? { ...t, feedback: { verdict, comment } } : t);
      const updated = { ...selectedTicket, timeline: updatedTimeline };
      setSelectedTicket(updated);
      setTickets(tickets.map(t => t.id === updated.id ? updated : t));
    }
    alert(`Feedback (${verdict}) recorded successfully for item ${itemId}!`);
  };

  const handleAddNote = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNote.trim() || !selectedTicket) return;

    const noteItem = {
      id: 'N-' + Date.now(),
      author: 'Alex Mercer',
      role: 'Lead SOC Operator',
      type: 'human' as const,
      content: newNote,
      timestamp: 'Just now'
    };

    const updatedInvestigation = {
      ...selectedTicket.investigation,
      notes: [...selectedTicket.investigation.notes, noteItem]
    };
    const updated = { ...selectedTicket, investigation: updatedInvestigation };
    setSelectedTicket(updated);
    setTickets(tickets.map(t => t.id === updated.id ? updated : t));
    setNewNote('');
  };

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-gray-100 flex">
      <Sidebar />
      <div className="flex-1 ml-64 flex flex-col min-w-0">
        <Header
          title="Tickets & Investigation"
          subtitle="Incident management, investigation workspace, and agent feedback loop"
          onOpenChat={() => setIsChatOpen(true)}
        />
        <main className="flex-1 p-8 grid grid-cols-1 lg:grid-cols-3 gap-6 overflow-y-auto">
          {isLoading ? (
            <div className="lg:col-span-3 h-96 flex items-center justify-center text-purple-400">
              Loading tickets and investigation telemetry...
            </div>
          ) : tickets.length === 0 ? (
            <div className="lg:col-span-3 glass-card rounded-2xl p-12 text-center text-gray-400">
              No tickets found in queue.
            </div>
          ) : (
            <>
              {/* Tickets List */}
              <div className="lg:col-span-1 space-y-3">
                <h3 className="text-sm font-bold uppercase tracking-wider text-gray-400 mb-2">Open Incidents ({tickets.length})</h3>
                {tickets.map((t) => (
                  <div
                    key={t.id}
                    onClick={() => setSelectedTicket(t)}
                    className={`p-4 rounded-2xl cursor-pointer transition-all glass-card border ${
                      selectedTicket?.id === t.id ? 'border-purple-500 bg-purple-500/10 shadow-lg shadow-purple-500/10' : 'border-purple-500/15 hover:border-purple-500/30'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold text-purple-400">{t.id}</span>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        t.severity === 'Critical' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' : 'bg-orange-500/20 text-orange-400 border border-orange-500/30'
                      }`}>
                        {t.severity}
                      </span>
                    </div>
                    <h4 className="text-xs font-semibold text-white mb-2">{t.title}</h4>
                    <div className="flex items-center justify-between text-[10px] text-gray-400">
                      <span>{t.client}</span>
                      <span className="text-purple-300 font-semibold">{t.status}</span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Ticket Detail & Investigation Workspace */}
              {selectedTicket ? (
                <div className="lg:col-span-2 glass-card rounded-2xl p-6 border border-purple-500/25 space-y-6">
                  <div className="flex items-center justify-between border-b border-purple-500/20 pb-4">
                    <div>
                      <div className="flex items-center space-x-3 mb-1">
                        <span className="text-sm font-bold text-purple-400">{selectedTicket.id}</span>
                        <span className="text-xs font-semibold text-gray-300 bg-purple-500/20 px-2.5 py-0.5 rounded-full">{selectedTicket.client}</span>
                        <span className="text-xs font-bold text-amber-300 bg-amber-500/15 px-2.5 py-0.5 rounded-full border border-amber-500/30">
                          Investigation: {selectedTicket.investigation.status}
                        </span>
                      </div>
                      <h2 className="text-lg font-black text-white">{selectedTicket.title}</h2>
                    </div>
                    <button
                      onClick={() => setIsChatOpen(true)}
                      className="px-3.5 py-2 rounded-xl bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/40 text-xs font-semibold flex items-center space-x-1.5 transition-colors"
                    >
                      <MessageSquare className="w-4 h-4 text-purple-400" />
                      <span>Chat with Agent on Ticket</span>
                    </button>
                  </div>

                  {/* Investigation Fields Section */}
                  <div className="space-y-4 p-4 rounded-xl bg-[#141420] border border-purple-500/20">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-purple-300 flex items-center space-x-2">
                      <FileText className="w-4 h-4 text-purple-400" />
                      <span>Investigation Workspace</span>
                    </h3>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                      <div className="space-y-1">
                        <span className="font-semibold text-gray-400">Analyst / Agent Hypothesis:</span>
                        <p className="p-3 rounded-xl bg-[#0a0a0f] border border-purple-500/15 text-gray-200">
                          {selectedTicket.investigation.analystHypothesis || 'No hypothesis formulated yet.'}
                        </p>
                      </div>
                      <div className="space-y-1">
                        <span className="font-semibold text-gray-400">Root Cause Identified:</span>
                        <p className="p-3 rounded-xl bg-[#0a0a0f] border border-purple-500/15 text-gray-200">
                          {selectedTicket.investigation.rootCause || 'Root cause under investigation.'}
                        </p>
                      </div>
                    </div>

                    <div className="space-y-2 pt-2">
                      <span className="text-[11px] font-bold text-gray-400 uppercase">Recommended Remediation Actions:</span>
                      <ul className="list-disc list-inside text-xs text-gray-300 space-y-1">
                        {selectedTicket.investigation.recommendedRemediations.map((rec, i) => (
                          <li key={i}>{rec}</li>
                        ))}
                      </ul>
                    </div>

                    <div className="space-y-2 pt-2">
                      <span className="text-[11px] font-bold text-gray-400 uppercase">Executed Remediation Actions:</span>
                      <div className="space-y-1.5">
                        {selectedTicket.investigation.executedRemediations.map((exec, i) => (
                          <div key={i} className="flex items-center justify-between text-xs p-2.5 rounded-lg bg-[#0a0a0f] border border-purple-500/10">
                            <span className="text-gray-200">{exec.action}</span>
                            <div className="flex items-center space-x-2">
                              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                                exec.executedBy === 'Agent' ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30' : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                              }`}>
                                {exec.executedBy}: {exec.authorName}
                              </span>
                              <span className="text-[10px] text-gray-500">{exec.timestamp}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Investigation Notes / Timeline */}
                    <div className="space-y-3 pt-3 border-t border-purple-500/15">
                      <span className="text-[11px] font-bold text-gray-400 uppercase">Investigation Notes & Comments (Historized)</span>
                      <div className="space-y-2 max-h-48 overflow-y-auto">
                        {selectedTicket.investigation.notes.map((note) => (
                          <div key={note.id} className={`p-3 rounded-xl text-xs space-y-1 ${
                            note.type === 'agent' ? 'bg-purple-600/10 border border-purple-500/20' : 'bg-[#0a0a0f] border border-gray-800'
                          }`}>
                            <div className="flex items-center justify-between">
                              <span className="font-bold text-purple-300">{note.author} ({note.role})</span>
                              <span className="text-[10px] text-gray-500">{note.timestamp}</span>
                            </div>
                            <p className="text-gray-200">{note.content}</p>
                          </div>
                        ))}
                      </div>

                      {/* Add Note Form */}
                      <form onSubmit={handleAddNote} className="flex gap-2 pt-2">
                        <input
                          type="text"
                          placeholder="Add investigation note or comment..."
                          value={newNote}
                          onChange={(e) => setNewNote(e.target.value)}
                          className="flex-1 bg-[#0a0a0f] border border-purple-500/25 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none focus:border-purple-500"
                        />
                        <button type="submit" className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold flex items-center space-x-1">
                          <Send className="w-3.5 h-3.5" />
                          <span>Add Note</span>
                        </button>
                      </form>
                    </div>
                  </div>

                  {/* Evidence & Validation Pipeline */}
                  <div className="space-y-3">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400 flex items-center space-x-2">
                      <ShieldAlert className="w-4 h-4 text-purple-400" />
                      <span>Evidence & Validation Pipeline</span>
                    </h3>
                    <div className="space-y-2">
                      {selectedTicket.evidence.map((ev) => (
                        <div key={ev.id} className="p-3 rounded-xl bg-[#141420] border border-purple-500/10 flex items-center justify-between text-xs">
                          <div>
                            <div className="font-semibold text-gray-200">{ev.description}</div>
                            <div className="text-[10px] text-gray-400">Validated by: <span className="text-purple-300">{ev.validatedBy}</span> • {ev.timestamp}</div>
                          </div>
                          <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${
                            ev.validationStatus === 'validated' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                          }`}>
                            {ev.validationStatus.toUpperCase()}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Codex Agent & MCP Skills Timeline + Feedback Loop */}
                  <div className="space-y-3">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400 flex items-center space-x-2">
                      <Cpu className="w-4 h-4 text-purple-400" />
                      <span>Codex Agent & MCP Skills Timeline (Feedback Loop Enabled)</span>
                    </h3>
                    <div className="space-y-4 border-l-2 border-purple-500/30 ml-2 pl-4">
                      {selectedTicket.timeline.map((step) => (
                        <div key={step.id} className="space-y-2 relative p-4 rounded-xl bg-[#141420] border border-purple-500/15">
                          <div className="absolute -left-[25px] top-4 w-3.5 h-3.5 rounded-full bg-purple-500 border-2 border-[#0a0a0f]" />
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-bold text-white">{step.step}</span>
                            <span className="text-[10px] text-gray-400">{step.timestamp}</span>
                          </div>
                          <p className="text-xs text-purple-300 font-semibold">Skill called: {step.skillCalled}</p>
                          <p className="text-[11px] text-gray-300">{step.details}</p>

                          {/* Feedback Loop Action Bar (Point 5) */}
                          <div className="pt-3 border-t border-purple-500/10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
                            <div className="flex items-center space-x-2">
                              <span className="text-[10px] text-gray-400 font-bold uppercase">Human Feedback:</span>
                              {step.feedback ? (
                                <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full ${
                                  step.feedback.verdict === 'correct' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                                }`}>
                                  {step.feedback.verdict === 'correct' ? '👍 Correct' : '👎 Incorrect'} {step.feedback.comment ? `(${step.feedback.comment})` : ''}
                                </span>
                              ) : (
                                <div className="flex items-center space-x-2">
                                  <button
                                    onClick={() => handleFeedback(step.id, 'correct')}
                                    className="p-1.5 rounded-lg bg-emerald-500/15 hover:bg-emerald-500/30 text-emerald-400 text-xs flex items-center space-x-1 transition-colors"
                                    title="Mark Correct"
                                  >
                                    <ThumbsUp className="w-3.5 h-3.5" />
                                    <span className="text-[10px]">Correct</span>
                                  </button>
                                  <button
                                    onClick={() => handleFeedback(step.id, 'incorrect')}
                                    className="p-1.5 rounded-lg bg-rose-500/15 hover:bg-rose-500/30 text-rose-400 text-xs flex items-center space-x-1 transition-colors"
                                    title="Mark Incorrect"
                                  >
                                    <ThumbsDown className="w-3.5 h-3.5" />
                                    <span className="text-[10px]">Incorrect</span>
                                  </button>
                                </div>
                              )}
                            </div>
                            {!step.feedback && (
                              <input
                                type="text"
                                placeholder="Optional comment for AI training..."
                                value={feedbackInput[step.id] || ''}
                                onChange={(e) => setFeedbackInput({ ...feedbackInput, [step.id]: e.target.value })}
                                className="bg-[#0a0a0f] border border-purple-500/20 rounded-lg px-3 py-1 text-[11px] text-white focus:outline-none focus:border-purple-500 w-full sm:w-64"
                              />
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : null}
            </>
          )}
        </main>
      </div>

      <AgentChatPanel isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} ticketContextId={selectedTicket?.id} />
    </div>
  );
}
