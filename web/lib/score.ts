// Friendly labels for the engine's real 6 gates + 9 dimensions (the compose eval panel
// shows these, mapped from engine/rubric/schemas.py GATE_NAMES / DIM_NAMES).

export const GATE_LABELS: Record<string, string> = {
  only_you: "an only-you take",
  real_number_or_specific: "a real number or specific",
  concrete_scene: "a concrete scene",
  non_obvious_lesson: "a non-obvious lesson",
  no_slop: "no slop",
  central_claim_human: "sounds like you",
};

export const DIM_LABELS: Record<string, string> = {
  story_strength: "story strength",
  opinion_edge: "opinion edge",
  specificity_surprise: "specificity & surprise",
  emotional_resonance: "emotional resonance",
  ownability: "ownability",
  voice_match: "voice match",
  format_adherence: "format adherence",
  audience_fit: "audience fit",
  stakes_turn: "stakes / turn",
};

export const gateLabel = (name: string) => GATE_LABELS[name] ?? name.replace(/_/g, " ");
export const dimLabel = (name: string) => DIM_LABELS[name] ?? name.replace(/_/g, " ");
