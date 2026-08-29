"use client";

import type { Deal } from "../lib/api";
import { signalFor } from "../lib/signal";

interface DealListProps {
  deals: Deal[];
  activeDealId: string | null;
  heroDealId: string;
  onSimulateReply: () => void;
  simulateDisabled: boolean;
}

export default function DealList({
  deals,
  activeDealId,
  heroDealId,
  onSimulateReply,
  simulateDisabled,
}: DealListProps) {
  return (
    <section aria-labelledby="deals-heading">
      <h2 id="deals-heading" className="font-display text-lg text-paper mb-3">
        Deals
      </h2>

      {deals.length === 0 ? (
        <p className="text-sm text-paper-dim border border-dashed border-hairline rounded-md p-4">
          Nothing loaded yet. Load deals to bring in the synthetic threads and watch Sentry
          triage them one by one.
        </p>
      ) : (
        <div className="border border-hairline rounded-md overflow-hidden">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wide text-paper-dim border-b border-hairline">
                <th className="py-2 pl-4 pr-2 font-sans font-medium w-8" aria-hidden="true"></th>
                <th className="py-2 pr-2 font-sans font-medium">Deal</th>
                <th className="py-2 pr-2 font-sans font-medium">Reasoning</th>
                <th className="py-2 pr-2 font-sans font-medium whitespace-nowrap">CRM status</th>
                <th className="py-2 pr-4 font-sans font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {deals.map((deal) => {
                const signal = signalFor(deal.branch);
                const isActive = deal.deal_id === activeDealId;
                return (
                  <tr
                    key={deal.deal_id}
                    className={`border-b border-hairline last:border-0 ${
                      isActive ? "bg-panel-raised" : ""
                    }`}
                  >
                    <td className="py-3 pl-4 pr-2">
                      <span
                        className={`inline-block h-2.5 w-2.5 rounded-full ring-4 ${signal.dot} ${signal.ring}`}
                        title={signal.label}
                      />
                    </td>
                    <td className="py-3 pr-2 align-top">
                      <div className="font-medium text-paper">
                        {deal.company ?? deal.deal_id}
                      </div>
                      <div className="text-xs text-paper-dim">
                        {deal.prospect_name ?? deal.deal_id}
                      </div>
                    </td>
                    <td className="py-3 pr-2 align-top text-paper-dim max-w-sm">
                      {deal.reasoning ?? (isActive ? "triaging…" : "not yet triaged")}
                    </td>
                    <td className="py-3 pr-2 align-top font-mono text-xs text-paper-dim">
                      {deal.crm_status ?? "—"}
                    </td>
                    <td className="py-3 pr-4 align-top text-right">
                      {deal.deal_id === heroDealId && deal.branch === "ambiguous" && (
                        <button
                          onClick={onSimulateReply}
                          disabled={simulateDisabled}
                          className="text-xs px-2.5 py-1 rounded border border-signal-amber/50 text-signal-amber hover:bg-signal-amber/10 disabled:opacity-40 disabled:hover:bg-transparent transition-colors"
                        >
                          Simulate a reply
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
