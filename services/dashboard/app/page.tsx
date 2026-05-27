import React from "react";

export default function OverviewPage() {
  return (
    <div className="space-y-8">
      {/* Dynamic Title */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white">System Overview</h2>
          <p className="text-slate-400 mt-1">Real-time status of your self-hosted AI engine.</p>
        </div>
        <div className="flex gap-2">
          <span className="flex h-3 w-3 items-center justify-center rounded-full bg-teal-400/20">
            <span className="h-2.5 w-2.5 rounded-full bg-teal-400 animate-pulse"></span>
          </span>
          <span className="text-sm font-medium text-teal-400">All Systems Operational</span>
        </div>
      </div>

      {/* Database Integration Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="rounded-xl border border-slate-800/60 bg-slate-900/20 backdrop-blur-lg p-6 space-y-4 hover:border-slate-700/60 transition-all">
          <div className="flex justify-between items-start">
            <span className="text-2xl">🐘</span>
            <span className="text-xs font-semibold px-2 py-1 rounded bg-teal-500/10 text-teal-400 border border-teal-500/20">Active</span>
          </div>
          <div>
            <h3 className="font-semibold text-white">PostgreSQL</h3>
            <p className="text-xs text-slate-500 mt-1">Persistent State Store</p>
          </div>
        </div>

        <div className="rounded-xl border border-slate-800/60 bg-slate-900/20 backdrop-blur-lg p-6 space-y-4 hover:border-slate-700/60 transition-all">
          <div className="flex justify-between items-start">
            <span className="text-2xl">⚡</span>
            <span className="text-xs font-semibold px-2 py-1 rounded bg-teal-500/10 text-teal-400 border border-teal-500/20">Active</span>
          </div>
          <div>
            <h3 className="font-semibold text-white">Valkey Cache</h3>
            <p className="text-xs text-slate-500 mt-1">Broker & Streams Logging</p>
          </div>
        </div>

        <div className="rounded-xl border border-slate-800/60 bg-slate-900/20 backdrop-blur-lg p-6 space-y-4 hover:border-slate-700/60 transition-all">
          <div className="flex justify-between items-start">
            <span className="text-2xl">🎯</span>
            <span className="text-xs font-semibold px-2 py-1 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">Connected</span>
          </div>
          <div>
            <h3 className="font-semibold text-white">Qdrant DB</h3>
            <p className="text-xs text-slate-500 mt-1">Semantic Memory</p>
          </div>
        </div>

        <div className="rounded-xl border border-slate-800/60 bg-slate-900/20 backdrop-blur-lg p-6 space-y-4 hover:border-slate-700/60 transition-all">
          <div className="flex justify-between items-start">
            <span className="text-2xl">🌿</span>
            <span className="text-xs font-semibold px-2 py-1 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">Connected</span>
          </div>
          <div>
            <h3 className="font-semibold text-white">FalkorDB</h3>
            <p className="text-xs text-slate-500 mt-1">Knowledge Entity Graph</p>
          </div>
        </div>
      </div>

      {/* System Resource Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="rounded-xl border border-slate-800/60 bg-slate-900/20 backdrop-blur-lg p-6 space-y-4">
          <h3 className="text-lg font-bold text-white">Inference Engine Matrix</h3>
          <div className="space-y-3">
            <div className="flex justify-between text-sm py-1 border-b border-slate-800/40">
              <span className="text-slate-400">Ollama API (Active Phase 1)</span>
              <span className="text-slate-200">http://inference:11434</span>
            </div>
            <div className="flex justify-between text-sm py-1 border-b border-slate-800/40">
              <span className="text-slate-400">vLLM Continuous Batcher</span>
              <span className="text-slate-500 font-light">Inactive</span>
            </div>
            <div className="flex justify-between text-sm py-1 border-b border-slate-800/40">
              <span className="text-slate-400">SGLang Engine</span>
              <span className="text-slate-500 font-light">Inactive</span>
            </div>
            <div className="flex justify-between text-sm py-1 border-b border-slate-800/40">
              <span className="text-slate-400">llama.cpp CPU Engine</span>
              <span className="text-slate-500 font-light">Inactive</span>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-slate-800/60 bg-slate-900/20 backdrop-blur-lg p-6 space-y-4">
          <h3 className="text-lg font-bold text-white">Resource Utilization</h3>
          <div className="space-y-4">
            <div className="space-y-1">
              <div className="flex justify-between text-sm text-slate-400">
                <span>VRAM Allocation (openbmb/minicpm5:fp16)</span>
                <span>~1.8 GB / 8.0 GB</span>
              </div>
              <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                <div className="h-full w-[22%] bg-gradient-to-r from-teal-400 to-indigo-500 rounded-full"></div>
              </div>
            </div>
            <div className="space-y-1">
              <div className="flex justify-between text-sm text-slate-400">
                <span>Local GPU Utilization</span>
                <span>12%</span>
              </div>
              <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                <div className="h-full w-[12%] bg-gradient-to-r from-teal-400 to-indigo-500 rounded-full"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
