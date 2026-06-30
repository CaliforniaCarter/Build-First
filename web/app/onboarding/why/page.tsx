"use client";
import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { OnboardingTop } from "@/components/OnboardingTop";
import { api } from "@/lib/api";
import { setName as persistName, startTimer } from "@/lib/onboarding-store";

const WHYS = [
  "i don't have time to write",
  "i stare at the blank page",
  "i do great work no one sees",
  "posting feels like a chore",
  "the creator cup is coming 👀",
];

export default function WhyPage() {
  const router = useRouter();
  const [picked, setPicked] = useState<Set<number>>(new Set());
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);

  const ready = name.trim().length > 0;
  // honest teaser: progress tied to real actions (name entered, whys picked)
  const pct = useMemo(
    () => (ready ? 20 : 0) + Math.min(picked.size, 3) * 5,
    [ready, picked]
  );

  const hint = ready
    ? `great, ${name.trim().toLowerCase()} — let's find your voice.`
    : picked.size
      ? "got it. now your name and we're off."
      : "takes about 8 minutes. you can change anything later.";

  function toggle(i: number) {
    setPicked((prev) => {
      const next = new Set(prev);
      next.has(i) ? next.delete(i) : next.add(i);
      return next;
    });
  }

  async function go() {
    if (!ready || busy) return;
    setBusy(true);
    try {
      persistName(name.trim());
      startTimer();
      await api.patchIntake({ name: name.trim() });
      router.push("/onboarding/profile");
    } catch {
      setBusy(false);
    }
  }

  return (
    <>
      <OnboardingTop active="why" pct={pct} />
      <main className="flex-1 flex items-center py-12">
        <div className="wrap grid items-center gap-16 md:grid-cols-[1.05fr_.95fr]">
          <section>
            <span className="eyebrow mb-5">brand voice, from zero</span>
            <h1 className="serif text-[clamp(46px,6.4vw,78px)]">
              let&apos;s find
              <br />
              your <span className="hl">brand voice.</span>
            </h1>
            <p className="mt-5 text-[18px] max-w-[30ch]" style={{ color: "#C8C8C2" }}>
              no time to sit and write? timbre learns your voice once — then you just drop in
              what you worked on and it writes the post for you. sounds like you, every time.
            </p>
            <div className="mt-7 flex items-center gap-2 text-[13px]" style={{ color: "var(--muted)" }}>
              <span className="pill">drafts only</span>
              <span>timbre never posts for you.</span>
            </div>
          </section>

          <section className="card">
            <div className="font-[var(--display)] font-semibold text-[17px]">
              which of these sound like you?
              <small className="block font-normal text-[13.5px] mt-1" style={{ color: "var(--muted)" }}>
                pick any. this is just so we get you.
              </small>
            </div>
            <div className="flex flex-wrap gap-2.5 my-4">
              {WHYS.map((w, i) => (
                <button
                  key={i}
                  className={`chip ${picked.has(i) ? "on" : ""}`}
                  onClick={() => toggle(i)}
                  type="button"
                >
                  {w}
                </button>
              ))}
            </div>

            <div className="mt-6 pt-5 border-t" style={{ borderColor: "var(--border)" }}>
              <div className="font-[var(--display)] font-semibold text-[17px] mb-3.5">
                nice. and what should we call you?
              </div>
              <div className="field flex gap-2.5">
                <input
                  className="tn flex-1 min-w-0"
                  type="text"
                  placeholder="first name"
                  autoComplete="off"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && go()}
                />
                <button className={`cta shrink-0 ${ready ? "" : "disabled"}`} onClick={go} type="button">
                  {busy ? "tuning…" : "tune my voice"} <span className="arrow">→</span>
                </button>
              </div>
              <div className="mt-3 text-[12.5px] min-h-4" style={{ color: "var(--muted)" }}>
                {hint}
              </div>
            </div>
          </section>
        </div>
      </main>
    </>
  );
}
