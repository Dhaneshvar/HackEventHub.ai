import React, { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Sliders, Save, Bell, Clock, MapPin, Tag } from "lucide-react";
import { api, InterestsData } from "../api";

export const InterestsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { data: interests, isLoading } = useQuery({
    queryKey: ["interests"],
    queryFn: api.getInterests,
  });

  const [formData, setFormData] = useState<Partial<InterestsData>>({});
  const [topicInput, setTopicInput] = useState("");
  const [cityInput, setCityInput] = useState("");

  useEffect(() => {
    if (interests) {
      setFormData(interests);
    }
  }, [interests]);

  const updateMutation = useMutation({
    mutationFn: (data: Partial<InterestsData>) => api.updateInterests(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["interests"] });
    },
  });

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    updateMutation.mutate(formData);
  };

  const addTopic = () => {
    if (topicInput.trim()) {
      const current = formData.topics_include || [];
      setFormData({ ...formData, topics_include: [...current, topicInput.trim()] });
      setTopicInput("");
    }
  };

  const removeTopic = (index: number) => {
    const current = [...(formData.topics_include || [])];
    current.splice(index, 1);
    setFormData({ ...formData, topics_include: current });
  };

  const addCity = () => {
    if (cityInput.trim()) {
      const current = formData.cities || [];
      setFormData({ ...formData, cities: [...current, cityInput.trim()] });
      setCityInput("");
    }
  };

  const removeCity = (index: number) => {
    const current = [...(formData.cities || [])];
    current.splice(index, 1);
    setFormData({ ...formData, cities: current });
  };

  return (
    <div className="space-y-8 max-w-4xl">
      <div>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
          Preferences & Telegram Schedule
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Tailor what opportunities get flagged as relevant, configure daily digest times, and alert
          settings.
        </p>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Interests & Topics Card */}
        <div className="p-6 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm space-y-4">
          <h3 className="font-bold text-sm text-slate-900 dark:text-white flex items-center gap-2">
            <Tag className="w-4 h-4 text-indigo-600" />
            Topics of Interest
          </h3>

          <div className="flex gap-2">
            <input
              type="text"
              value={topicInput}
              onChange={(e) => setTopicInput(e.target.value)}
              placeholder="e.g. AI, Hackathon, Rust, Web3"
              className="flex-1 px-3.5 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <button
              type="button"
              onClick={addTopic}
              className="px-4 py-2 bg-indigo-600 text-white rounded-xl text-xs font-semibold hover:bg-indigo-700"
            >
              Add Topic
            </button>
          </div>

          <div className="flex flex-wrap gap-2 pt-2">
            {formData.topics_include?.map((t, idx) => (
              <span
                key={idx}
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800"
              >
                {t}
                <button
                  type="button"
                  onClick={() => removeTopic(idx)}
                  className="hover:text-red-500 font-bold ml-1"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        </div>

        {/* Location & Formats Card */}
        <div className="p-6 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm space-y-4">
          <h3 className="font-bold text-sm text-slate-900 dark:text-white flex items-center gap-2">
            <MapPin className="w-4 h-4 text-indigo-600" />
            Target Cities & Formats
          </h3>

          <div className="flex gap-2">
            <input
              type="text"
              value={cityInput}
              onChange={(e) => setCityInput(e.target.value)}
              placeholder="e.g. Bangalore, San Francisco, London"
              className="flex-1 px-3.5 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <button
              type="button"
              onClick={addCity}
              className="px-4 py-2 bg-indigo-600 text-white rounded-xl text-xs font-semibold hover:bg-indigo-700"
            >
              Add City
            </button>
          </div>

          <div className="flex flex-wrap gap-2 pt-2">
            {formData.cities?.map((c, idx) => (
              <span
                key={idx}
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border border-slate-300 dark:border-slate-700"
              >
                {c}
                <button
                  type="button"
                  onClick={() => removeCity(idx)}
                  className="hover:text-red-500 font-bold ml-1"
                >
                  ×
                </button>
              </span>
            ))}
          </div>

          <div className="pt-2 flex flex-col sm:flex-row gap-4">
            <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.include_online || false}
                onChange={(e) => setFormData({ ...formData, include_online: e.target.checked })}
                className="rounded text-indigo-600 focus:ring-indigo-500"
              />
              Include Virtual / Online Events
            </label>

            <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.free_only || false}
                onChange={(e) => setFormData({ ...formData, free_only: e.target.checked })}
                className="rounded text-indigo-600 focus:ring-indigo-500"
              />
              Free Events Only
            </label>
          </div>
        </div>

        {/* Digest & Schedule Card */}
        <div className="p-6 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm space-y-4">
          <h3 className="font-bold text-sm text-slate-900 dark:text-white flex items-center gap-2">
            <Clock className="w-4 h-4 text-indigo-600" />
            Digest Time & Thresholds
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-500 mb-1">
                Daily Digest Push Time
              </label>
              <input
                type="time"
                value={formData.digest_time || "09:00"}
                onChange={(e) => setFormData({ ...formData, digest_time: e.target.value })}
                className="w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-500 mb-1">
                Timezone
              </label>
              <input
                type="text"
                value={formData.timezone || "UTC"}
                onChange={(e) => setFormData({ ...formData, timezone: e.target.value })}
                className="w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-500 mb-1">
                Minimum Relevance Score ({Math.round((formData.min_relevance || 0.3) * 100)}%)
              </label>
              <input
                type="range"
                min="0.1"
                max="0.9"
                step="0.05"
                value={formData.min_relevance || 0.3}
                onChange={(e) =>
                  setFormData({ ...formData, min_relevance: parseFloat(e.target.value) })
                }
                className="w-full"
              />
            </div>

            <div className="flex items-center pt-4">
              <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.instant_alerts || false}
                  onChange={(e) => setFormData({ ...formData, instant_alerts: e.target.checked })}
                  className="rounded text-indigo-600 focus:ring-indigo-500"
                />
                Push Instant Alerts on High Match
              </label>
            </div>
          </div>
        </div>

        <button
          type="submit"
          disabled={updateMutation.isPending}
          className="flex items-center gap-2 px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-sm shadow-md"
        >
          <Save className="w-4 h-4" />
          {updateMutation.isPending ? "Saving..." : "Save Preferences"}
        </button>
      </form>
    </div>
  );
};
