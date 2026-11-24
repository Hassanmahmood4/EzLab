"use client";

import { useMemo, useState } from "react";
import { Button } from "@/components/ui/Button";
import { CheckMark, CrossMark } from "@/components/ui/Marks";
import { useToast } from "@/components/ui/Toast";
import { ProfileFields } from "@/components/workspace/ProfileFields";
import { useSystem } from "@/lib/system-context";
import type { StudentProfile } from "@/lib/types";
import { EMPTY_PROFILE, validateProfile, type FieldErrors } from "@/lib/useWorkspace";

export default function ProfilePage() {
  const { profile, profileLoaded } = useSystem();

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="mx-auto grid max-w-6xl gap-10 px-5 py-8 sm:px-8 lg:grid-cols-[minmax(0,1fr)_22rem]">
        <section aria-labelledby="profile-head">
          <h1 id="profile-head" className="text-[1.375rem] font-bold tracking-tight text-ink">
            Profile
          </h1>
          <p className="mt-1 text-sm text-mute">
            These details fill every cover page. Change them once a semester, not every week.
          </p>
          {profileLoaded ? (
            <ProfileForm key={JSON.stringify(profile)} profile={profile} />
          ) : (
            <div className="mt-6 h-80 animate-pulse rounded-md bg-well" />
          )}
        </section>

        <aside className="space-y-8">
          <SystemStatus />
          <section aria-labelledby="data-head">
            <div className="journal-head">
              <h2 id="data-head">Your data</h2>
            </div>
            <ul className="space-y-2 text-sm text-body">
              <li>Your profile and reports are stored in the project&apos;s <code className="font-mono text-[0.8125rem]">outputs/</code> folder.</li>
              <li>Nothing is uploaded. LabPulse makes no internet requests.</li>
              <li>Delete any report from History at any time.</li>
              <li className="text-mute">University crests are placeholders, not official artwork.</li>
            </ul>
          </section>
        </aside>
      </div>
    </div>
  );
}

function ProfileForm({ profile }: { profile: StudentProfile | null }) {
  const { universities, saveProfile } = useSystem();
  const notify = useToast();
  const [draft, setDraft] = useState<StudentProfile>(profile ?? EMPTY_PROFILE);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const dirty = useMemo(() => JSON.stringify(draft) !== JSON.stringify(profile ?? EMPTY_PROFILE), [draft, profile]);

  const onSave = async (event: React.FormEvent) => {
    event.preventDefault();
    const nextErrors = validateProfile(draft);
    setErrors(nextErrors);
    if (Object.values(nextErrors).some(Boolean)) return;
    setSaving(true);
    setSaveError(null);
    try {
      await saveProfile(draft);
      notify("Profile saved on this laptop");
    } catch (e) {
      setSaveError(e instanceof Error ? e.message : "Couldn't save your profile.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={onSave} className="mt-6 rounded-md border border-rule bg-sheet p-5 shadow-sheet sm:p-6">
      <ProfileFields
        value={draft}
        onChange={(field, value) => {
          setDraft((d) => ({ ...d, [field]: value }));
          setErrors((e) => ({ ...e, [field]: undefined }));
        }}
        universities={universities}
        errors={errors}
      />
      {saveError && (
        <p role="alert" className="mt-4 text-sm font-medium text-error">
          {saveError}
        </p>
      )}
      <div className="mt-6 flex items-center gap-3 border-t border-rule pt-5">
        <Button type="submit" loading={saving} disabled={!dirty}>
          Save profile
        </Button>
        {dirty && profile && (
          <Button type="button" variant="quiet" onClick={() => setDraft(profile)}>
            Undo changes
          </Button>
        )}
        {!dirty && profile && <span className="text-sm text-mute">All changes saved</span>}
      </div>
    </form>
  );
}

function SystemStatus() {
  const { health, connection, refreshHealth } = useSystem();
  const [checking, setChecking] = useState(false);

  const checks = health
    ? [
        {
          ok: health.model.found || health.model.stub,
          label: health.model.stub ? "Sample mode (no model)" : "Model file",
          detail: health.model.stub
            ? "Generation replays the built-in samples. Unset LABPULSE_STUB to use the model."
            : health.model.found
              ? health.model.path
              : `Place ${health.model.file} at ${health.model.path}`,
        },
        {
          ok: health.model.runtime_installed || health.model.stub,
          label: "llama.cpp runtime",
          detail: health.model.runtime_installed ? "llama-cpp-python installed" : "Run: pip install llama-cpp-python",
        },
        {
          ok: health.typst.found,
          label: "PDF renderer (Typst)",
          detail: health.typst.found ? "Ready" : "Install Typst or place the binary at bin/typst. Word export still works.",
        },
      ]
    : [];

  return (
    <section id="system" aria-labelledby="system-head" className="scroll-mt-20">
      <div className="journal-head">
        <h2 id="system-head">System</h2>
        <button
          type="button"
          onClick={async () => {
            setChecking(true);
            await refreshHealth();
            setChecking(false);
          }}
          className="text-xs font-semibold text-navy hover:underline disabled:opacity-50"
          disabled={checking}
        >
          {checking ? "Checking…" : "Check again"}
        </button>
      </div>
      {connection === "unreachable" ? (
        <div className="rounded-md border border-warn-rule bg-warn-tint p-4 text-sm">
          <p className="font-semibold text-ink">Local server not running</p>
          <p className="mt-1 text-body">From the project folder, run:</p>
          <code className="mt-2 block rounded bg-sheet px-2.5 py-1.5 font-mono text-[0.8125rem]">make demo</code>
        </div>
      ) : (
        <ul className="divide-y divide-rule rounded-md border border-rule bg-sheet shadow-sheet">
          <li className="flex gap-3 px-4 py-3">
            <StatusIcon ok={connection === "connected"} />
            <div>
              <p className="text-sm font-semibold text-ink">Running on this laptop</p>
              <p className="text-xs text-mute">
                Local server at 127.0.0.1{health ? ` · ${health.platform} · ${health.memory.rss_gb.toFixed(1)} GB in use` : ""}
              </p>
            </div>
          </li>
          {checks.map((check) => (
            <li key={check.label} className="flex gap-3 px-4 py-3">
              <StatusIcon ok={check.ok} />
              <div className="min-w-0">
                <p className="text-sm font-semibold text-ink">{check.label}</p>
                <p className="break-words text-xs text-mute">{check.detail}</p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function StatusIcon({ ok }: { ok: boolean }) {
  return (
    <span
      className={`mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full ${ok ? "bg-navy-tint text-navy" : "bg-error-tint text-error"}`}
    >
      {ok ? <CheckMark /> : <CrossMark />}
      <span className="sr-only">{ok ? "OK" : "Needs attention"}</span>
    </span>
  );
}
