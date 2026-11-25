import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Sparkles,
  Search,
  Bookmark,
  EyeOff,
  ExternalLink,
  MapPin,
  Calendar,
  Tag,
  Check,
} from "lucide-react";
import { api, ItemData } from "../api";

export const ItemsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [cityFilter, setCityFilter] = useState("");
  const [priceFilter, setPriceFilter] = useState<string>("");
  const [onlineOnly, setOnlineOnly] = useState<boolean>(false);

  const { data: itemsData, isLoading } = useQuery({
    queryKey: ["items", search, cityFilter, priceFilter, onlineOnly],
    queryFn: () =>
      api.getItems({
        query: search || undefined,
        city: cityFilter || undefined,
        price_status: priceFilter || undefined,
        is_online: onlineOnly ? true : undefined,
      }),
  });

  const saveMutation = useMutation({
    mutationFn: (id: number) => api.saveItem(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["items"] }),
  });

  const hideMutation = useMutation({
    mutationFn: (id: number) => api.hideItem(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["items"] }),
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
          Opportunities & Events
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Scraped hackathons, conferences, and workshops scored deterministically & by AI.
        </p>
      </div>

      {/* Filter / Search Bar */}
      <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm flex flex-col md:flex-row gap-3 items-center">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search keywords, titles, organizers..."
            className="w-full pl-9 pr-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div className="flex flex-wrap gap-2 w-full md:w-auto">
          <input
            type="text"
            value={cityFilter}
            onChange={(e) => setCityFilter(e.target.value)}
            placeholder="City filter"
            className="px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-sm w-32 focus:outline-none"
          />

          <select
            value={priceFilter}
            onChange={(e) => setPriceFilter(e.target.value)}
            className="px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-sm focus:outline-none"
          >
            <option value="">All Prices</option>
            <option value="free">Free Only</option>
            <option value="paid">Paid</option>
          </select>

          <label className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs font-medium cursor-pointer select-none">
            <input
              type="checkbox"
              checked={onlineOnly}
              onChange={(e) => setOnlineOnly(e.target.checked)}
              className="rounded text-indigo-600 focus:ring-indigo-500"
            />
            Online only
          </label>
        </div>
      </div>

      {/* Items List */}
      {isLoading ? (
        <div className="p-12 text-center text-sm text-slate-500">Loading opportunities...</div>
      ) : itemsData?.items.length === 0 ? (
        <div className="p-12 text-center rounded-2xl border border-dashed border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900">
          <Sparkles className="w-8 h-8 text-slate-400 mx-auto mb-2" />
          <h3 className="font-semibold text-slate-700 dark:text-slate-300">
            No opportunities matched
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            Try adjusting your search filters or registering more websites in Tool Registry.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {itemsData?.items.map((item) => (
            <div
              key={item.id}
              className={`p-5 rounded-2xl border transition-all flex flex-col justify-between ${
                item.status === "saved"
                  ? "border-indigo-400/60 bg-indigo-50/20 dark:bg-indigo-950/20"
                  : "border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900"
              }`}
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-800 dark:bg-indigo-950 dark:text-indigo-300 capitalize">
                      {item.price_status}
                    </span>
                    {item.is_online ? (
                      <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                        Online
                      </span>
                    ) : (
                      item.city && (
                        <span className="text-xs text-slate-500 flex items-center gap-1">
                          <MapPin className="w-3 h-3" />
                          {item.city}
                        </span>
                      )
                    )}
                  </div>

                  <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-amber-50 text-amber-800 dark:bg-amber-950 dark:text-amber-300">
                    Score: {Math.round(item.relevance_score * 100)}%
                  </span>
                </div>

                <h3 className="font-bold text-slate-900 dark:text-white text-base leading-snug">
                  {item.title}
                </h3>

                <p className="text-xs text-slate-600 dark:text-slate-400 line-clamp-3">
                  {item.description_snippet || "No description provided."}
                </p>

                {item.organizer && (
                  <p className="text-xs text-slate-500 font-medium">
                    Organizer: {item.organizer}
                  </p>
                )}
              </div>

              {/* Action Buttons */}
              <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => saveMutation.mutate(item.id)}
                    className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                      item.status === "saved"
                        ? "bg-indigo-600 text-white"
                        : "text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
                    }`}
                  >
                    <Bookmark className="w-3.5 h-3.5" />
                    {item.status === "saved" ? "Saved" : "Save"}
                  </button>

                  <button
                    onClick={() => hideMutation.mutate(item.id)}
                    className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-400 hover:text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800"
                  >
                    <EyeOff className="w-3.5 h-3.5" />
                    Hide
                  </button>
                </div>

                <a
                  href={item.url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-1 px-3.5 py-1.5 rounded-lg bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 text-xs font-bold hover:bg-indigo-100 dark:hover:bg-indigo-900/60"
                >
                  Visit Site
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
