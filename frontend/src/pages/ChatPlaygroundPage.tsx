import React, { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { MessageSquare, Send, Cpu, Terminal, Sparkles } from "lucide-react";
import { api } from "../api";

interface ChatEntry {
  role: "user" | "assistant";
  content: string;
  tool_calls?: any[];
  provider?: string;
}

export const ChatPlaygroundPage: React.FC = () => {
  const [messages, setMessages] = useState<ChatEntry[]>([
    {
      role: "assistant",
      content:
        "Hello! I am HackEventHub.ai. Ask me about upcoming hackathons, events, or workshops. I only use verified data from your registered tools and never invent items.",
    },
  ]);
  const [input, setInput] = useState("");
  const [selectedProvider, setSelectedProvider] = useState("");

  const { data: providersData } = useQuery({
    queryKey: ["providers"],
    queryFn: api.getProviders,
  });

  const chatMutation = useMutation({
    mutationFn: (newMsgs: { role: string; content: string }[]) =>
      api.chat(newMsgs, selectedProvider || undefined),
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.content,
          tool_calls: data.tool_calls,
          provider: data.provider,
        },
      ]);
    },
  });

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || chatMutation.isPending) return;

    const userMsg: ChatEntry = { role: "user", content: input.trim() };
    const updated = [...messages, userMsg];
    setMessages(updated);
    setInput("");

    chatMutation.mutate(
      updated.map((m) => ({ role: m.role, content: m.content }))
    );
  };

  return (
    <div className="space-y-4 max-w-4xl h-[calc(100vh-10rem)] flex flex-col">
      {/* Top Controls */}
      <div className="flex items-center justify-between pb-2">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-indigo-600" />
            Agent Chat Playground
          </h2>
          <p className="text-xs text-slate-500">
            Interactive debug chat showing tool invocation calls & raw model outputs.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500 font-medium">Model:</span>
          <select
            value={selectedProvider}
            onChange={(e) => setSelectedProvider(e.target.value)}
            className="px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs font-semibold"
          >
            <option value="">(Default Active)</option>
            {providersData?.providers.map((p) => (
              <option key={p.name} value={p.name}>
                {p.name.toUpperCase()}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Messages Pane */}
      <div className="flex-1 overflow-y-auto p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-4">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`flex flex-col ${
              m.role === "user" ? "items-end" : "items-start"
            }`}
          >
            <div
              className={`max-w-2xl px-4 py-3 rounded-2xl text-sm ${
                m.role === "user"
                  ? "bg-indigo-600 text-white"
                  : "bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100"
              }`}
            >
              {m.content}
            </div>

            {/* Tool Calls Inspector */}
            {m.tool_calls && m.tool_calls.length > 0 && (
              <div className="mt-2 p-2.5 rounded-xl bg-slate-950 text-slate-200 font-mono text-xs max-w-2xl w-full border border-slate-800">
                <div className="flex items-center gap-1.5 text-indigo-400 font-bold mb-1">
                  <Terminal className="w-3.5 h-3.5" /> Tool Executed:
                </div>
                {m.tool_calls.map((tc, tIdx) => (
                  <pre key={tIdx} className="overflow-x-auto whitespace-pre-wrap text-[11px]">
                    {tc.function?.name}({tc.function?.arguments})
                  </pre>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Input bar */}
      <form onSubmit={handleSend} className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask e.g. 'What hackathons are happening in Bangalore this month?'"
          className="flex-1 px-4 py-3 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <button
          type="submit"
          disabled={chatMutation.isPending || !input.trim()}
          className="px-5 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-sm shadow-md disabled:opacity-50"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};
