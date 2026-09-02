'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Bot, Send, X, Cpu, CheckCircle2, AlertCircle } from 'lucide-react';
import { sendAgentAssistantMessage } from '@/lib/api';
import type { AgentActivity } from '@/lib/api';

export interface ChatActivity {
  id: string;
  type: string;
  skill?: string;
  text: string;
  status: 'running' | 'success' | 'failed';
}

export interface ChatMessageItem {
  id: string;
  sender: 'user' | 'agent';
  text: string;
  timestamp: string;
  activities: ChatActivity[];
  sources?: string[];
  isError?: boolean;
}

interface AgentChatPanelProps {
  isOpen: boolean;
  onClose: () => void;
  ticketContextId?: string;
  fullPage?: boolean;
}

export default function AgentChatPanel({ isOpen, onClose, ticketContextId, fullPage = false }: AgentChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessageItem[]>([
    {
      id: 'msg-init',
      sender: 'agent',
      text: ticketContextId
        ? `Hello! I am the SOC Analyst Agent overseeing incident ${ticketContextId}. Ask me to query Splunk or Elastic.`
        : `Hello! I am the SOC Analyst Agent connected to the Sekera SOC pipeline. Ask me anything (e.g. 'give me the last critical alert sous elastic').`,
      timestamp: 'Just now',
      activities: []
    }
  ]);
  const [input, setInput] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isThinking]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isThinking) return;

    const userQuery = input;
    const userMsgId = 'user-' + Date.now();
    const agentMsgId = 'agent-' + Date.now();

    const userMsg: ChatMessageItem = {
      id: userMsgId,
      sender: 'user',
      text: userQuery,
      timestamp: 'Just now',
      activities: []
    };

    const initialActivities: ChatActivity[] = [
      { id: 'act-request', type: 'backend_request', text: 'Question envoyée au backend SOC…', status: 'running' }
    ];

    const initialAgentMsg: ChatMessageItem = {
      id: agentMsgId,
      sender: 'agent',
      text: '',
      timestamp: 'Just now',
      activities: initialActivities
    };

    setMessages(prev => [...prev, userMsg, initialAgentMsg]);
    setInput('');
    setIsThinking(true);

    try {
      const result = await sendAgentAssistantMessage(userQuery, { investigationId: ticketContextId });
      const evidenceCount = result.evidence?.length ?? 0;
      const backendActivities: ChatActivity[] = (result.activities || []).map((activity: AgentActivity) => ({
        ...activity,
        skill: result.agentProvider || result.platform || 'SOC backend'
      }));
      if (result.skill || result.mcp) {
        backendActivities.unshift({
          id: 'act-route',
          type: 'routing',
          skill: result.skill,
          text: `Route sélectionnée : ${result.skill || 'analyse générale'}${result.mcp ? ` · MCP cible : ${result.mcp}` : ''}`,
          status: 'success'
        });
      }
      if (backendActivities.length === 0) {
        backendActivities.push({
          id: 'act-response',
          type: 'backend_response',
          skill: result.agentProvider || 'SOC backend',
          text: evidenceCount > 0
            ? `${evidenceCount} élément(s) de preuve transmis par le backend`
            : 'Réponse reçue ; aucune preuve fournisseur n’a été renvoyée',
          status: 'success'
        });
      }
      setMessages(prev => prev.map(m => m.id === agentMsgId ? {
        ...m,
        activities: backendActivities,
        text: result.answer,
        sources: result.sources
      } : m));
      setIsThinking(false);

    } catch (err: unknown) {
      console.error('Chat error:', err);
      const errorMsg = err instanceof Error ? err.message : 'Backend agent assistant is currently unavailable. Ensure the real backend server is running.';
      setMessages(prev => prev.map(m => m.id === agentMsgId ? {
        ...m,
        activities: [{ id: 'act-err', type: 'backend_error', skill: 'SOC backend', text: `Échec de la requête backend : ${errorMsg}`, status: 'failed' }],
        text: errorMsg,
        isError: true
      } : m));
      setIsThinking(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className={fullPage
      ? 'relative w-full h-full min-h-[640px] glass-card rounded-2xl border border-purple-500/40 shadow-2xl shadow-purple-500/20 flex flex-col overflow-hidden'
      : 'fixed bottom-6 right-6 w-96 h-[580px] glass-card rounded-2xl border border-purple-500/40 shadow-2xl shadow-purple-500/20 z-50 flex flex-col overflow-hidden'}>
      {/* Header */}
      <div className="h-14 bg-[#12121d] border-b border-purple-500/25 px-4 flex items-center justify-between">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-purple-600 to-indigo-600 flex items-center justify-center shadow-md shadow-purple-500/30">
            <Bot className="w-4 h-4 text-white animate-pulse" />
          </div>
          <div>
            <h3 className="text-xs font-black text-white">SOC Analyst Chat</h3>
            <span className="text-[10px] text-purple-300">
              {ticketContextId ? `Context: ${ticketContextId}` : 'Backend SOC · port 8787'}
            </span>
          </div>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-white p-1 rounded-lg hover:bg-purple-500/10 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 p-4 overflow-y-auto space-y-4 bg-[#0a0a0f]/90">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'} space-y-2`}>
            {/* Activities / Intermediate MCP events (ChatGPT-style activity timeline) */}
            {msg.activities && msg.activities.length > 0 && (
              <div className="w-full space-y-1.5 pl-1">
                {msg.activities.map((act) => (
                  <div key={act.id} className="p-2.5 rounded-xl bg-[#141420] border border-purple-500/25 text-[11px] flex items-center space-x-2 text-purple-300">
                    {act.status === 'running' ? (
                      <Cpu className="w-3.5 h-3.5 text-purple-400 animate-spin flex-shrink-0" />
                    ) : act.status === 'failed' ? (
                      <AlertCircle className="w-3.5 h-3.5 text-rose-400 flex-shrink-0" />
                    ) : (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                    )}
                    <span className="font-mono truncate">{act.text}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Main Message Bubble */}
            <div className={`max-w-[90%] p-3.5 rounded-2xl text-xs space-y-1.5 ${
              msg.sender === 'user'
                ? 'bg-purple-600 text-white rounded-br-none shadow-md shadow-purple-500/20'
                : msg.isError
                ? 'bg-rose-950/40 text-rose-200 border border-rose-500/30 rounded-bl-none'
                : 'bg-[#141420] text-gray-200 border border-purple-500/20 rounded-bl-none'
            }`}>
              {msg.isError && (
                <div className="flex items-center space-x-1.5 text-rose-400 font-bold pb-1 mb-1 border-b border-rose-500/20">
                  <AlertCircle className="w-4 h-4" />
                  <span>Backend Error / MCP Unavailable</span>
                </div>
              )}
              <p className="leading-relaxed whitespace-pre-wrap">
                {msg.text || (isThinking ? 'Le backend SOC prépare la réponse…' : '')}
              </p>
              {msg.sources && msg.sources.length > 0 && (
                <div className="pt-2 border-t border-purple-500/15 text-[10px] text-purple-300 font-mono">
                  <span>Sources: {msg.sources.join(', ')}</span>
                </div>
              )}
            </div>
            <span className="text-[9px] text-gray-500 px-1">{msg.timestamp}</span>
          </div>
        ))}

        {isThinking && messages[messages.length - 1]?.sender === 'agent' && (
          <div className="flex items-center space-x-2 text-xs text-purple-300 bg-[#141420] p-3 rounded-2xl rounded-bl-none border border-purple-500/20 w-fit">
            <Cpu className="w-4 h-4 animate-spin text-purple-400" />
            <span>Le backend SOC prépare la réponse…</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <form onSubmit={handleSend} className="p-3 bg-[#12121d] border-t border-purple-500/25 flex items-center space-x-2">
        <input
          type="text"
          placeholder="Ask Codex (e.g. 'give me the last critical alert sous elastic')..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="flex-1 bg-[#0a0a0f] border border-purple-500/25 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none focus:border-purple-500"
        />
        <button
          type="submit"
          className="p-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white transition-all shadow-md shadow-purple-500/20 flex-shrink-0"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}
