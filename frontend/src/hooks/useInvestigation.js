import { useCallback, useRef, useState } from "react";
import { InvestigationError, investigate } from "../lib/api";

const makeRef = () => `SS-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).slice(2, 6).toUpperCase()}`;

/** idle -> scanning -> result | error, with real stage events from the backend. */
export function useInvestigation() {
  const [phase, setPhase] = useState("idle");
  const [stages, setStages] = useState([]);
  const [preview, setPreview] = useState(null); // verdict known before the explanation arrives
  const [partialUrls, setPartialUrls] = useState([]);
  const [meta, setMeta] = useState(null);
  const [error, setError] = useState(null);
  const abortRef = useRef(null);

  const onEvent = useCallback(({ event, data }) => {
    if (event === "stage") {
      setStages((prev) => {
        const i = prev.findIndex((s) => s.id === data.id);
        if (i === -1) return [...prev, data];
        const copy = [...prev];
        copy[i] = { ...copy[i], ...data, detail: data.detail || copy[i].detail };
        return copy;
      });
    } else if (event === "partial") {
      setPartialUrls(data.urls || []);
    } else if (event === "verdict") {
      setPreview(data);
    }
  }, []);

  const run = useCallback(
    async (mode, input) => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;
      setPhase("scanning");
      setStages([]);
      setPreview(null);
      setPartialUrls([]);
      setError(null);
      try {
        const { result, latencyMs } = await investigate(mode, input, { onEvent, signal: controller.signal });
        setMeta({ result, latencyMs, mode, input, ref: makeRef(), at: new Date() });
        setPhase("result");
      } catch (err) {
        if (err.name === "AbortError") return;
        setError(err instanceof InvestigationError ? err.message : "Something went wrong. Please try again.");
        setPhase("error");
      }
    },
    [onEvent],
  );

  const cancel = useCallback(() => {
    abortRef.current?.abort();
    setPhase("idle");
  }, []);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setPhase("idle");
    setMeta(null);
    setError(null);
    setStages([]);
    setPreview(null);
  }, []);

  return { phase, stages, preview, partialUrls, meta, error, run, cancel, reset };
}
