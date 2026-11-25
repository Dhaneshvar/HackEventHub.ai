import React from "react";
import { useQuery } from "@tanstack/react-query";
import { History } from "lucide-react";
import { api } from "../api";

export const RunLogsPage: React.FC = () => {
  const { data: runsData, isLoading } = useQuery({
    queryKey: ["runs"],
    queryFn: () => api.getRuns({ limit: 100 }),
  });

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
          <History className="w-5 h-5 text-indigo-600" />
          Crawler Execution Logs
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          History of website crawl jobs, timings, items extracted, and cost units.
        </p>
      </div>

      <div className="border border-slate-200 dark:border-slate-800 rounded-2xl bg-white dark:bg-slate-900 overflow-hidden shadow-sm">
        {isLoading ? (
          <div className="p-8 text-center text-sm text-slate-500">Loading run logs...</div>
        ) : runsData?.runs.length === 0 ? (
          <div className="p-8 text-center text-sm text-slate-500">
            No crawl runs recorded yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 dark:bg-slate-800/50 text-xs uppercase text-slate-500 font-semibold border-b border-slate-200 dark:border-slate-800">
                <tr>
                  <th className="px-6 py-3">Timestamp</th>
                  <th className="px-6 py-3">Tool ID</th>
                  <th className="px-6 py-3">Method</th>
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3">Items Found</th>
                  <th className="px-6 py-3">New Items</th>
                  <th className="px-6 py-3">Cost Units</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {runsData?.runs.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40">
                    <td className="px-6 py-4 font-mono text-xs text-slate-600 dark:text-slate-400">
                      {r.started_at ? new Date(r.started_at).toLocaleString() : "-"}
                    </td>

                    <td className="px-6 py-4 font-semibold text-slate-800 dark:text-slate-200">
                      Tool #{r.tool_id}
                    </td>

                    <td className="px-6 py-4">
                      <span className="text-xs px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 font-mono">
                        {r.fetch_method || "auto"}
                      </span>
                    </td>

                    <td className="px-6 py-4">
                      <span
                        className={`text-xs font-semibold px-2 py-0.5 rounded-full capitalize ${
                          r.status === "success"
                            ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                            : "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300"
                        }`}
                      >
                        {r.status}
                      </span>
                    </td>

                    <td className="px-6 py-4">{r.items_found}</td>
                    <td className="px-6 py-4 font-bold text-emerald-600 dark:text-emerald-400">
                      +{r.items_new}
                    </td>
                    <td className="px-6 py-4 text-slate-500">{r.cost_units}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
