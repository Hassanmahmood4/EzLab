"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ApiRequestError, api, streamGenerate } from "./api";
import { useSystem } from "./system-context";
import type {
  ApiError,
  EditableBodyField,
  EditableCoverField,
  GenerationStage,
  LabDetails,
  Preset,
  ReportEdits,
  ReportRecord,
  StudentProfile,
} from "./types";

export const STAGES: { id: GenerationStage; label: string }[] = [
  { id: "reading", label: "Reading lab" },
  { id: "writing", label: "Writing report" },
  { id: "validating", label: "Validating" },
  { id: "rendering", label: "Rendering files" },
];

const DATA_EXTENSIONS = [".csv", ".log", ".txt", ".tsv"];
const MANUAL_EXTENSIONS = [".txt", ".md", ".pdf", ".docx"];
const MAX_DATA_BYTES = 1024 * 1024;
const LAB_STORAGE_KEY = "labpulse.lab";

export const EMPTY_LAB: LabDetails = {
  course_code: "",
  course_title: "",
  lab_number: "",
  experiment_title: "",
  department: "",
};

export const EMPTY_PROFILE: StudentProfile = {
  name: "",
  registration_no: "",
  section: "",
  university_id: "",
  university_label: "",
  instructor: "",
  department: "",
};

export type Phase = "idle" | "generating" | "ready" | "failed";

export interface DataFile {
  name: string;
  text: string;
  size: number;
}

export interface Progress {
  stage: GenerationStage;
  startedAt: number;
  stageStarts: Partial<Record<GenerationStage, number>>;
  tokens: number;
  retried: boolean;
}

export type FieldErrors = Partial<Record<keyof LabDetails | keyof StudentProfile | "data" | "manual", string>>;

const hasExtension = (name: string, allowed: string[]) => allowed.some((ext) => name.toLowerCase().endsWith(ext));
const today = () => new Date().toISOString().slice(0, 10);

export function validateProfile(profile: StudentProfile): FieldErrors {
  const errors: FieldErrors = {};
  if (!profile.name.trim()) errors.name = "Enter your name as it should appear on the cover.";
  if (!profile.registration_no.trim()) errors.registration_no = "Enter your registration number.";
  if (!profile.university_id) errors.university_id = "Choose your university.";
  return errors;
}

function validateLab(lab: LabDetails): FieldErrors {
  const errors: FieldErrors = {};
  if (!lab.course_code.trim()) errors.course_code = "Required";
  if (!lab.course_title.trim()) errors.course_title = "Required";
  if (!lab.lab_number.trim()) errors.lab_number = "Required";
  if (!lab.experiment_title.trim()) errors.experiment_title = "Enter the experiment title from your manual.";
  if (!lab.department.trim()) errors.department = "Required";
  return errors;
}

export function useWorkspace() {
  const { profile: savedProfile, saveProfile, setLastStats, refreshHealth, connection } = useSystem();
  const [presets, setPresets] = useState<Preset[]>([]);

  const [profileDraft, setProfileDraft] = useState<StudentProfile>(EMPTY_PROFILE);
  const [lab, setLab] = useState<LabDetails>(EMPTY_LAB);
  const [manual, setManual] = useState<{ name: string; text: string } | null>(null);
  const [manualLoading, setManualLoading] = useState(false);
  const [data, setData] = useState<DataFile | null>(null);
  const [errors, setErrors] = useState<FieldErrors>({});

  const [phase, setPhase] = useState<Phase>("idle");
  const [progress, setProgress] = useState<Progress | null>(null);
  const [record, setRecord] = useState<ReportRecord | null>(null);
  const [failure, setFailure] = useState<ApiError | null>(null);

  const [edits, setEdits] = useState<ReportEdits>({ cover: {}, body: {} });
  const [updating, setUpdating] = useState(false);
  const [updateError, setUpdateError] = useState<string | null>(null);
  const [hoveredLine, setHoveredLine] = useState<number | null>(null);

  const abortRef = useRef<AbortController | null>(null);
  // A sample's student fills the form for a trial run but is never saved as the real profile.
  const draftIsSampleRef = useRef(false);

  const presetsLoaded = presets.length > 0;
  useEffect(() => {
    if (connection !== "connected" || presetsLoaded) return;
    api.presets().then(setPresets).catch(() => undefined);
  }, [connection, presetsLoaded]);

  // Restore last week's course details so only the lab number and title change.
  useEffect(() => {
    try {
      const stored = localStorage.getItem(LAB_STORAGE_KEY);
      if (stored) setLab({ ...EMPTY_LAB, ...JSON.parse(stored) });
    } catch {
      /* ignore corrupt storage */
    }
  }, []);

  const updateLab = useCallback((field: keyof LabDetails, value: string) => {
    setLab((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: undefined }));
  }, []);

  const updateProfileDraft = useCallback((field: keyof StudentProfile, value: string) => {
    draftIsSampleRef.current = false;
    setProfileDraft((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: undefined }));
  }, []);

  const loadData = useCallback(async (file: File) => {
    if (!hasExtension(file.name, DATA_EXTENSIONS)) {
      setErrors((e) => ({ ...e, data: "Use a .csv, .log, .tsv or .txt file." }));
      return;
    }
    if (file.size > MAX_DATA_BYTES) {
      setErrors((e) => ({ ...e, data: "This file is over 1 MB. Keep only the readings for this lab." }));
      return;
    }
    const text = await file.text();
    if (!text.trim()) {
      setErrors((e) => ({ ...e, data: "This file is empty." }));
      return;
    }
    if ((text.match(/-?\d+(?:\.\d+)?/g) ?? []).length < 3) {
      setErrors((e) => ({ ...e, data: "No numeric readings found in this file." }));
      return;
    }
    setData({ name: file.name, text, size: file.size });
    setErrors((e) => ({ ...e, data: undefined }));
  }, []);

  const loadManual = useCallback(async (file: File) => {
    if (!hasExtension(file.name, MANUAL_EXTENSIONS)) {
      setErrors((e) => ({ ...e, manual: "Use a .pdf, .docx, .txt or .md manual." }));
      return;
    }
    setManualLoading(true);
    try {
      const parsed = await api.parseManual(file);
      setManual({ name: file.name, text: parsed.text });
      setLab((current) => {
        const next = { ...current };
        for (const key of Object.keys(parsed.fields) as (keyof LabDetails)[]) {
          if (parsed.fields[key]) next[key] = parsed.fields[key];
        }
        return next;
      });
      setErrors((e) => ({ ...e, manual: undefined }));
    } catch (error) {
      setErrors((e) => ({ ...e, manual: error instanceof Error ? error.message : "Couldn't read this manual." }));
    } finally {
      setManualLoading(false);
    }
  }, []);

    const loadPreset = useCallback(
    (preset: Preset) => {
      setLab(preset.lab);
      setData(null);
      setManual(null);
      setErrors({});
      if (!savedProfile) {
        draftIsSampleRef.current = true;
        setProfileDraft({
          name: preset.profile.name,
          registration_no: preset.profile.registration_no,
          section: preset.profile.section,
          university_id: preset.university_id,
          university_label: preset.profile.university,
          instructor: preset.profile.instructor,
          department: preset.lab.department,
        });
      }
    },
    [savedProfile],
  );

  const generate = useCallback(async () => {
    const profile = savedProfile ?? profileDraft;
    const nextErrors: FieldErrors = {
      ...(savedProfile ? {} : validateProfile(profileDraft)),
      ...validateLab(lab),
    };
    if (Object.values(nextErrors).some(Boolean)) {
      setErrors(nextErrors);
      return;
    }

    if (!savedProfile && !draftIsSampleRef.current) {
      try {
        await saveProfile(profileDraft);
      } catch (error) {
        setFailure({ code: "profile_save", message: error instanceof Error ? error.message : "Couldn't save your profile." });
        setPhase("failed");
        return;
      }
    }
    localStorage.setItem(LAB_STORAGE_KEY, JSON.stringify(lab));

    const controller = new AbortController();
    abortRef.current = controller;
    const startedAt = performance.now();
    setPhase("generating");
    setFailure(null);
    setRecord(null);
    setEdits({ cover: {}, body: {} });
    setProgress({ stage: "reading", startedAt, stageStarts: { reading: startedAt }, tokens: 0, retried: false });

    await streamGenerate(
      {
        profile,
        lab,
        raw_log: data?.text ?? "",
        raw_log_name: data?.name,
        manual_text: manual?.text,
        submission_date: today(),
      },
      (event) => {
        switch (event.type) {
          case "stage":
            setProgress((p) =>
              p && { ...p, stage: event.stage, stageStarts: { ...p.stageStarts, [event.stage]: p.stageStarts[event.stage] ?? performance.now() } },
            );
            break;
          case "tokens":
            setProgress((p) => p && { ...p, tokens: event.count });
            break;
          case "retry":
            setProgress((p) => p && { ...p, retried: true, tokens: 0 });
            break;
          case "done":
            setRecord(event.record);
            setPhase("ready");
            setLastStats({
              tokensPerSecond: event.record.stats.tokens_per_second,
              seconds: event.record.stats.seconds,
              peakRssGb: event.record.stats.peak_rss_gb,
            });
            window.history.replaceState(null, "", `/?report=${encodeURIComponent(event.record.id)}`);
            break;
          case "error":
            setFailure({ code: event.code, message: event.message });
            setPhase("failed");
            break;
          case "cancelled":
            setPhase("idle");
            setProgress(null);
            break;
        }
      },
      controller.signal,
    );
    abortRef.current = null;
    refreshHealth();
  }, [savedProfile, profileDraft, lab, data, manual, saveProfile, setLastStats, refreshHealth]);

  const cancel = useCallback(() => abortRef.current?.abort(), []);

  const openReport = useCallback(async (id: string) => {
    try {
      const loaded = await api.report(id);
      setRecord(loaded);
      setLab(loaded.inputs.lab);
      if (loaded.raw_log) {
        setData({ name: loaded.inputs.raw_log_name || "Saved measurements", text: loaded.raw_log, size: loaded.raw_log.length });
      } else {
        setData(null);
      }
      setEdits({ cover: {}, body: {} });
      setPhase("ready");
      setFailure(null);
    } catch (error) {
      setFailure({
        code: error instanceof ApiRequestError ? error.code : "not_found",
        message: "That report couldn't be opened. It may have been deleted.",
      });
      setPhase("failed");
    }
  }, []);

  const editCover = useCallback(
    (field: EditableCoverField, value: string) => {
      setEdits((current) => {
        const cover = { ...current.cover };
        if (record && record.report.cover_page[field] === value) delete cover[field];
        else cover[field] = value;
        return { ...current, cover };
      });
    },
    [record],
  );

  const editBody = useCallback(
    (field: EditableBodyField, value: string | string[]) => {
      setEdits((current) => {
        const body = { ...current.body };
        const original = record?.report.report_body[field];
        if (JSON.stringify(original) === JSON.stringify(value)) delete body[field];
        else body[field] = value;
        return { ...current, body };
      });
    },
    [record],
  );

  const isStale = Object.keys(edits.cover).length + Object.keys(edits.body).length > 0;

  const applyEdits = useCallback(async () => {
    if (!record || !isStale) return false;
    setUpdating(true);
    setUpdateError(null);
    try {
      const updated = await api.editReport(record.id, edits);
      setRecord(updated);
      setEdits({ cover: {}, body: {} });
      return true;
    } catch (error) {
      setUpdateError(error instanceof Error ? error.message : "Couldn't update the files.");
      return false;
    } finally {
      setUpdating(false);
    }
  }, [record, edits, isStale]);

  const discardEdits = useCallback(() => {
    setEdits({ cover: {}, body: {} });
    setUpdateError(null);
  }, []);

  const startNew = useCallback(() => {
    setRecord(null);
    setPhase("idle");
    setProgress(null);
    setFailure(null);
    setData(null);
    setManual(null);
    setEdits({ cover: {}, body: {} });
    setLab((current) => ({ ...current, lab_number: "", experiment_title: "" }));
    window.history.replaceState(null, "", "/");
  }, []);

  /** The report as the student currently sees it, with unsaved edits applied. */
  const viewReport = useMemo(() => {
    if (!record) return null;
    return {
      ...record.report,
      cover_page: { ...record.report.cover_page, ...edits.cover },
      report_body: { ...record.report.report_body, ...edits.body } as ReportRecord["report"]["report_body"],
    };
  }, [record, edits]);

  return {
    presets,
    profileDraft,
    updateProfileDraft,
    lab,
    updateLab,
    manual,
    manualLoading,
    loadManual,
    clearManual: () => setManual(null),
    data,
    loadData,
    clearData: () => setData(null),
    loadPreset,
    errors,
    phase,
    progress,
    record,
    viewReport,
    failure,
    generate,
    cancel,
    openReport,
    startNew,
    edits,
    editCover,
    editBody,
    isStale,
    applyEdits,
    discardEdits,
    updating,
    updateError,
    hoveredLine,
    setHoveredLine,
  };
}

export type Workspace = ReturnType<typeof useWorkspace>;
