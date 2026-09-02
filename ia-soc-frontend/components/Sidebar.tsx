'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  AlertTriangle,
  Ticket,
  Network,
  ShieldAlert,
  BookOpen,
  ClipboardCheck,
  Cpu,
  Activity,
  Settings,
  Building2,
  Bell,
  MessageSquare,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Shield
} from 'lucide-react';

interface SidebarProps {
  unprocessedAlertsCount?: number;
  openTicketsCount?: number;
  reviewQueueCount?: number;
  notificationsCount?: number;
}

export default function Sidebar({
  unprocessedAlertsCount = 3,
  openTicketsCount = 8,
  reviewQueueCount = 3,
  notificationsCount = 2
}: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);
  const pathname = usePathname();

  const navItems = [
    { name: 'Overview', href: '/', icon: LayoutDashboard },
    { name: 'SOC Agent Chat', href: '/chat', icon: MessageSquare },
    { name: 'Alerts', href: '/alerts', icon: AlertTriangle, badge: unprocessedAlertsCount, badgeColor: 'bg-rose-500/20 text-rose-400 border border-rose-500/30' },
    { name: 'Tickets', href: '/tickets', icon: Ticket, badge: openTicketsCount, badgeColor: 'bg-purple-500/20 text-purple-400 border border-purple-500/30' },
    { name: 'Correlations', href: '/correlations', icon: Network },
    { name: 'IOCs', href: '/iocs', icon: ShieldAlert },
    { name: 'Playbook Templates', href: '/playbooks', icon: BookOpen },
    { name: 'Review Queue', href: '/review-queue', icon: ClipboardCheck, badge: reviewQueueCount, badgeColor: 'bg-amber-500/20 text-amber-400 border border-amber-500/30' },
    { name: 'AI Gym', href: '/ai-gym', icon: Cpu },
    { name: 'AI Performance', href: '/ai-performance', icon: Activity },
    { name: 'Admin', href: '/admin', icon: Settings },
    { name: 'Client List', href: '/clients', icon: Building2 },
    { name: 'Notifications', href: '/notifications', icon: Bell, badge: notificationsCount, badgeColor: 'bg-blue-500/20 text-blue-400 border border-blue-500/30' },
  ];

  return (
    <aside
      className={`fixed top-0 left-0 h-screen bg-[#0e0e16] border-r border-purple-500/20 transition-all duration-300 z-40 flex flex-col ${
        collapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Brand Header */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-purple-500/25 bg-[#12121d]">
        <div className="flex items-center space-x-3 overflow-hidden">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-purple-600 via-indigo-600 to-pink-500 flex items-center justify-center shadow-lg shadow-purple-500/30 flex-shrink-0">
            <Shield className="w-6 h-6 text-white" />
          </div>
          {!collapsed && (
            <div className="flex flex-col">
              <span className="font-black text-lg tracking-wider bg-gradient-to-r from-white via-purple-200 to-purple-400 bg-clip-text text-transparent truncate">
                IA SOC Agent
              </span>
              <span className="text-[10px] text-purple-400/80 tracking-widest uppercase font-semibold">
                SOC IA Agent
              </span>
            </div>
          )}
        </div>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="text-gray-400 hover:text-white p-1.5 rounded-lg hover:bg-purple-500/10 transition-colors"
          title={collapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
        >
          {collapsed ? <ChevronRight className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />}
        </button>
      </div>

      {/* Navigation Items */}
      <div className="flex-1 overflow-y-auto py-4 px-3 space-y-1.5">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center justify-between px-3 py-2.5 rounded-xl transition-all group ${
                isActive
                  ? 'bg-gradient-to-r from-purple-600/30 to-indigo-600/20 text-white border border-purple-500/40 shadow-sm shadow-purple-500/20'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-white/[0.04]'
              }`}
              title={collapsed ? item.name : undefined}
            >
              <div className="flex items-center space-x-3 min-w-0">
                <Icon
                  className={`w-5 h-5 flex-shrink-0 transition-colors ${
                    isActive ? 'text-purple-400' : 'text-gray-400 group-hover:text-purple-300'
                  }`}
                />
                {!collapsed && (
                  <span className="text-sm font-medium truncate">{item.name}</span>
                )}
              </div>
              {!collapsed && item.badge !== undefined && item.badge > 0 && (
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${item.badgeColor}`}>
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </div>

      {/* Footer / Logout */}
      <div className="p-3 border-t border-purple-500/20 bg-[#12121d]/50">
        <button
          onClick={() => alert('Logged out successfully (mock action)')}
          className="w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl text-rose-400 hover:bg-rose-500/10 transition-colors group"
          title={collapsed ? 'Logout' : undefined}
        >
          <LogOut className="w-5 h-5 flex-shrink-0 text-rose-400 group-hover:scale-110 transition-transform" />
          {!collapsed && <span className="text-sm font-medium">Logout</span>}
        </button>
      </div>
    </aside>
  );
}
