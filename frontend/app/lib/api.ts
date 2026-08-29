/**
 * API client for the Sentry backend.
 */

// Exposed to the browser via the `env` key in next.config.mjs, since this
// name doesn't carry the NEXT_PUBLIC_ prefix Next.js would otherwise require.
const API_BASE = process.env.NEXT_API_BASE ?? "http://localhost:8000";

export interface DealFeatures {
  days_since_last_message: number;
  last_speaker: "rep" | "prospect";
  last_commitment: string | null;
  commitment_date_passed: boolean;
  sentiment_delta: number;
  unanswered_questions: number;
}

export interface Deal {
  deal_id: string;
  thread_text: string;
  features: DealFeatures | null;
  branch: "confident" | "ambiguous" | "deprioritize" | null;
  reasoning: string | null;
  draft: string | null;
  calendar_slot: string | null;
  crm_status: string | null;
  iteration: number;
  max_iterations: number;
  retriage_requested: boolean;
  prospect_name?: string | null;
  company?: string | null;
}

/** Load the synthetic threads on the backend and seed initial DealState per deal. */
export async function ingestDeals(): Promise<{ ingested: string[]; count: number }> {
  const res = await fetch(`${API_BASE}/deals/ingest`, { method: "POST" });
  if (!res.ok) throw new Error(`ingestDeals failed: ${res.status}`);
  return res.json();
}

/** Fetch the current state snapshot for every deal. */
export async function getDeals(): Promise<Deal[]> {
  const res = await fetch(`${API_BASE}/deals`);
  if (!res.ok) throw new Error(`getDeals failed: ${res.status}`);
  return res.json();
}

/**
 * Open an SSE connection to a deal's reasoning trace. Note: opening this
 * actually (re-)invokes the graph on the backend — it is not a passive
 * "view" of already-computed state. Caller is responsible for closing it
 * (e.g. on a "done" event or on unmount).
 */
export function streamDeal(dealId: string): EventSource {
  return new EventSource(`${API_BASE}/deals/${dealId}/stream`);
}

/** Inject a new message into a deal's thread and flag it for re-triage. */
export async function triggerRetriage(
  dealId: string,
  message: string
): Promise<{ deal_id: string; queued: boolean; thread_text?: string; reason?: string }> {
  const res = await fetch(`${API_BASE}/deals/${dealId}/retriage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  if (!res.ok) throw new Error(`triggerRetriage failed: ${res.status}`);
  return res.json();
}
