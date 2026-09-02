import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "IA SOC Agent | SOC IA Agent Platform",
  description: "Autonomous Security Operations Center platform driven by Codex Agent, SOC RAG, and MCP skills.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr" className="dark">
      <body className="antialiased bg-[#0a0a0f] text-gray-100">
        {children}
      </body>
    </html>
  );
}
