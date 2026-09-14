// Purely cosmetic label mapping for the REAL `reasoning_model` value the
// backend returns (see backend/app/graph/nodes/gemini_reasoning.py). The
// backend only reports a model it actually used — nothing here is invented.
const MODEL_LABELS = {
  "gemini-3.6-flash": "Gemini 3.6 Flash",
  "gemini-3.5-flash-lite": "Gemini 3.5 Flash-Lite",
};

export const PRIMARY_MODEL_ID = "gemini-3.6-flash";
export const SECONDARY_MODEL_ID = "gemini-3.5-flash-lite";

export function formatModelName(modelId) {
  if (!modelId) return null;
  return MODEL_LABELS[modelId] || modelId;
}

export function isFallbackModel(modelId) {
  return Boolean(modelId) && modelId !== PRIMARY_MODEL_ID;
}
