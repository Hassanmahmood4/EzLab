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
}

export interface ReportTable {
  caption: string;
  headers: string[];
  rows: string[][];
}

export interface ReportBody {
  abstract: string;
  apparatus: string[];
  methodology: string;
  equations_latex: string[];
  tables: ReportTable[];
  plot_code: string;
  discussion: string;
  conclusion: string;
}

export interface LabReport {
  cover_page: CoverPage;
  anomaly_check: { status: AnomalyStatus; flags: string[] };
  report_body: ReportBody;
}

export interface CellTrace {
  status: TraceStatus;
  line: number | null;
}

export interface TraceSummary {
  grounded: number;
  normalised: number;
  derived: number;
  ungrounded: number;
  total: number;
}

export interface FlagDetail {
  text: string;
  table: number | null;
  row: number | null;
  from: string | null;
  to: string | null;
}

export interface GenerationStats {
  tokens: number;
  seconds: number;
  tokens_per_second: number;
  peak_rss_gb: number;
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
    raw_log_name?: string | null;
  };
  stats: GenerationStats;
  trace: CellTrace[][][];
  trace_summary: TraceSummary;
  flags: FlagDetail[];
  files: { docx: boolean; pdf: boolean; plot: boolean };
  render_errors: Partial<Record<"pdf" | "docx" | "plot", string>>;
}

export interface ReportSummary {
  id: string;
  created_at: string;
  updated_at: string;
  course_code: string;
  course_title: string;
  lab_number: string;
  experiment_title: string;
  anomaly_status: AnomalyStatus;
  files: { docx?: boolean; pdf?: boolean; plot?: boolean };
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
  raw_log: string;
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
export type EditableBodyField = "abstract" | "apparatus" | "methodology" | "discussion" | "conclusion";

export interface ReportEdits {
  cover: Partial<Record<EditableCoverField, string>>;
  body: Partial<Record<EditableBodyField, string | string[]>>;
}
