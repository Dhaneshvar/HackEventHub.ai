import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Cpu,
  CheckCircle,
  AlertTriangle,
  Play,
  RotateCw,
  Sparkles,
} from "lucide-react";
import { api, ProviderItem } from "../api";

export const ProvidersPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [testResults, setTestResults] = useState<Record<string, any>>({});

  const { data: providersData, isLoading } = useQuery({
    queryKey: ["providers"],
    queryFn: api.getProviders,
  });

  const setActiveMutation = useMutation({
    mutationFn: (provider: string) => api.setActiveProvider(provider),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["providers"] });
      queryClient.invalidateQueries({ queryKey: ["health"] });
    },
  });

  const testMutation = useMutation({
    mutationFn: (name: string) => api.testProvider(name),
    onSuccess: (data, name) => {
      setTestResults((prev) => ({ ...prev, [name]: data }));
      queryClient.invalidateQueries({ queryKey: ["providers"] });
    },
  });

  const updateConfigMutation = useMutation({
    mutationFn: ({ name, config }: { name: string; config: any }) =>
      api.updateProviderConfig(name, config),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["providers"] }),
  });

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
          LLM Provider Management
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Switch between Ollama (local), Azure OpenAI, and Unisys Athena EA instantly with zero
          service restart.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {providersData?.providers.map((p) => {
          const testRes = testResults[p.name];
          return (
            <div
              key={p.name}
              className={`p-6 rounded-2xl border transition-all flex flex-col justify-between ${
                p.is_active
                  ? "border-indigo-500 shadow-md ring-2 ring-indigo-500/20 bg-white dark:bg-slate-900"
                  : "border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900"
              }`}
            >
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div
                      className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-xs uppercase ${
                        p.is_active
                          ? "bg-indigo-600 text-white"
                          : "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
                      }`}
                    >
                      {p.name.slice(0, 2)}
                    </div>
                    <h3 className="font-bold text-base text-slate-900 dark:text-white capitalize">
                      {p.name === "ollama" ? "Ollama (Local)" : p.name === "azure" ? "Azure OpenAI" : "Unisys Athena EA"}
                    </h3>
                  </div>

                  {p.is_active && (
                    <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300">
                      ACTIVE
                    </span>
                  )}
                </div>

                <div className="text-xs space-y-1 text-slate-500 dark:text-slate-400">
                  <p>
                    <strong>Model:</strong> {p.model_name || "From config/env"}
                  </p>
                  <p className="truncate">
                    <strong>Endpoint:</strong> {p.base_url || "Default"}
                  </p>
                  <p>
                    <strong>API Key:</strong>{" "}
                    {p.has_api_key ? (
                      <span className="text-emerald-600 dark:text-emerald-400">Configured</span>
                    ) : (
                      <span className="text-amber-500">Not set in .env</span>
                    )}
                  </p>
                </div>

                {/* Capabilities pills */}
                <div className="flex flex-wrap gap-1.5 pt-2">
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                    Tool Calling: {p.capabilities.tool_calling ? "Yes" : "No"}
                  </span>
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                    JSON Mode: {p.capabilities.json_mode ? "Yes" : "No"}
                  </span>
                </div>

                {/* Test Result Box */}
                {testRes && (
                  <div
                    className={`p-3 rounded-xl text-xs space-y-1 ${
                      testRes.ok
                        ? "bg-emerald-50 text-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-300"
                        : "bg-red-50 text-red-900 dark:bg-red-950/40 dark:text-red-300"
                    }`}
                  >
                    <p className="font-semibold">
                      {testRes.ok ? `Connected (${testRes.latency_ms}ms)` : "Connection Failed"}
                    </p>
                    {testRes.error && <p className="text-[11px]">{testRes.error}</p>}
                    {testRes.note && <p className="text-[11px] italic">{testRes.note}</p>}
                  </div>
                )}
              </div>

              {/* Action buttons */}
              <div className="mt-6 pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between gap-2">
                <button
                  onClick={() => testMutation.mutate(p.name)}
                  disabled={testMutation.isPending}
                  className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-xs font-semibold text-slate-700 dark:text-slate-200 flex items-center gap-1.5"
                >
                  <RotateCw
                    className={`w-3.5 h-3.5 ${
                      testMutation.isPending ? "animate-spin" : ""
                    }`}
                  />
                  Test
                </button>

                {!p.is_active ? (
                  <button
                    onClick={() => setActiveMutation.mutate(p.name)}
                    disabled={setActiveMutation.isPending}
                    className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-sm"
                  >
                    Make Active
                  </button>
                ) : (
                  <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                    <CheckCircle className="w-4 h-4" /> Selected
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
