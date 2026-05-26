"use client";

import React, { useEffect, useState } from "react";

interface EventItem {
  id: string;
  event_type: string;
  data: any;
  timestamp: string;
}

export default function EventStreamPage() {
  const [events, setEvents] = useState<EventItem[]>([]);
  const [status, setStatus] = useState<"connecting" | "connected" | "disconnected">("connecting");

  useEffect(() => {
    // Standard server resolution loading client settings dynamically
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/api/v1/events/ws";
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setStatus("connected");
    };

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        const newItem: EventItem = {
          id: payload.id || Math.random().toString(),
          event_type: payload.event_type || "unknown.event",
          data: payload.data || {},
          timestamp: new Date().toLocaleTimeString(),
        };
        setEvents((prev) => [newItem, ...prev].slice(0, 50));
      } catch (err) {
        console.error("Failed to parse event message:", err);
      }
    };

    ws.onclose = () => {
      setStatus("disconnected");
    };

    return () => {
      ws.close();
    };
  }, []);

  return (
    <div className="space-y-6">
      {/* Title Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white">Live Event Stream</h2>
          <p className="text-slate-400 mt-1">Real-time WebSocket fan-out logs from Valkey streams.</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-slate-800 bg-slate-900/50 backdrop-blur-md">
          <span className={`h-2.5 w-2.5 rounded-full ${
            status === "connected" ? "bg-teal-400 animate-pulse" : status === "connecting" ? "bg-amber-400 animate-pulse" : "bg-rose-400"
          }`} />
          <span className="text-xs font-semibold capitalize text-slate-300">
            {status}
          </span>
        </div>
      </div>

      {/* Events Board */}
      <div className="rounded-xl border border-slate-800 bg-[#0b101c]/60 backdrop-blur-lg p-6 min-h-[500px]">
        {events.length === 0 ? (
          <div className="flex flex-col items-center justify-center min-h-[400px] text-slate-500 space-y-3">
            <span className="text-4xl animate-bounce">📡</span>
            <p className="text-sm">Awaiting system and agent execution events...</p>
          </div>
        ) : (
          <div className="space-y-4">
            {events.map((evt) => {
              // Custom colors based on event categories
              let badgeColor = "bg-slate-500/10 text-slate-400 border-slate-500/20";
              if (evt.event_type.startsWith("agent.")) {
                badgeColor = "bg-indigo-500/10 text-indigo-400 border-indigo-500/20";
              } else if (evt.event_type.startsWith("system.")) {
                badgeColor = "bg-teal-500/10 text-teal-400 border-teal-500/20";
              } else if (evt.event_type.startsWith("workflow.")) {
                badgeColor = "bg-purple-500/10 text-purple-400 border-purple-500/20";
              }
              
              return (
                <div
                  key={evt.id}
                  className="p-4 rounded-lg border border-slate-800/40 bg-slate-900/10 hover:border-slate-700/40 hover:bg-slate-900/20 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4"
                >
                  <div className="space-y-2">
                    <div className="flex items-center gap-3">
                      <span className={`text-xs font-bold px-2 py-1 rounded border ${badgeColor}`}>
                        {evt.event_type}
                      </span>
                      <span className="text-xs text-slate-500">{evt.timestamp}</span>
                    </div>
                    <pre className="text-xs text-slate-400 font-mono max-w-2xl overflow-x-auto">
                      {JSON.stringify(evt.data, null, 2)}
                    </pre>
                  </div>
                  <div className="text-xs font-mono text-slate-600">ID: {evt.id}</div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
