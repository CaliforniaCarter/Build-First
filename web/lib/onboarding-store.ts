// Tiny client-side helpers for onboarding: the person's name (for instant greetings)
// and a REAL elapsed timer (so "tuned in M:SS" on the done screen is honest, not faked).

const NAME_KEY = "timbre_name";
const START_KEY = "timbre_started_at";

export function setName(name: string) {
  if (typeof window !== "undefined") localStorage.setItem(NAME_KEY, name);
}
export function getName(): string {
  if (typeof window === "undefined") return "";
  return localStorage.getItem(NAME_KEY) ?? "";
}

export function startTimer() {
  if (typeof window === "undefined") return;
  if (!localStorage.getItem(START_KEY)) localStorage.setItem(START_KEY, String(Date.now()));
}

export function resetTimer() {
  if (typeof window !== "undefined") localStorage.setItem(START_KEY, String(Date.now()));
}

export function elapsedLabel(): string {
  if (typeof window === "undefined") return "—";
  const started = Number(localStorage.getItem(START_KEY) || 0);
  if (!started) return "—";
  const secs = Math.max(0, Math.round((Date.now() - started) / 1000));
  const m = Math.floor(secs / 60);
  const s = secs % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}
