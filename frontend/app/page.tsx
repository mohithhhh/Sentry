import DealList from "./components/DealList";
import TraceFeed from "./components/TraceFeed";

/**
 * Root page for Sentry.
 *
 * TODO: implement layout/state wiring between DealList and TraceFeed
 * (e.g. selecting a deal and streaming its trace).
 */
export default function Home() {
  return (
    <main>
      {/* TODO: replace placeholders with real data-driven components */}
      <DealList />
      <TraceFeed />
    </main>
  );
}
