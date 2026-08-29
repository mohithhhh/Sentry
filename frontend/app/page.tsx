"use client";

import { useRef, useState } from "react";
import DealList from "./components/DealList";
import TraceFeed from "./components/TraceFeed";
import { ingestDeals, getDeals, triggerRetriage, type Deal } from "./lib/api";

const HERO_DEAL_ID = "deal-003";
const HERO_REPLY =
  "Sorry for the delay — we looped in our data lead and got sign-off. Would love to move forward, can we grab time this week to finalize pricing?";

export default function Home() {
  const [deals, setDeals] = useState<Deal[]>([]);
  const [activeDealId, setActiveDealId] = useState<string | null>(null);
  const [streamKey, setStreamKey] = useState(0);
  const [isBusy, setIsBusy] = useState(false);
  const [progress, setProgress] = useState<string | null>(null);
  const pendingDoneRef = useRef<(() => void) | null>(null);

  // Opens a fresh trace stream for dealId and resolves once it reports "done".
  // A ref-held resolver is how the imperative EventSource lifecycle (owned by
  // TraceFeed) reports back to this async orchestration.
  function runStreamFor(dealId: string): Promise<void> {
    return new Promise((resolve) => {
      pendingDoneRef.current = resolve;
      setStreamKey((k) => k + 1);
      setActiveDealId(dealId);
    });
  }

  function handleTraceDone(finalState: Deal) {
    setDeals((prev) =>
      prev.map((d) => (d.deal_id === finalState.deal_id ? { ...d, ...finalState } : d))
    );
    pendingDoneRef.current?.();
    pendingDoneRef.current = null;
  }

  // A stream can fail mid-flight (network blip, backend restart). Without
  // this, the orchestration below would await a "done" that never comes and
  // the page would sit stuck on "Triaging…" with the buttons disabled forever.
  function handleTraceError() {
    pendingDoneRef.current?.();
    pendingDoneRef.current = null;
  }

  async function handleLoadDeals() {
    setIsBusy(true);
    await ingestDeals();
    const list = await getDeals();
    setDeals(list);
    for (let i = 0; i < list.length; i++) {
      setProgress(`Triaging ${list[i].deal_id} (${i + 1} of ${list.length})…`);
      await runStreamFor(list[i].deal_id);
    }
    setActiveDealId(null);
    setProgress(null);
    setIsBusy(false);
  }

  async function handleSimulateReply() {
    setIsBusy(true);
    setProgress(`Re-triaging ${HERO_DEAL_ID}…`);
    await triggerRetriage(HERO_DEAL_ID, HERO_REPLY);
    await runStreamFor(HERO_DEAL_ID);
    setProgress(null);
    setIsBusy(false);
  }

  const heroDeal = deals.find((d) => d.deal_id === HERO_DEAL_ID);

  return (
    <main className="min-h-screen px-6 py-10 sm:px-10">
      <div className="mx-auto max-w-3xl space-y-10">
        <header className="space-y-4">
          <p className="font-mono text-xs tracking-[0.2em] text-paper-dim uppercase">
            Sentry · Deal watch
          </p>
          <h1 className="font-display text-4xl text-paper">Sentry</h1>
          <p className="text-paper-dim max-w-xl">
            Watches every deal thread and explains, in one sentence, why it needs you now —
            or why it doesn&apos;t.
          </p>

          <div className="flex items-center gap-3 pt-2">
            <button
              onClick={handleLoadDeals}
              disabled={isBusy}
              className="px-4 py-2 rounded border border-paper/30 text-sm font-medium text-paper hover:bg-panel-raised disabled:opacity-40 disabled:hover:bg-transparent transition-colors"
            >
              {deals.length === 0 ? "Load deals" : "Reload deals"}
            </button>
            {progress && (
              <span className="font-mono text-xs text-paper-dim">{progress}</span>
            )}
          </div>
        </header>

        <DealList
          deals={deals}
          activeDealId={activeDealId}
          heroDealId={HERO_DEAL_ID}
          onSimulateReply={handleSimulateReply}
          simulateDisabled={isBusy || !heroDeal || heroDeal.branch !== "ambiguous"}
        />

        <TraceFeed
          key={streamKey}
          dealId={activeDealId}
          onDone={handleTraceDone}
          onError={handleTraceError}
        />
      </div>
    </main>
  );
}
