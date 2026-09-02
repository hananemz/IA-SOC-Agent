'use client';

import React, { useState, useEffect } from 'react';
import { RefreshCw, Bot, Calendar, MessageSquare, Wifi, WifiOff } from 'lucide-react';
import { getCurrentUser, UserProfile } from '@/lib/api';
import { getInitials } from '@/lib/auth';

interface HeaderProps {
  title: string;
  subtitle: string;
  onRefresh?: () => void;
  isRefreshing?: boolean;
  onOpenChat?: () => void;
}

export default function Header({ title, subtitle, onRefresh, isRefreshing = false, onOpenChat }: HeaderProps) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isBackendConnected, setIsBackendConnected] = useState<boolean>(true);

  useEffect(() => {
    getCurrentUser()
      .then(setUser)
      .catch(() => setIsBackendConnected(false));

    // Health check ping
    const checkHealth = async () => {
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
        const res = await fetch(`${baseUrl}/health`, { method: 'GET' });
        setIsBackendConnected(res.ok);
      } catch {
        // If fetch fails completely, backend might be offline
        setIsBackendConnected(false);
      }
    };
    checkHealth();
  }, []);

  const initials = user ? getInitials(user.name) : 'U';

  return (
    <header className="h-20 border-b border-purple-500/15 bg-[#0e0e16]/80 backdrop-blur-md px-8 flex items-center justify-between sticky top-0 z-30">
      <div className="flex flex-col">
        <h1 className="text-2xl font-black tracking-tight text-white flex items-center space-x-3">
          <span>{title}</span>
          <span className="inline-flex items-center space-x-1.5 px-3 py-0.5 rounded-full text-xs font-medium bg-purple-500/15 text-purple-300 border border-purple-500/30">
            <Bot className="w-3.5 h-3.5 animate-pulse text-purple-400" />
            <span>Codex Agent Active</span>
            {/* Backend Connection Status Indicator Dot */}
            <span
              className={`w-2 h-2 rounded-full ml-1 ${
                isBackendConnected ? 'bg-emerald-400 animate-ping' : 'bg-rose-500'
              }`}
              title={isBackendConnected ? 'Backend agent connected' : 'Backend agent unreachable'}
            />
          </span>
        </h1>
        <p className="text-xs text-gray-400 mt-0.5">{subtitle}</p>
      </div>

      <div className="flex items-center space-x-4">
        {/* Chat Toggle Button */}
        {onOpenChat && (
          <button
            onClick={onOpenChat}
            className="flex items-center space-x-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white px-3.5 py-1.5 rounded-xl text-xs font-semibold shadow-lg shadow-purple-500/25 transition-all"
            title="Open AI Agent Chat"
          >
            <MessageSquare className="w-3.5 h-3.5" />
            <span className="hidden md:inline">Agent Chat</span>
          </button>
        )}

        {/* Period Selector */}
        <div className="hidden sm:flex items-center space-x-2 bg-[#141420] border border-purple-500/20 px-3 py-1.5 rounded-xl text-xs text-gray-300">
          <Calendar className="w-4 h-4 text-purple-400" />
          <span>Last 30 days</span>
        </div>

        {/* Refresh Button */}
        <button
          onClick={onRefresh}
          className={`flex items-center space-x-2 bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/40 px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all ${
            isRefreshing ? 'opacity-75 cursor-wait' : ''
          }`}
          title="Refresh SOC data"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
          <span className="hidden md:inline">Refresh</span>
        </button>

        {/* Dynamic User Profile */}
        <div className="flex items-center space-x-3 pl-4 border-l border-purple-500/20">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center font-bold text-white text-sm shadow-md shadow-purple-500/20">
            {initials}
          </div>
          <div className="hidden lg:flex flex-col text-left">
            <span className="text-[10px] text-purple-400">{user ? user.role : 'Opérateur'}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
