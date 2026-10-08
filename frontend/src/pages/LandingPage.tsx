import { useEffect, useState } from "react";
import { fetchReady, ReadyResponse } from "../api/client";

export default function LandingPage() {
  const [backend, setBackend] = useState<ReadyResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchReady()
      .then(setBackend)
      .catch((e) => setError(e.message));
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center px-6">
      <h1 className="text-4xl font-bold mb-3">Understand Any Web3 Wallet in Seconds</h1>
      <p className="text-slate-400 mb-8 max-w-xl text-center">
        Analyze wallet activity, NFTs, tokens and on-chain behavior with actionable blockchain
        intelligence.
      </p>
      <a
        href="/analyze"
        className="bg-indigo-500 hover:bg-indigo-400 transition-colors px-6 py-3 rounded-lg font-medium"
      >
        Analyze a Wallet
      </a>

      <div className="mt-10 text-sm text-slate-500">
        {error && <span className="text-red-400">Backend unreachable: {error}</span>}
        {backend && (
          <span>
            Backend status: {backend.status} · demo mode: {String(backend.demo_mode)}
          </span>
        )}
      </div>
    </div>
  );
}
