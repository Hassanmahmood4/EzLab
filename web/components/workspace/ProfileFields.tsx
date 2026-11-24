"use client";

import { SelectField, TextField } from "@/components/ui/Field";
import type { FieldErrors } from "@/lib/useWorkspace";
import type { StudentProfile, University } from "@/lib/types";

interface Props {
  value: StudentProfile;
  onChange: (field: keyof StudentProfile, value: string) => void;
  universities: University[];
  errors?: FieldErrors;
  compact?: boolean;
}

/** Shared profile form used on first run (workspace) and on the Profile page. */
export function ProfileFields({ value, onChange, universities, errors = {}, compact = false }: Props) {
  const grid = compact ? "grid gap-3" : "grid gap-4 sm:grid-cols-2";
  return (
    <div className={grid}>
      <TextField
        label="Full name"
        autoComplete="name"
        value={value.name}
        onChange={(e) => onChange("name", e.target.value)}
        error={errors.name}
        wrapperClassName={compact ? "" : "sm:col-span-2"}
      />
      <TextField
        label="Registration no."
        placeholder="21I-1234"
        value={value.registration_no}
        onChange={(e) => onChange("registration_no", e.target.value)}
        error={errors.registration_no}
      />
      <TextField
        label="Section"
        placeholder="BCS-4A"
        optional
        value={value.section}
        onChange={(e) => onChange("section", e.target.value)}
      />
      <SelectField
        label="University"
        value={value.university_id}
        onChange={(e) => onChange("university_id", e.target.value)}
        error={errors.university_id}
        wrapperClassName={compact ? "" : "sm:col-span-2"}
      >
        <option value="" disabled>
          {universities.length ? "Choose your university" : "Loading universities…"}
        </option>
        {universities.map((u) => (
          <option key={u.id} value={u.id}>
            {u.full_name}
          </option>
        ))}
      </SelectField>
      <TextField
        label="Campus as you write it"
        placeholder="FAST-NU Isb"
        optional
        hint="Printed under your university name if different."
        value={value.university_label}
        onChange={(e) => onChange("university_label", e.target.value)}
      />
      <TextField
        label="Lab instructor"
        placeholder="Dr. Ayesha Khan"
        optional
        value={value.instructor}
        onChange={(e) => onChange("instructor", e.target.value)}
      />
      {!compact && (
        <TextField
          label="Default department"
          placeholder="Department of Computer Science"
          optional
          value={value.department}
          onChange={(e) => onChange("department", e.target.value)}
          wrapperClassName="sm:col-span-2"
        />
      )}
    </div>
  );
}
