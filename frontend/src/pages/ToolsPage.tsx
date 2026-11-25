import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Plus,
  CheckCircle,
  XCircle,
  Globe,
  Trash2,
  Upload,
  Settings2,
  RefreshCw,
  SlidersHorizontal,
} from "lucide-react";
import { api, ToolItem } from "../api";

export const ToolsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [newUrl, setNewUrl] = useState("");
  const [newNote, setNewNote] = useState("");
  const [bulkText, setBulkText] = useState("");
  const [showBulk, setShowBulk] = useState(false);

  const { data: toolsData, isLoading } = useQuery({
    queryKey: ["tools"],
    queryFn: api.getTools,
  });

  const { data: agentToolsData } = useQuery({
    queryKey: ["agent-tools"],
    queryFn: api.getAgentTools,
  });

  const createMutation = useMutation({
    mutationFn: () => api.createTool(newUrl, newNote),
    onSuccess: () => {
      setNewUrl("");
      setNewNote("");
      queryClient.invalidateQueries({ queryKey: ["tools"] });
    },
  });

  const confirmMutation = useMutation({
    mutationFn: (id: number) => api.confirmTool(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["tools"] }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.deleteTool(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["tools"] }),
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: number; enabled: boolean }) =>
      api.updateTool(id, { enabled }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["tools"] }),
  });

  const toggleAgentMutation = useMutation({
    mutationFn: ({ name, enabled }: { name: string; enabled: boolean }) =>
      api.toggleAgentTool(name, enabled),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["agent-tools"] }),
  });

  const bulkMutation = useMutation({
    mutationFn: (urls: string[]) =>
      api.bulkImport(urls.map((u) => ({ url: u.trim() }))),
    onSuccess: () => {
      setBulkText("");
      setShowBulk(false);
      queryClient.invalidateQueries({ queryKey: ["tools"] });
    },
  });

  const handleBulkSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const urls = bulkText.split("\n").filter((u) => u.trim().startsWith("http"));
    if (urls.length > 0) {
      bulkMutation.mutate(urls);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
            Tool Registry (Registered Sites)
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Register websites to crawl. New sites are auto-profiled by the LLM and wait for confirmation.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowBulk(!showBulk)}
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800"
          >
            <Upload className="w-3.5 h-3.5" />
            Bulk Import
          </button>
        </div>
      </div>

      {/* Add New Tool Box */}
      <div className="p-6 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm space-y-4">
        <h3 className="font-semibold text-sm text-slate-900 dark:text-white flex items-center gap-2">
          <Plus className="w-4 h-4 text-indigo-600" />
          Add Website to Crawl
        </h3>
        <div className="flex flex-col sm:flex-row gap-3">
          <input
            type="url"
            value={newUrl}
            onChange={(e) => setNewUrl(e.target.value)}
            placeholder="https://devpost.com/hackathons or https://mlh.io/events"
            className="flex-1 px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/60 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <input
            type="text"
            value={newNote}
            onChange={(e) => setNewNote(e.target.value)}
            placeholder="Optional note (e.g. looking for Web3 & AI hackathons)"
            className="sm:w-80 px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/60 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <button
            onClick={() => createMutation.mutate()}
            disabled={!newUrl || createMutation.isPending}
            className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm rounded-xl shadow-md disabled:opacity-50"
          >
            {createMutation.isPending ? "Profiling..." : "Add & Profile"}
          </button>
        </div>
      </div>

      {/* Bulk Import Modal / Expander */}
      {showBulk && (
        <form
          onSubmit={handleBulkSubmit}
          className="p-6 rounded-2xl border border-indigo-200 dark:border-indigo-900 bg-indigo-50/50 dark:bg-indigo-950/20 space-y-3"
        >
          <h4 className="font-semibold text-sm text-indigo-950 dark:text-indigo-200">
            Paste URL List (One per line)
          </h4>
          <textarea
            value={bulkText}
            onChange={(e) => setBulkText(e.target.value)}
            rows={4}
            placeholder="https://example1.com/events&#10;https://example2.com/hackathons"
            className="w-full p-3 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm font-mono"
          />
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setShowBulk(false)}
              className="px-3 py-1.5 text-xs text-slate-500 hover:text-slate-800"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={bulkMutation.isPending}
              className="px-4 py-1.5 bg-indigo-600 text-white text-xs font-semibold rounded-lg hover:bg-indigo-700"
            >
              {bulkMutation.isPending ? "Importing..." : "Start Bulk Profile"}
            </button>
          </div>
        </form>
      )}

      {/* Tools Table */}
      <div className="border border-slate-200 dark:border-slate-800 rounded-2xl bg-white dark:bg-slate-900 overflow-hidden shadow-sm">
        <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
          <h3 className="font-bold text-sm text-slate-900 dark:text-white">
            Registered Websites ({toolsData?.tools.length || 0})
          </h3>
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-sm text-slate-500">Loading tools...</div>
        ) : toolsData?.tools.length === 0 ? (
          <div className="p-8 text-center text-sm text-slate-500">
            No websites registered yet. Add a URL above to profile and confirm.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 dark:bg-slate-800/50 text-xs uppercase text-slate-500 font-semibold border-b border-slate-200 dark:border-slate-800">
                <tr>
                  <th className="px-6 py-3">Site / Target</th>
                  <th className="px-6 py-3">Type</th>
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3">Crawling</th>
                  <th className="px-6 py-3">Agent Visible</th>
                  <th className="px-6 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {toolsData?.tools.map((tool) => (
                  <tr key={tool.id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40">
                    <td className="px-6 py-4">
                      <div className="font-semibold text-slate-900 dark:text-white">
                        {tool.name || tool.url}
                      </div>
                      <a
                        href={tool.url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1"
                      >
                        <Globe className="w-3 h-3" />
                        {tool.url}
                      </a>
                    </td>

                    <td className="px-6 py-4">
                      <span className="text-xs px-2.5 py-1 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium">
                        {tool.kind || "other"}
                      </span>
                    </td>

                    <td className="px-6 py-4">
                      {tool.status === "draft" ? (
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300">
                            Draft (Needs Review)
                          </span>
                          <button
                            onClick={() => confirmMutation.mutate(tool.id)}
                            className="px-2 py-0.5 text-xs font-bold bg-emerald-600 text-white rounded hover:bg-emerald-700"
                          >
                            Confirm
                          </button>
                        </div>
                      ) : (
                        <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
                          Active
                        </span>
                      )}
                    </td>

                    <td className="px-6 py-4">
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={tool.enabled}
                          onChange={(e) =>
                            toggleMutation.mutate({ id: tool.id, enabled: e.target.checked })
                          }
                          className="sr-only peer"
                        />
                        <div className="w-9 h-5 bg-slate-200 peer-focus:outline-none rounded-full peer dark:bg-slate-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all dark:border-slate-600 peer-checked:bg-indigo-600"></div>
                      </label>
                    </td>

                    <td className="px-6 py-4">
                      <span
                        className={`text-xs font-medium ${
                          tool.agent_visible
                            ? "text-emerald-600 dark:text-emerald-400"
                            : "text-slate-400"
                        }`}
                      >
                        {tool.agent_visible ? "Yes" : "Hidden"}
                      </span>
                    </td>

                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => deleteMutation.mutate(tool.id)}
                        className="p-1.5 text-slate-400 hover:text-red-500 rounded-lg hover:bg-red-50 dark:hover:bg-red-950/40"
                        title="Delete tool"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Built-in Agent Tools Toggle Panel */}
      <div className="p-6 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-bold text-sm text-slate-900 dark:text-white flex items-center gap-2">
              <SlidersHorizontal className="w-4 h-4 text-indigo-600" />
              Built-in Agent Tool Functions
            </h3>
            <p className="text-xs text-slate-500">
              Enable or disable agent functions. Changes take effect on every request immediately.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {agentToolsData?.tools.map((func) => (
            <div
              key={func.function_name}
              className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 flex items-start justify-between gap-2"
            >
              <div className="space-y-1">
                <span className="font-mono text-xs font-semibold text-slate-900 dark:text-white">
                  {func.function_name}()
                </span>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-tight">
                  {func.description}
                </p>
              </div>

              <input
                type="checkbox"
                checked={func.enabled}
                onChange={(e) =>
                  toggleAgentMutation.mutate({
                    name: func.function_name,
                    enabled: e.target.checked,
                  })
                }
                className="w-4 h-4 text-indigo-600 rounded border-slate-300 focus:ring-indigo-500 shrink-0"
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
