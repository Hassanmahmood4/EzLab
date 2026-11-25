/** Legacy UI helpers still import these; task reports do not use anomaly audit. */
export type AnomalyStatus = "ok" | "warning" | "error";
export type TraceStatus = "text" | "grounded" | "normalised" | "derived" | "ungrounded";

export interface CoverPage {
  university_id: string;
  university_raw: string;
  department: string;
  course_code: string;
  course_title: string;
  lab_number: string;
  experiment_title: string;
  student_name: string;
  registration_no: string;
  section: string;
  instructor: string;
  submission_date: string;
  semester?: string;
}

export interface LabTask {
  number: number;
  title: string;
  prompt: string;
  code: string;
  output: string;
  /** PNG filenames under /reports/{id}/figures/{name} */
  figures?: string[];
}

/** Unused by the task-report path; kept so older UI helpers still typecheck. */
export interface ReportTable {
  caption: string;
  headers: string[];
  rows: string[][];
}
export interface CellTrace {
  status: TraceStatus;
  line: number | null;
}
export interface FlagDetail {
  text: string;
  table: number | null;
  row: number | null;
  from: string | null;
  to: string | null;
}

export interface LabReport {
  cover_page: CoverPage;
  tasks: LabTask[];
}

export interface GenerationStats {
  tokens: number;
  seconds: number;
  tokens_per_second: number;
  peak_rss_gb: number;
  format_only?: boolean;
}

export interface LabDetails {
  course_code: string;
  course_title: string;
  lab_number: string;
  experiment_title: string;
  department: string;
}

export interface ReportRecord {
  id: string;
  created_at: string;
  updated_at: string;
  report: LabReport;
  raw_log: string;
  inputs: {
    profile: {
      name: string;
      registration_no: string;
      section: string;
      university: string;
      instructor: string;
      date: string;
    };
    lab: LabDetails;
    university_id: string | null;
    semester?: string;
    raw_log_name?: string | null;
  };
  stats: GenerationStats;
  trace: unknown[];
  trace_summary: {
    grounded: number;
    normalised: number;
    derived: number;
    ungrounded: number;
    total: number;
  };
  flags: unknown[];
  files: { docx: boolean; pdf: boolean; plot: boolean; preview?: boolean };
  render_errors: Partial<Record<"pdf" | "docx" | "plot" | "preview", string>>;
}

export interface ReportSummary {
  id: string;
  created_at: string;
  updated_at: string;
  course_code: string;
  course_title: string;
  lab_number: string;
  experiment_title: string;
  task_count: number;
  files: { docx?: boolean; pdf?: boolean; plot?: boolean; preview?: boolean };
}

export interface StudentProfile {
  name: string;
  registration_no: string;
  section: string;
  university_id: string;
  university_label: string;
  instructor: string;
  department: string;
}

export interface University {
  id: string;
  full_name: string;
  logo_url: string;
}

export interface Preset {
  id: string;
  label: string;
  university_id: string;
  profile: {
    name: string;
    registration_no: string;
    section: string;
    university: string;
    instructor: string;
    date: string;
  };
  lab: LabDetails;
  semester?: string;
  manual_text?: string;
  tasks: LabTask[];
}

export interface Health {
  status: "ok";
  local: boolean;
  platform: string;
  model: {
    file: string;
    path: string;
    found: boolean;
    loaded: boolean;
    busy: boolean;
    stub: boolean;
    runtime_installed: boolean;
  };
  typst: { found: boolean };
  memory: { rss_gb: number };
}

export type GenerationStage = "reading" | "writing" | "validating" | "rendering";

export interface ApiError {
  code: string;
  message: string;
}

export type EditableCoverField = Exclude<keyof CoverPage, "university_id" | "university_raw">;

export interface ReportEdits {
  cover: Partial<Record<EditableCoverField, string>>;
  tasks?: LabTask[];
}
