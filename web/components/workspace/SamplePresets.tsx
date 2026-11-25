import type { Preset } from "@/lib/types";

interface Props {
  presets: Preset[];
  onPick: (preset: Preset) => void;
  label: string;
  disabled?: boolean;
}

/** One-click sample labs, for trying EzLab without a manual of your own. */
export function SamplePresets({ presets, onPick, label, disabled }: Props) {
  if (presets.length === 0) return null;
  return (
    <div>
      <p className="mb-1.5 text-xs text-mute">{label}</p>
      <div className="flex flex-wrap gap-1.5">
        {presets.map((preset) => (
          <button
            key={preset.id}
            type="button"
            disabled={disabled}
            onClick={() => onPick(preset)}
            className="rounded-full border border-rule-strong bg-sheet px-2.5 py-1 text-xs font-medium text-body transition-colors hover:border-navy hover:text-navy disabled:pointer-events-none disabled:opacity-50"
          >
            {preset.label}
          </button>
        ))}
      </div>
    </div>
  );
}
