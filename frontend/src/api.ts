/** API Client for HackEventHub.ai */

export interface HealthResponse {
  status: string;
  version: string;
  active_provider: string;
}

export interface ProviderItem {
  name: string;
  is_active: boolean;
  base_url: string;
  model_name: string;
  has_api_key: boolean;
  supports_tool_calling: boolean | null;
  supports_json_mode: boolean | null;
  last_test_at: string | null;
  last_test_latency_ms: number | null;
  last_test_error: string;
  capabilities: {
    tool_calling?: boolean;
    json_mode?: boolean;
    reasoning_effort?: boolean;
  };
  task_profiling: string;
  task_extraction: string;
  task_relevance: string;
  task_chat: string;
}

export interface ToolItem {
  id: number;
  url: string;
  name: string;
  kind: string | null;
  domain: string | null;
  description: string;
  fetch_method: string | null;
  listing_urls: string[];
  needs_js: boolean;
  crawl_interval_minutes: number;
  enabled: boolean;
  agent_visible: boolean;
  is_preset: boolean;
  user_note: string;
  profile_confidence: number;
  profile_json: any;
  status: string | null;
  last_run_at: string | null;
  last_status: string;
  last_error: string;
  items_total: number;
  robots_txt_ok: boolean | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface ItemData {
  id: number;
  domain: string;
  tool_id: number;
  title: string;
  url: string;
  location_text: string;
  is_online: boolean;
  city: string;
  start_date: string | null;
  end_date: string | null;
  price_status: "free" | "paid" | "unknown";
  price_text: string;
  organizer: string;
  description_snippet: string;
  tags: string[];
  first_seen_at: string | null;
  last_seen_at: string | null;
  relevance_score: number;
  relevance_reason: string;
  status: "new" | "sent" | "saved" | "hidden";
}

export interface InterestsData {
  id: number;
  topics_include: string[];
  topics_exclude: string[];
  cities: string[];
  include_online: boolean;
  free_only: boolean;
  skill_level: string;
  max_items_per_digest: number;
  min_relevance: number;
  instant_alerts: boolean;
  digest_time: string;
  timezone: string;
  quiet_hours_start: string;
  quiet_hours_end: string;
}

export interface RunLogItem {
  id: number;
  tool_id: number;
  started_at: string | null;
  finished_at: string | null;
  status: string;
  items_found: number;
  items_new: number;
  error: string;
  fetch_method: string;
  cost_units: number;
}

export interface AgentToolItem {
  function_name: string;
  enabled: boolean;
  description: string;
}

const API_BASE = "/api";

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem("dashboard_token");
  const headers = new Headers(options.headers || {});
  headers.set("Content-Type", "application/json");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(errorText || `API error ${res.status}`);
  }

  return res.json();
}

export const api = {
  getHealth: () => request<HealthResponse>("/health"),
  getProviders: () => request<{ providers: ProviderItem[] }>("/providers"),
  setActiveProvider: (provider: string) =>
    request<{ active: string }>("/providers/active", {
      method: "PUT",
      body: JSON.stringify({ provider }),
    }),
  testProvider: (name: string) =>
    request<any>(`/providers/${name}/test`, { method: "POST" }),
  updateProviderConfig: (name: string, update: any) =>
    request<{ ok: boolean }>(`/providers/${name}/config`, {
      method: "PUT",
      body: JSON.stringify(update),
    }),
  getTools: () => request<{ tools: ToolItem[] }>("/tools"),
  createTool: (url: string, note = "") =>
    request<ToolItem>("/tools", {
      method: "POST",
      body: JSON.stringify({ url, note }),
    }),
  updateTool: (id: number, data: Partial<ToolItem>) =>
    request<ToolItem>(`/tools/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  confirmTool: (id: number) =>
    request<ToolItem>(`/tools/${id}/confirm`, { method: "POST" }),
  deleteTool: (id: number) =>
    request<{ ok: boolean }>(`/tools/${id}`, { method: "DELETE" }),
  bulkImport: (tools: { url: string; note?: string }[]) =>
    request<{ created: any[]; skipped: string[] }>("/tools/bulk-import", {
      method: "POST",
      body: JSON.stringify({ tools }),
    }),
  getItems: (params: Record<string, any> = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") query.append(k, String(v));
    });
    return request<{ items: ItemData[] }>(`/items?${query.toString()}`);
  },
  saveItem: (id: number) =>
    request<{ ok: boolean; item: ItemData }>(`/items/${id}/save`, {
      method: "POST",
    }),
  hideItem: (id: number) =>
    request<{ ok: boolean; item: ItemData }>(`/items/${id}/hide`, {
      method: "POST",
    }),
  getInterests: () => request<InterestsData>("/interests"),
  updateInterests: (data: Partial<InterestsData>) =>
    request<InterestsData>("/interests", {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  getRuns: (params: Record<string, any> = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") query.append(k, String(v));
    });
    return request<{ runs: RunLogItem[] }>(`/runs?${query.toString()}`);
  },
  triggerRunAll: () =>
    request<{ status: string; message: string }>("/runs", { method: "POST" }),
  getAgentTools: () => request<{ tools: AgentToolItem[] }>("/agent-tools"),
  toggleAgentTool: (function_name: string, enabled: boolean) =>
    request<{ function_name: string; enabled: boolean }>(
      `/agent-tools/${function_name}/toggle`,
      {
        method: "PUT",
        body: JSON.stringify({ enabled }),
      }
    ),
  chat: (messages: { role: string; content: string }[], provider?: string) =>
    request<any>("/chat", {
      method: "POST",
      body: JSON.stringify({ messages, provider }),
    }),
};
