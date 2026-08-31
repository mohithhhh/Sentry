"use client";

import { useEffect, useState } from "react";
import { streamDeal, type Deal } from "../lib/api";
import { signalFor } from "../lib/signal";

interface TraceLine {
  node: string;
  phase: "start" | "end";
  text: string;
}

interface TraceFeedProps {
  dealId: string | null;
  onDone?: (finalState: Deal) => void;
  onError?: () => void;
}

const NODE_STARTING: Record<string, string> = {
  analyst: "reading the thread",
  strategist: "deciding what to do",
  sentry_check: "checking the loop",
};

function describeEnd(node: string, state: Partial<Deal> | null): string {
  if (!state) return "done";
  if (node === "analyst") {
    return `classified ${state.branch ?? "?"} — ${state.reasoning ?? "no reasoning given"}`;
  }
  if (node === "strategist") {
    return state.crm_status
      ? `booked ${state.calendar_slot}, drafted a follow-up, marked ${state.crm_status} in the CRM`
      : "no action taken";
  }
  if (node === "sentry_check") {
    return `iteration ${state.iteration ?? "?"} of ${state.max_iterations ?? "?"}`;
  }
  return "done";
}

export default function TraceFeed({ dealId, onDone, onError }: TraceFeedProps) {
  const [lines, setLines] = useState<TraceLine[]>([]);
  const [finalState, setFinalState] = useState<Deal | null>(null);
  const [isLive, setIsLive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLines([]);
    setFinalState(null);
    setError(null);
    if (!dealId) return;

    setIsLive(true);
    const source = streamDeal(dealId);

    source.addEventListener("node_start", (e) => {
      const { node } = JSON.parse((e as MessageEvent).data);
      setLines((prev) => [
        ...prev,
        { node, phase: "start", text: NODE_STARTING[node] ?? "working" },
      ]);
    });

    source.addEventListener("node_end", (e) => {
      const { node, state } = JSON.parse((e as MessageEvent).data);
      setLines((prev) => [...prev, { node, phase: "end", text: describeEnd(node, state) }]);
    });

    source.addEventListener("done", (e) => {
      const state = JSON.parse((e as MessageEvent).data) as Deal;
      setFinalState(state);
      setIsLive(false);
      onDone?.(state);
      source.close();
    });

    source.onerror = () => {
      setIsLive(false);
      setError("Lost connection to Sentry before it finished this deal.");
      source.close();
      onError?.();
    };

    return () => {
      setIsLive(false);
      source.close();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dealId]);

  const signal = finalState ? signalFor(finalState.branch) : null;

  return (
    <section aria-labelledby="trace-heading">
      <div className="flex items-center justify-between mb-3">
        <h2 id="trace-heading" className="font-display text-lg text-paper">
          Reasoning trace
        </h2>
        {isLive && (
          <span className="flex items-center gap-1.5 text-xs text-signal-amber font-mono">
            <span className="h-1.5 w-1.5 rounded-full bg-signal-amber animate-live-pulse" />
            live — {dealId}
          </span>
        )}
      </div>

      <div className="border border-hairline rounded-md bg-panel">
        {!dealId ? (
          <p className="text-sm text-paper-dim p-4">
            Nothing running yet. Load deals to watch Sentry triage them one by one.
          </p>
        ) : (
          <div className="p-4 font-mono text-xs space-y-1.5 max-h-[28rem] overflow-y-auto">
            {error && <p className="text-signal-rust">{error}</p>}
            {lines.map((line, i) => (
              <div
                key={i}
                className={`animate-log-in ${
                  line.phase === "start" ? "text-paper-dim" : "text-paper"
                }`}
              >
                <span className="text-paper-dim">{line.phase === "start" ? "▸" : "✓"}</span>{" "}
                <span className="text-signal-amber">{line.node}</span> — {line.text}
              </div>
            ))}
          </div>
        )}

        {finalState && signal && (
          <div className="border-t border-hairline p-4 space-y-2">
            <div className="flex items-center gap-2">
              <span className={`inline-block h-2.5 w-2.5 rounded-full ${signal.dot}`} />
              <span className="font-display text-paper">{signal.label}</span>
            </div>
            <p className="text-sm text-paper-dim font-mono">{finalState.reasoning}</p>
            {finalState.draft && (
              <div className="text-sm border border-hairline rounded p-3 bg-panel-raised text-paper whitespace-pre-wrap">
                {finalState.draft}
              </div>
            )}
            {finalState.calendar_slot && (
              <p className="text-xs text-paper-dim font-mono">slot: {finalState.calendar_slot}</p>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
