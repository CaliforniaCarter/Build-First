// 1:1 mirror of engine/blocks/intake.py (pydantic Intake) and data/intake.example.json.
// Keep this in sync with the Python model — it is the single source of truth the
// onboarding screens assemble and PUT/PATCH to the API.

export interface ContentIdea {
  topic: string; // required by the engine
  take: string;
  scene: string;
  number: string; // "" if no real number
  lesson: string;
  only_you: string;
  mechanism: string;
  proof: string[];
  close: string;
}
export interface Online {
  linkedin: string;
  x: string;
  other: string;
  existing_posts: string;
  cold_start: boolean;
}
export interface Docs {
  resume: string;
  portfolio: string;
}
export interface Typed {
  identity: string;
  known_for: string;
  background: string;
  beliefs: string;
  lessons: string;
}
export interface Voice {
  answers: Record<string, string>;
  tone_words: string[];
  look: string;
  sentence_length: string;
  banned: string[];
  signatures: string[];
  emojis: string;
  notes: string;
}
export interface Audience {
  writing_for: string;
  goal: string;
  play_to: string;
}
export interface OutputPrefs {
  channels: string[];
  length: string;
  format: string;
  hard_nevers: string[];
  off_limits: string;
}
export interface Intake {
  name: string; // required by the engine
  idea: ContentIdea;
  online: Online;
  docs: Docs;
  typed: Typed;
  voice: Voice;
  audience: Audience;
  output: OutputPrefs;
}

export function emptyIntake(): Intake {
  return {
    name: "",
    idea: {
      topic: "",
      take: "",
      scene: "",
      number: "",
      lesson: "",
      only_you: "",
      mechanism: "",
      proof: [],
      close: "",
    },
    online: { linkedin: "", x: "", other: "", existing_posts: "", cold_start: true },
    docs: { resume: "", portfolio: "" },
    typed: { identity: "", known_for: "", background: "", beliefs: "", lessons: "" },
    voice: {
      answers: {},
      tone_words: [],
      look: "",
      sentence_length: "",
      banned: [],
      signatures: [],
      emojis: "",
      notes: "",
    },
    audience: { writing_for: "", goal: "", play_to: "" },
    output: { channels: ["LinkedIn"], length: "", format: "", hard_nevers: [], off_limits: "" },
  };
}

// Truthful onboarding completion (0..1): the share of the fields onboarding asks for
// that are actually filled. Powers the "voice tuned %" meter — no faked numbers.
export function completion(i: Intake): number {
  const filled = (s: string) => s.trim().length > 0;
  const checks: boolean[] = [
    filled(i.name),
    filled(i.online.linkedin) || filled(i.online.x),
    filled(i.docs.resume),
    filled(i.typed.identity),
    filled(i.typed.known_for),
    filled(i.typed.beliefs),
    Object.values(i.voice.answers).some(filled),
    i.voice.tone_words.length > 0,
    filled(i.voice.sentence_length),
  ];
  const done = checks.filter(Boolean).length;
  return done / checks.length;
}
