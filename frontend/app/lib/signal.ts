import type { Deal } from "./api";

/** Visual + copy mapping for the three branches — shared by the ledger and the trace panel. */
export const SIGNAL: Record<
  NonNullable<Deal["branch"]>,
  { dot: string; ring: string; label: string }
> = {
  confident: { dot: "bg-signal-green", ring: "ring-signal-green/40", label: "confident" },
  ambiguous: { dot: "bg-signal-amber", ring: "ring-signal-amber/40", label: "ambiguous" },
  deprioritize: { dot: "bg-signal-rust", ring: "ring-signal-rust/40", label: "deprioritize" },
};

export function signalFor(branch: Deal["branch"]) {
  if (!branch) return { dot: "bg-paper-dim/40", ring: "ring-paper-dim/20", label: "pending" };
  return SIGNAL[branch];
}
