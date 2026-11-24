import { useId } from "react";

const CONTROL =
  "w-full rounded-md border border-rule-strong bg-sheet px-3 text-sm text-ink placeholder:text-mute/70 transition-[border-color,box-shadow] duration-150 hover:border-mute/60 focus:border-navy focus:outline-none focus:ring-2 focus:ring-navy/15 disabled:bg-well disabled:text-mute aria-[invalid=true]:border-error";

interface FieldShellProps {
  label: string;
  hint?: string;
  error?: string | null;
  optional?: boolean;
  children: (props: { id: string; describedBy?: string; invalid: boolean }) => React.ReactNode;
  className?: string;
}

export function FieldShell({ label, hint, error, optional, children, className = "" }: FieldShellProps) {
  const id = useId();
  const hintId = `${id}-hint`;
  const errorId = `${id}-error`;
  const describedBy = [hint ? hintId : null, error ? errorId : null].filter(Boolean).join(" ") || undefined;

  return (
    <div className={className}>
      <label htmlFor={id} className="mb-1.5 flex items-baseline justify-between text-[0.8125rem] font-semibold text-body">
        {label}
        {optional && <span className="text-xs font-normal text-mute">Optional</span>}
      </label>
      {children({ id, describedBy, invalid: Boolean(error) })}
      {hint && !error && (
        <p id={hintId} className="mt-1 text-xs text-mute">
          {hint}
        </p>
      )}
      {error && (
        <p id={errorId} role="alert" className="mt-1 text-xs font-medium text-error">
          {error}
        </p>
      )}
    </div>
  );
}

type InputProps = Omit<React.InputHTMLAttributes<HTMLInputElement>, "id"> & {
  label: string;
  hint?: string;
  error?: string | null;
  optional?: boolean;
  wrapperClassName?: string;
};

export function TextField({ label, hint, error, optional, wrapperClassName, className = "", ...props }: InputProps) {
  return (
    <FieldShell label={label} hint={hint} error={error} optional={optional} className={wrapperClassName}>
      {({ id, describedBy, invalid }) => (
        <input
          id={id}
          aria-describedby={describedBy}
          aria-invalid={invalid}
          className={`${CONTROL} h-10 ${className}`}
          {...props}
        />
      )}
    </FieldShell>
  );
}

type SelectProps = Omit<React.SelectHTMLAttributes<HTMLSelectElement>, "id"> & {
  label: string;
  hint?: string;
  error?: string | null;
  wrapperClassName?: string;
};

export function SelectField({ label, hint, error, wrapperClassName, className = "", children, ...props }: SelectProps) {
  return (
    <FieldShell label={label} hint={hint} error={error} className={wrapperClassName}>
      {({ id, describedBy, invalid }) => (
        <select
          id={id}
          aria-describedby={describedBy}
          aria-invalid={invalid}
          className={`${CONTROL} h-10 appearance-none bg-[url('data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%2212%22 height=%2212%22 viewBox=%220 0 12 12%22><path d=%22M2.5 4.5 6 8l3.5-3.5%22 fill=%22none%22 stroke=%22%23646b7c%22 stroke-width=%221.5%22/></svg>')] bg-[length:12px] bg-[right_0.75rem_center] bg-no-repeat pr-9 ${className}`}
          {...props}
        >
          {children}
        </select>
      )}
    </FieldShell>
  );
}

type TextAreaProps = Omit<React.TextareaHTMLAttributes<HTMLTextAreaElement>, "id"> & {
  label: string;
  hint?: string;
  error?: string | null;
  optional?: boolean;
  wrapperClassName?: string;
};

export function TextAreaField({ label, hint, error, optional, wrapperClassName, className = "", ...props }: TextAreaProps) {
  return (
    <FieldShell label={label} hint={hint} error={error} optional={optional} className={wrapperClassName}>
      {({ id, describedBy, invalid }) => (
        <textarea
          id={id}
          aria-describedby={describedBy}
          aria-invalid={invalid}
          className={`${CONTROL} min-h-24 resize-y py-2 leading-relaxed ${className}`}
          {...props}
        />
      )}
    </FieldShell>
  );
}
