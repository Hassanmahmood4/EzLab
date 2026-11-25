"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ApiRequestError, api, streamGenerate } from "./api";
import { useSystem } from "./system-context";
import type {
  ApiError,
  EditableCoverField,
  GenerationStage,
  LabDetails,
  LabTask,
  Preset,
  ReportEdits,
  ReportRecord,
  StudentProfile,
} from "./types";

export const STAGES: { id: GenerationStage; label: string }[] = [
  { id: "reading", label: "Reading tasks" },
  { id: "writing", label: "Building report" },
  { id: "validating", label: "Checking" },
  { id: "rendering", label: "Rendering files" },
];

const MANUAL_EXTENSIONS = [".txt", ".md", ".pdf", ".docx"];
const LAB_STORAGE_KEY = "ezlab.lab";

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

export interface Progress {
  stage: GenerationStage;
  startedAt: number;
  stageStarts: Partial<Record<GenerationStage, number>>;
  tokens: number;
  retried: boolean;
}

export type FieldErrors = Partial<
  Record<keyof LabDetails | keyof StudentProfile | "manual" | "tasks", string>
>;

const hasExtension = (name: string, allowed: string[]) =>
  allowed.some((ext) => name.toLowerCase().endsWith(ext));
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

function validateManual(manual: { name: string; text: string } | null): FieldErrors {
  if (!manual?.text?.trim() || manual.text.trim().length < 20) {
    return { manual: "Upload a lab manual (PDF, Word, or text)." };
  }
  return {};
}

export function useWorkspace() {
  const { profile: savedProfile, saveProfile, setLastStats, refreshHealth, connection } = useSystem();
  const [presets, setPresets] = useState<Preset[]>([]);

  const [profileDraft, setProfileDraft] = useState<StudentProfile>(EMPTY_PROFILE);
  const [lab, setLab] = useState<LabDetails>(EMPTY_LAB);
  const [semester, setSemester] = useState("");
  const [manual, setManual] = useState<{ name: string; text: string } | null>(null);
  const [manualLoading, setManualLoading] = useState(false);
  const [tasks, setTasks] = useState<LabTask[]>([]);
  const [errors, setErrors] = useState<FieldErrors>({});

  const [phase, setPhase] = useState<Phase>("idle");
  const [progress, setProgress] = useState<Progress | null>(null);
  const [record, setRecord] = useState<ReportRecord | null>(null);
  const [failure, setFailure] = useState<ApiError | null>(null);

  const [edits, setEdits] = useState<ReportEdits>({ cover: {} });
  const [updating, setUpdating] = useState(false);
  const [updateError, setUpdateError] = useState<string | null>(null);

  const abortRef = useRef<AbortController | null>(null);
  const draftIsSampleRef = useRef(false);

  const presetsLoaded = presets.length > 0;
  useEffect(() => {
    if (connection !== "connected" || presetsLoaded) return;
    api.presets().then(setPresets).catch(() => undefined);
  }, [connection, presetsLoaded]);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(LAB_STORAGE_KEY);
      if (stored) setLab({ ...EMPTY_LAB, ...JSON.parse(stored) });
    } catch {
      /* ignore */
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

  const updateTask = useCallback((index: number, patch: Partial<LabTask>) => {
    setTasks((current) => current.map((task, i) => (i === index ? { ...task, ...patch } : task)));
    setErrors((e) => ({ ...e, tasks: undefined }));
  }, []);

  const addTask = useCallback(() => {
    setTasks((current) => {
      const number = (current[current.length - 1]?.number ?? 0) + 1;
      return [...current, { number, title: `Task ${number}`, prompt: "", code: "", output: "" }];
    });
    setErrors((e) => ({ ...e, tasks: undefined }));
  }, []);

  const removeTask = useCallback((index: number) => {
    setTasks((current) => current.filter((_, i) => i !== index));
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
        // Always take a fresh title from the new manual when the parser found one;
        // clears stale titles left over from a previous sample/preset.
        if (parsed.fields.experiment_title) {
          next.experiment_title = parsed.fields.experiment_title;
        }
        return next;
      });
      setTasks(
        (parsed.tasks ?? []).map((t) => ({
          number: t.number,
          title: t.title,
          prompt: t.prompt,
          code: t.code || "",
          output: t.output || "",
        })),
      );
      setErrors((e) => ({ ...e, manual: undefined, tasks: undefined }));
    } catch (error) {
      setErrors((e) => ({
        ...e,
        manual: error instanceof Error ? error.message : "Couldn't read this manual.",
      }));
    } finally {
      setManualLoading(false);
    }
  }, []);

  const loadPreset = useCallback(
    (preset: Preset) => {
      setLab(preset.lab);
      setSemester(preset.semester || "");
      setManual(
        preset.manual_text
          ? { name: `${preset.id}.txt`, text: preset.manual_text }
          : null,
      );
      setTasks((preset.tasks ?? []).map((t) => ({ ...t, code: t.code || "", output: t.output || "" })));
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
      ...validateManual(manual),
    };
    if (Object.values(nextErrors).some(Boolean)) {
      setErrors(nextErrors);
      return;
    }

    if (!savedProfile && !draftIsSampleRef.current) {
      try {
        await saveProfile(profileDraft);
      } catch (error) {
        setFailure({
          code: "profile_save",
          message: error instanceof Error ? error.message : "Couldn't save your profile.",
        });
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
    setEdits({ cover: {} });
    setProgress({
      stage: "reading",
      startedAt,
      stageStarts: { reading: startedAt },
      tokens: 0,
      retried: false,
    });

    await streamGenerate(
      {
        profile,
        lab,
        manual_text: manual!.text,
        tasks,
        semester,
        submission_date: today(),
      },
      (event) => {
        switch (event.type) {
          case "stage":
            setProgress((p) =>
              p && {
                ...p,
                stage: event.stage,
                stageStarts: {
                  ...p.stageStarts,
                  [event.stage]: p.stageStarts[event.stage] ?? performance.now(),
                },
              },
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
  }, [savedProfile, profileDraft, lab, manual, tasks, semester, saveProfile, setLastStats, refreshHealth]);

  const cancel = useCallback(() => abortRef.current?.abort(), []);

  const openReport = useCallback(async (id: string) => {
    try {
      const loaded = await api.report(id);
      setRecord(loaded);
      setLab(loaded.inputs.lab);
      setSemester(loaded.inputs.semester || "");
      setTasks(loaded.report.tasks.map((t) => ({ ...t })));
      setEdits({ cover: {} });
      setPhase("ready");
      setFailure(null);
    } catch {
      setFailure({
        code: "not_found",
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

  const isStale = Object.keys(edits.cover).length > 0;

  const applyEdits = useCallback(async () => {
    if (!record || !isStale) return false;
    setUpdating(true);
    setUpdateError(null);
    try {
      const updated = await api.editReport(record.id, edits);
      setRecord(updated);
      setEdits({ cover: {} });
      return true;
    } catch (error) {
      setUpdateError(error instanceof Error ? error.message : "Couldn't update the files.");
      return false;
    } finally {
      setUpdating(false);
    }
  }, [record, edits, isStale]);

  const discardEdits = useCallback(() => {
    setEdits({ cover: {} });
    setUpdateError(null);
  }, []);

  const startNew = useCallback(() => {
    setRecord(null);
    setPhase("idle");
    setProgress(null);
    setFailure(null);
    setManual(null);
    setTasks([]);
    setEdits({ cover: {} });
    setLab((current) => ({ ...current, lab_number: "", experiment_title: "" }));
    window.history.replaceState(null, "", "/");
  }, []);

  const viewReport = useMemo(() => {
    if (!record) return null;
    return {
      ...record.report,
      cover_page: { ...record.report.cover_page, ...edits.cover },
    };
  }, [record, edits]);

  return {
    presets,
    profileDraft,
    updateProfileDraft,
    lab,
    updateLab,
    semester,
    setSemester,
    manual,
    manualLoading,
    loadManual,
    clearManual: () => setManual(null),
    tasks,
    updateTask,
    addTask,
    removeTask,
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
    isStale,
    applyEdits,
    discardEdits,
    updating,
    updateError,
  };
}

export type Workspace = ReturnType<typeof useWorkspace>;
