"use client";
import { Brand } from "./Brand";

const STEPS: { key: Step; label: string }[] = [
  { key: "why", label: "the why" },
  { key: "you", label: "you" },
  { key: "voice", label: "your voice" },
];

export type Step = "why" | "you" | "voice";

export function OnboardingTop({ active, pct }: { active: Step; pct: number }) {
  return (
    <header className="pt-7">
      <div className="wrap flex items-center justify-between gap-6">
        <Brand />
        <div className="flex items-center gap-5">
          <div className="hidden sm:flex items-center gap-2.5 text-[13px] font-medium text-[var(--muted)]">
            {STEPS.map((s, i) => (
              <span key={s.key} className="flex items-center gap-2.5">
                <span style={{ color: s.key === active ? "var(--ink)" : undefined }}>
                  {s.label}
                </span>
                {i < STEPS.length - 1 && <span className="opacity-40">·</span>}
              </span>
            ))}
          </div>
          <div className="flex items-center gap-2.5 text-[12.5px] text-[var(--muted)] font-medium">
            <span className="hidden sm:inline">voice tuned</span>
            <span className="meter">
              <i style={{ width: `${Math.round(pct)}%` }} />
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
