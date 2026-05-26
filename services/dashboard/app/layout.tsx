import React from "react";
import "./globals.css";

export const metadata = {
  title: "🪐 NeuralFolk Dashboard",
  description: "Self-Hosted Local AI Runtime OS Orchestration.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body
        className="min-h-screen bg-[#07090e] text-[#e2e8f0] antialiased"
        style={{ fontFamily: "'Outfit', sans-serif" }}
      >
        <div className="flex min-h-screen">
          {/* Glassmorphic Sidebar */}
          <aside className="w-64 border-r border-[#1e293b]/40 bg-[#0b0f19]/80 backdrop-blur-md p-6 flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-3 mb-8">
                <span className="text-2xl">🪐</span>
                <h1 className="text-xl font-bold tracking-wider bg-gradient-to-r from-teal-400 to-indigo-500 bg-clip-text text-transparent">
                  NeuralFolk
                </h1>
              </div>
              <nav className="space-y-2">
                <a
                  href="/"
                  className="flex items-center gap-3 px-4 py-3 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 transition-all"
                >
                  <span>📊</span>
                  <span className="text-sm font-medium">Overview</span>
                </a>
                <a
                  href="/agents"
                  className="flex items-center gap-3 px-4 py-3 rounded-lg text-slate-400 hover:bg-slate-800/40 hover:text-slate-200 transition-all"
                >
                  <span>🤖</span>
                  <span className="text-sm font-medium">Spawn Agents</span>
                </a>
                <a
                  href="/events"
                  className="flex items-center gap-3 px-4 py-3 rounded-lg text-slate-400 hover:bg-slate-800/40 hover:text-slate-200 transition-all"
                >
                  <span>⚡</span>
                  <span className="text-sm font-medium">Event Stream</span>
                </a>
              </nav>
            </div>
            <div className="border-t border-[#1e293b]/40 pt-4 text-xs text-slate-500">
              <p>v0.1.0 • Air-Gapped Local OS</p>
            </div>
          </aside>

          {/* Main Workspace Area */}
          <main className="flex-1 p-8 overflow-y-auto">{children}</main>
        </div>
      </body>
    </html>
  );
}
