import type {
  ApiError,
  GenerationStage,
  Health,
  LabTask,
  Preset,
  ReportEdits,
  ReportRecord,
  ReportSummary,
  StudentProfile,
  University,
  LabDetails,
} from "./types";

/**
 * Prefer a same-origin `/backend` proxy (see next.config.ts rewrites) so PDF
 * iframes are not cross-origin — Chrome often shows a black pane otherwise.
 * Override with NEXT_PUBLIC_LABPULSE_API when needed.
 */
export const API_BASE =
  process.env.NEXT_PUBLIC_LABPULSE_API ??
  (typeof window !== "undefined" ? `${window.location.origin}/backend` : "http://127.0.0.1:8080");

export class ApiRequestError extends Error implements ApiError {
  constructor(
    public code: string,
    message: string,
    public status?: number,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, init);
  } catch {
    throw new ApiRequestError("backend_unreachable", "The EzLab server isn't running.");
  }
  if (!response.ok) {
    let code = "http_error";
    let message = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      const detail = body?.detail;
      if (typeof detail === "string") message = detail;
      else if (detail?.message) {
        message = detail.message;
        code = detail.code ?? code;
      }
    } catch {
      /* non-JSON error body */
    }
    throw new ApiRequestError(code, message, response.status);
  }
  return (await response.json()) as T;
}

const json = (body: unknown): RequestInit => ({
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export const api = {
  health: () => request<Health>("/health"),
  universities: () => request<University[]>("/universities"),
  profile: () => request<StudentProfile | null>("/profile"),
  saveProfile: (profile: StudentProfile) =>
    request<StudentProfile>("/profile", { method: "PUT", ...json(profile) }),
  presets: () => request<Preset[]>("/presets"),
  reports: () => request<ReportSummary[]>("/reports"),
  report: (id: string) => request<ReportRecord>(`/reports/${encodeURIComponent(id)}`),
  deleteReport: (id: string) =>
    request<{ deleted: string }>(`/reports/${encodeURIComponent(id)}`, { method: "DELETE" }),
  editReport: (id: string, edits: ReportEdits) =>
    request<ReportRecord>(`/reports/${encodeURIComponent(id)}/edit`, { method: "POST", ...json(edits) }),
  parseManual: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<{ text: string; fields: LabDetails; tasks: LabTask[] }>("/manual/parse", {
      method: "POST",
      body: form,
    });
  },
};

export function fileUrl(
  id: string,
  kind: "pdf" | "docx" | "plot" | "preview",
  opts: { download?: boolean; version?: string } = {},
) {
  const params = new URLSearchParams();
  if (opts.download) params.set("download", "true");
  if (opts.version) params.set("v", opts.version);
  const query = params.toString();
  return `${API_BASE}/reports/${encodeURIComponent(id)}/files/${kind}${query ? `?${query}` : ""}`;
}

export function figureUrl(id: string, filename: string, version?: string) {
  const params = version ? `?v=${encodeURIComponent(version)}` : "";
  return `${API_BASE}/reports/${encodeURIComponent(id)}/figures/${encodeURIComponent(filename)}${params}`;
}

export function logoUrl(universityId: string) {
  return `${API_BASE}/universities/${encodeURIComponent(universityId)}/logo`;
}

export interface GenerateRequest {
  profile: StudentProfile;
  lab: LabDetails;
  manual_text: string;
  tasks?: LabTask[];
  semester?: string;
  submission_date: string;
}

export type GenerateEvent =
  | { type: "stage"; stage: GenerationStage; attempt?: number }
  | { type: "tokens"; count: number }
  | { type: "retry"; attempt: number; reason: string }
  | { type: "done"; record: ReportRecord }
  | { type: "error"; code: string; message: string }
  | { type: "cancelled" };

/** POST /generate and parse its server-sent events until done, error or abort. */
export async function streamGenerate(
  body: GenerateRequest,
  onEvent: (event: GenerateEvent) => void,
  signal: AbortSignal,
): Promise<void> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}/generate`, { method: "POST", signal, ...json(body) });
  } catch (error) {
    if (signal.aborted) return onEvent({ type: "cancelled" });
    void error;
    return onEvent({ type: "error", code: "backend_unreachable", message: "The EzLab server isn't running." });
  }
  if (!response.ok || !response.body) {
    if (response.status === 409) {
      return onEvent({
        type: "error",
        code: "busy",
        message: "Another report is still being generated.",
      });
    }
    let message = `Generation failed (${response.status}).`;
    try {
      const detail = await response.json();
      if (typeof detail?.detail === "string") message = detail.detail;
      else if (Array.isArray(detail?.detail) && detail.detail[0]?.msg) {
        const first = detail.detail[0];
        const where = Array.isArray(first.loc) ? first.loc.filter((x: unknown) => x !== "body").join(".") : "";
        message = where ? `${where}: ${first.msg}` : first.msg;
      }
    } catch {
      /* keep status fallback */
    }
    return onEvent({ type: "error", code: "http_error", message });
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let boundary: number;
      while ((boundary = buffer.indexOf("\n\n")) !== -1) {
        const chunk = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);
        let event = "message";
        let data = "";
        for (const line of chunk.split("\n")) {
          if (line.startsWith("event:")) event = line.slice(6).trim();
          else if (line.startsWith("data:")) data += line.slice(5).trim();
        }
        if (!data) continue;
        onEvent({ type: event, ...JSON.parse(data) } as GenerateEvent);
      }
    }
  } catch {
    if (signal.aborted) onEvent({ type: "cancelled" });
    else onEvent({ type: "error", code: "stream_broken", message: "Lost connection to the EzLab server." });
  }
}
