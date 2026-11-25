import React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  Sparkles,
  Wrench,
  Cpu,
  Play,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  Coins,
  Clock,
  ArrowRight,
} from "lucide-react";
import { api } from "../api";

export const HomePage: React.FC = () => {
  const queryClient = useQueryClient();

  const { data: health } = useQuery({ queryKey: ["health"], queryFn: api.getHealth });
  const { data: providersData } = useQuery({ queryKey: ["providers"], queryFn: api.getProviders });
  const { data: toolsData } = useQuery({ queryKey: ["tools"], queryFn: api.getTools });
  const { data: itemsData } = useQuery({
    queryKey: ["items-recent"],
    queryFn: () => api.getItems({ limit: 5 }),
  });
  const { data: runsData } = useQuery({
    queryKey: ["runs-recent"],
    queryFn: () => api.getRuns({ limit: 4 }),
  });

  const runAllMutation = useMutation({
    mutationFn: api.triggerRunAll,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["runs-recent"] });
      queryClient.invalidateQueries({ queryKey: ["items-recent"] });
    },
  });

  const activeProvider = providersData?.providers.find((p) => p.is_active);
  const enabledToolsCount = toolsData?.tools.filter((t) => t.enabled).length || 0;
  const totalItemsCount = itemsData?.items.length || 0;

  return (
    <div className="space-y-8">
      {/* Hero / Action Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-6 rounded-2xl bg-gradient-to-r from-indigo-900 via-indigo-800 to-slate-900 text-white shadow-xl">
        <div>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/30 text-indigo-200 mb-3 border border-indigo-400/20">
            <Sparkles className="w-3.5 h-3.5 text-indigo-300" />
            AI Opportunity Scout
          </span>
          <h2 className="text-2xl md:text-3xl font-extrabold tracking-tight">
            HackEventHub.ai Opportunity Radar
          </h2>
          <p className="mt-1 text-sm text-indigo-200 max-w-xl">
            Auto-profiles hackathons, conferences, and workshops, evaluates relevance against your
            interests, and pushes alerts directly to Telegram.
          </p>
        </div>

        <button
          onClick={() => runAllMutation.mutate()}
          disabled={runAllMutation.isPending}
          className="flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-white text-indigo-950 font-bold hover:bg-indigo-50 active:scale-95 transition-all shadow-md shrink-0 disabled:opacity-50"
        >
          <Play className="w-4 h-4 fill-current text-indigo-600" />
          {runAllMutation.isPending ? "Queuing..." : "Run All Tools Now"}
        </button>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Active Provider */}
        <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Active LLM
            </span>
            <Cpu className="w-4 h-4 text-indigo-500" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-xl font-bold text-slate-900 dark:text-white capitalize">
              {activeProvider?.name || health?.active_provider || "None"}
            </span>
            <span className="text-xs text-emerald-600 dark:text-emerald-400 font-medium">
              Ready
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-500 truncate">
            Model: {activeProvider?.model_name || "default"}
          </p>
        </div>

        {/* Card 2: Registered Sites */}
        <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Target Tools
            </span>
            <Wrench className="w-4 h-4 text-violet-500" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-slate-900 dark:text-white">
              {enabledToolsCount}
            </span>
            <span className="text-xs text-slate-500">
              of {toolsData?.tools.length || 0} active
            </span>
          </div>
          <Link
            to="/tools"
            className="mt-1 text-xs text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1"
          >
            Manage websites <ArrowRight className="w-3 h-3" />
          </Link>
        </div>

        {/* Card 3: Opportunities Found */}
        <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Discovered
            </span>
            <Sparkles className="w-4 h-4 text-amber-500" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-slate-900 dark:text-white">
              {totalItemsCount}
            </span>
            <span className="text-xs text-slate-500">recent items</span>
          </div>
          <Link
            to="/items"
            className="mt-1 text-xs text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1"
          >
            View list <ArrowRight className="w-3 h-3" />
          </Link>
        </div>

        {/* Card 4: TinyFish Budget Guard */}
        <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Scraping Guard
            </span>
            <Coins className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-xl font-bold text-slate-900 dark:text-white">
              Budget Safe
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-500">
            Fetch: 0/100 · Agent: 0/10
          </p>
        </div>
      </div>

      {/* Main Grid: Latest Opportunities & Recent Runs */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Top Opportunities */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
              Latest Opportunities
            </h3>
            <Link
              to="/items"
              className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline"
            >
              See all
            </Link>
          </div>

          {itemsData?.items.length === 0 ? (
            <div className="p-8 text-center rounded-xl border border-dashed border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900">
              <p className="text-sm text-slate-500 dark:text-slate-400">
                No items found yet. Add websites in the <strong>Tool Registry</strong> or trigger a run.
              </p>
              <Link
                to="/tools"
                className="mt-3 inline-block px-4 py-2 text-xs font-semibold text-white bg-indigo-600 rounded-lg hover:bg-indigo-700"
              >
                Add Your First Tool
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {itemsData?.items.map((item) => (
                <div
                  key={item.id}
                  className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:shadow-md transition-shadow flex items-start justify-between gap-4"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 capitalize">
                        {item.price_status}
                      </span>
                      {item.is_online ? (
                        <span className="text-xs font-medium px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300">
                          Online
                        </span>
                      ) : (
                        <span className="text-xs text-slate-500">{item.city}</span>
                      )}
                    </div>
                    <h4 className="font-semibold text-slate-900 dark:text-white text-base">
                      {item.title}
                    </h4>
                    <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-2">
                      {item.description_snippet || "No description preview available."}
                    </p>
                  </div>

                  <a
                    href={item.url}
                    target="_blank"
                    rel="noreferrer"
                    className="p-2 text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 shrink-0"
                    title="Open opportunity"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </a>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: Execution Health & Logs */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Clock className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
              Recent Crawler Runs
            </h3>
            <Link
              to="/logs"
              className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline"
            >
              All logs
            </Link>
          </div>

          <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-3">
            {runsData?.runs.length === 0 ? (
              <p className="text-xs text-slate-500 text-center py-4">
                No crawler runs recorded yet.
              </p>
            ) : (
              runsData?.runs.map((run) => (
                <div
                  key={run.id}
                  className="flex items-center justify-between py-2 border-b border-slate-100 dark:border-slate-800/80 last:border-0"
                >
                  <div className="flex items-center gap-2.5">
                    {run.status === "success" ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                    ) : (
                      <AlertCircle className="w-4 h-4 text-amber-500" />
                    )}
                    <div>
                      <p className="text-xs font-medium text-slate-800 dark:text-slate-200">
                        Tool #{run.tool_id} ({run.fetch_method || "auto"})
                      </p>
                      <span className="text-[10px] text-slate-400">
                        {run.started_at ? new Date(run.started_at).toLocaleTimeString() : ""}
                      </span>
                    </div>
                  </div>

                  <span className="text-xs font-bold text-slate-700 dark:text-slate-300">
                    +{run.items_new} new
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
