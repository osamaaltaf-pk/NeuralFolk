"use client";

import React, { useState } from "react";

export default function SpawnAgentPage() {
  const [model, setModel] = useState("miniCPM5-1B");
  const [task, setTask] = useState("");
  const [hardware, setHardware] = useState("no_gpu");
  const [status, setStatus] = useState<"idle" | "submitting" | "spawned" | "error">("idle");
  const [agentId, setAgentId] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!task) return;

    setStatus("submitting");
    setErrorMsg("");

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    try {
      const response = await fetch(`${apiUrl}/api/v1/agents/spawn`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model,
          task_summary: task,
          hardware,
        }),
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.statusText}`);
      }

      const data = await response.json();
      setAgentId(data.agent_id);
      setStatus("spawned");
      setTask("");
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.message || "Failed to submit request.");
      setStatus("error");
    }
  };

  return (
    <div className="space-y-8 max-w-4xl">
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-white">Spawn Cognitive Agent</h2>
        <p className="text-slate-400 mt-1">Boot up a local, autonomous task executor using reactive loops.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Spawn Form */}
        <div className="md:col-span-2 rounded-xl border border-slate-800 bg-[#0b101c]/60 backdrop-blur-lg p-6 space-y-6">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-300">Select AI Model</label>
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-4 py-3 text-sm text-slate-200 focus:outline-none focus:border-indigo-500 transition-all"
              >
                <option value="miniCPM5-1B">miniCPM5-1B (32k context — primary test model)</option>
                <option value="deepseek-r1:7b">deepseek-r1:7b (reasoning — optional)</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-300">Target Goal / Task Description</label>
              <textarea
                value={task}
                onChange={(e) => setTask(e.target.value)}
                placeholder="Describe exactly what the agent should accomplish (e.g. Audit security logs and search for anomalies)..."
                rows={4}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg p-4 text-sm text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-indigo-500 transition-all"
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-300">Hardware Profile Acceleration</label>
              <div className="grid grid-cols-3 gap-4">
                <button
                  type="button"
                  onClick={() => setHardware("no_gpu")}
                  className={`px-4 py-3 rounded-lg border text-sm font-semibold transition-all ${
                    hardware === "no_gpu"
                      ? "bg-indigo-500/10 text-indigo-400 border-indigo-500"
                      : "bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700"
                  }`}
                >
                  💻 CPU Only
                </button>
                <button
                  type="button"
                  onClick={() => setHardware("nvidia")}
                  className={`px-4 py-3 rounded-lg border text-sm font-semibold transition-all ${
                    hardware === "nvidia"
                      ? "bg-indigo-500/10 text-indigo-400 border-indigo-500"
                      : "bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700"
                  }`}
                >
                  🟢 NVIDIA GPU
                </button>
                <button
                  type="button"
                  onClick={() => setHardware("edge")}
                  className={`px-4 py-3 rounded-lg border text-sm font-semibold transition-all ${
                    hardware === "edge"
                      ? "bg-indigo-500/10 text-indigo-400 border-indigo-500"
                      : "bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700"
                  }`}
                >
                  📱 Edge Devices
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={status === "submitting" || !task}
              className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-800/50 disabled:text-slate-400 text-white font-semibold py-3 px-4 rounded-lg transition-all shadow-lg hover:shadow-indigo-500/10"
            >
              {status === "submitting" ? "Spawning Agent..." : "Spawn Agent Loop"}
            </button>
          </form>
        </div>

        {/* Console & Status log */}
        <div className="rounded-xl border border-slate-800 bg-[#0b101c]/30 p-6 space-y-4">
          <h3 className="text-lg font-bold text-white">Execution Console</h3>
          <div className="min-h-[250px] bg-slate-950/60 rounded-lg p-4 font-mono text-xs text-slate-400 space-y-3 border border-slate-900/60 overflow-y-auto">
            {status === "idle" && (
              <p className="text-slate-600">&gt;_ Waiting to spin up agent...</p>
            )}
            {status === "submitting" && (
              <p className="text-amber-400 animate-pulse">&gt;_ Posting payload to control-plane DDL database...</p>
            )}
            {status === "spawned" && (
              <>
                <p className="text-teal-400">&gt;_ SUCCESS: Agent loop spawned cleanly.</p>
                <p className="text-indigo-400">&gt;_ Agent ID: {agentId}</p>
                <p className="text-slate-300">&gt;_ Celery tasks scheduled in Valkey queue.</p>
                <p className="text-slate-400">&gt;_ Check 'Event Stream' tab for live planning & filesystem tool logs.</p>
              </>
            )}
            {status === "error" && (
              <>
                <p className="text-rose-500">&gt;_ ERROR spawning agent loop:</p>
                <p className="text-rose-400 font-sans">{errorMsg}</p>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
