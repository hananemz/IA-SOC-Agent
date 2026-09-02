'use client';

import React, { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';
import AgentChatPanel from '@/components/AgentChatPanel';
import { getNotifications, NotificationItem } from '@/lib/api';
import { CheckCircle2 } from 'lucide-react';

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [isChatOpen, setIsChatOpen] = useState(false);

  useEffect(() => {
    getNotifications().then(setNotifications);
  }, []);

  const markAllAsRead = () => {
    setNotifications(notifications.map(n => ({ ...n, read: true })));
  };

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-gray-100 flex">
      <Sidebar />
      <div className="flex-1 ml-64 flex flex-col min-w-0">
        <Header
          title="Notifications Center"
          subtitle="Real-time agent alerts, SLA warnings, and review queue updates"
          onOpenChat={() => setIsChatOpen(true)}
        />
        <main className="flex-1 p-8 space-y-6 overflow-y-auto">
          <div className="flex justify-between items-center">
            <span className="text-xs text-purple-300 font-semibold">{notifications.filter(n => !n.read).length} Unread Notifications</span>
            <button
              onClick={markAllAsRead}
              className="px-4 py-2 rounded-xl bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/40 text-xs font-semibold flex items-center space-x-1.5 transition-colors"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>Mark All as Read</span>
            </button>
          </div>

          <div className="space-y-3">
            {notifications.map((notif) => (
              <div
                key={notif.id}
                className={`p-4 rounded-2xl glass-card border flex items-center justify-between transition-all ${
                  notif.read ? 'border-purple-500/10 opacity-70' : 'border-purple-500/30 bg-purple-500/5'
                }`}
              >
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-bold text-white">{notif.title}</span>
                    {!notif.read && <span className="w-2 h-2 rounded-full bg-purple-500"></span>}
                  </div>
                  <p className="text-xs text-gray-300">{notif.message}</p>
                  <span className="text-[10px] text-gray-400">{notif.timestamp}</span>
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
