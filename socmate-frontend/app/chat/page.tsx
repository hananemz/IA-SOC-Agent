'use client';

import { useRouter } from 'next/navigation';
import AgentChatPanel from '@/components/AgentChatPanel';

export default function ChatPage() {
  const router = useRouter();

  return (
    <main className="min-h-screen bg-[#0a0a0f] text-gray-100 p-4 md:p-8">
      <div className="mx-auto max-w-5xl h-[calc(100vh-4rem)] min-h-[680px]">
        <AgentChatPanel
          isOpen
          fullPage
          onClose={() => router.push('/')}
        />
      </div>
    </main>
  );
}
