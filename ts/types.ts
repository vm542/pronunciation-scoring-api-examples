// Types for the stable compact response (send the header `TonePerfect-Response: compact`).
// Schema: https://api.toneperfect.app/capsule/compact.schema.json  (toneperfect.compact.v1)

export type Decision = 'review' | 'uncertain' | 'no_correction' | 'content_mismatch_suspected' | null;

export interface CompactUnit {
  dimension: 'initial' | 'final' | 'tone' | 'phoneme';
  expected: string | number | null;
  heard: string | number | null;
  score: number | null;
  decision: Decision; // Mandarin units only; null elsewhere (the decision is on the word)
}

export interface CompactWord {
  text: string;
  pinyin?: string;
  expected_ipa?: string;
  score: number | null;
  start_ms: number | null;
  end_ms: number | null;
  decision: Decision; // non-Mandarin words; null for Mandarin
  units: CompactUnit[];
}

export interface CompactResult {
  schema: 'toneperfect.compact.v1';
  id: string;
  assessable: boolean;
  reason: string | null;
  locale: string | null;
  task: string | null;
  model_version: string | null;
  scores: {
    overall: number | null; pronunciation: number | null;
    initial: number | null; final: number | null; tone: number | null;
    fluency: number | null; rhythm: number | null; completeness: number | null;
  };
  words: CompactWord[];
  warnings: unknown[];
  billing: { credits: number; [k: string]: unknown };
}

export interface ApiErrorBody { error: { code: string; message: string } }
