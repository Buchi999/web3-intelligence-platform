import { useState } from "react";
import {
  ApiError,
  CollectionHolders,
  CollectionOverview,
  ReportTargetType,
  WalletAnalysis,
  WalletOverview,
  downloadReport,
  fetchCollectionHolders,
  fetchCollectionOverview,
  fetchWalletAnalysis,
  fetchWalletOverview,
} from "../api/client";

function stripMarkdownBold(text: string): string {
  return text.replace(/\*\*/g, "").replace(/^#+\s*/gm, "");
}

function ConfidenceBadge({ confidence }: { confidence: string }) {
  const colors: Record<string, string> = {
    real: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
    estimated: "bg-amber-500/20 text-amber-300 border-amber-500/40",
    synthetic: "bg-slate-500/20 text-slate-300 border-slate-500/40",
  };
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full border ${colors[confidence] || colors.synthetic}`}>
      {confidence}
    </span>
  );
}

export default function AnalyzePage() {
  const [targetType, setTargetType] = useState<ReportTargetType>("wallet");
  const [address, setAddress] = useState("");
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [walletOverview, setWalletOverview] = useState<WalletOverview | null>(null);
  const [walletAnalysis, setWalletAnalysis] = useState<WalletAnalysis | null>(null);
  const [collectionOverview, setCollectionOverview] = useState<CollectionOverview | null>(null);
  const [collectionHolders, setCollectionHolders] = useState<CollectionHolders | null>(null);

  const hasResults = targetType === "wallet" ? !!walletOverview : !!collectionOverview;

  async function handleLookup() {
    setError(null);
    setLoading(true);
    setWalletOverview(null);
    setWalletAnalysis(null);
    setCollectionOverview(null);
    setCollectionHolders(null);
    try {
      if (targetType === "wallet") {
        const [overview, analysis] = await Promise.all([
          fetchWalletOverview(address),
          fetchWalletAnalysis(address),
        ]);
        setWalletOverview(overview);
        setWalletAnalysis(analysis);
      } else {
        const [overview, holders] = await Promise.all([
          fetchCollectionOverview(address),
          fetchCollectionHolders(address),
        ]);
        setCollectionOverview(overview);
        setCollectionHolders(holders);
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Something went wrong looking that up.");
    } finally {
      setLoading(false);
    }
  }

  async function handleDownload() {
    setError(null);
    setDownloading(true);
    try {
      await downloadReport(targetType, address);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Something went wrong generating the report.");
    } finally {
      setDownloading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 flex flex-col items-center">
      <h1 className="text-2xl font-semibold mb-2">Analyze a Wallet or Collection</h1>
      <p className="text-slate-400 mb-6 text-sm">Look up on-chain intelligence, then download a full PDF report.</p>

      <div className="flex gap-2 mb-4 bg-slate-900 border border-slate-700 rounded-lg p-1">
        {(["wallet", "collection"] as ReportTargetType[]).map((t) => (
          <button
            key={t}
            onClick={() => {
              setTargetType(t);
              setError(null);
            }}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
              targetType === t ? "bg-indigo-500 text-white" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            {t === "wallet" ? "Wallet" : "NFT Collection"}
          </button>
        ))}
      </div>

      <div className="flex gap-2 w-full max-w-lg mb-4">
        <input
          className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 outline-none focus:border-indigo-500"
          placeholder={targetType === "wallet" ? "0x... wallet address" : "0x... contract address"}
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && address && !loading && handleLookup()}
        />
        <button
          className="bg-indigo-500 hover:bg-indigo-400 transition-colors px-5 py-2 rounded-lg font-medium disabled:opacity-40 whitespace-nowrap"
          disabled={!address || loading}
          onClick={handleLookup}
        >
          {loading ? "Looking up..." : "Look Up"}
        </button>
      </div>

      {error && (
        <div className="w-full max-w-lg bg-red-950/50 border border-red-800 text-red-300 text-sm rounded-lg px-4 py-3 mb-4">
          {error}
        </div>
      )}

      {hasResults && (
        <div className="w-full max-w-lg mb-6">
          <button
            className="w-full bg-emerald-600 hover:bg-emerald-500 transition-colors px-5 py-3 rounded-lg font-medium disabled:opacity-40"
            disabled={downloading}
            onClick={handleDownload}
          >
            {downloading ? "Generating PDF..." : "Download Full PDF Report"}
          </button>
        </div>
      )}

      {targetType === "wallet" && walletOverview && (
        <div className="w-full max-w-lg bg-slate-900 border border-slate-700 rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-semibold">{walletOverview.native_balance_native_unit.toFixed(4)} ETH</div>
              <div className="text-xs text-slate-500 break-all">{walletOverview.address}</div>
            </div>
            <ConfidenceBadge confidence={walletOverview.meta.confidence} />
          </div>

          {walletAnalysis && (
            <>
              {walletAnalysis.wallet_age_days !== null && (
                <div className="text-sm text-slate-400">Wallet age: {walletAnalysis.wallet_age_days} day(s)</div>
              )}

              {walletAnalysis.classifications.length > 0 && (
                <div>
                  <div className="text-sm font-medium text-slate-300 mb-1">Behavior Classification</div>
                  <div className="flex flex-wrap gap-2">
                    {walletAnalysis.classifications.map((c) => (
                      <span
                        key={c.label}
                        title={c.factors.join(" · ")}
                        className="text-xs px-2 py-1 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/40"
                      >
                        {c.label} ({c.confidence.toFixed(0)}%)
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div>
                <div className="text-sm font-medium text-slate-300 mb-1">
                  Risk Score: {walletAnalysis.risk.score}/100
                </div>
                {walletAnalysis.risk.factors.length > 0 ? (
                  <ul className="text-xs text-slate-400 list-disc list-inside space-y-0.5">
                    {walletAnalysis.risk.factors.map((f, i) => (
                      <li key={i}>
                        {f.description} (+{f.points})
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="text-xs text-slate-500">No risk factors identified.</div>
                )}
              </div>

              {walletAnalysis.ai_summary ? (
                <div>
                  <div className="text-sm font-medium text-slate-300 mb-1">AI Summary</div>
                  <div className="text-xs text-slate-400 whitespace-pre-line max-h-48 overflow-y-auto">
                    {stripMarkdownBold(walletAnalysis.ai_summary)}
                  </div>
                </div>
              ) : (
                <div className="text-xs text-slate-600 italic">
                  AI summary unavailable (configure GROQ_API_KEY for AI-generated analysis).
                </div>
              )}
            </>
          )}
        </div>
      )}

      {targetType === "collection" && collectionOverview && (
        <div className="w-full max-w-lg bg-slate-900 border border-slate-700 rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xl font-semibold">{collectionOverview.name || "Unnamed Collection"}</div>
              <div className="text-xs text-slate-500 break-all">{collectionOverview.address}</div>
            </div>
            {collectionOverview.is_verified && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                verified
              </span>
            )}
          </div>

          {collectionHolders && (
            <>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <div className="text-slate-500 text-xs">Total Holders</div>
                  <div className="font-medium">{collectionHolders.total_holders.toLocaleString()}</div>
                </div>
                <div>
                  <div className="text-slate-500 text-xs">Total Supply Held</div>
                  <div className="font-medium">{collectionHolders.total_supply_held.toLocaleString()}</div>
                </div>
                <div>
                  <div className="text-slate-500 text-xs">Top 10 Concentration</div>
                  <div className="font-medium">
                    {collectionHolders.top_10_concentration_pct?.toFixed(2) ?? "N/A"}%
                  </div>
                </div>
                <div>
                  <div className="text-slate-500 text-xs">Top 50 Concentration</div>
                  <div className="font-medium">
                    {collectionHolders.top_50_concentration_pct?.toFixed(2) ?? "N/A"}%
                  </div>
                </div>
              </div>

              <div>
                <div className="text-sm font-medium text-slate-300 mb-1">Holder Distribution</div>
                <div className="space-y-1">
                  {collectionHolders.distribution.map((d) => (
                    <div key={d.label} className="flex items-center gap-2 text-xs">
                      <span className="w-16 text-slate-400">{d.label}</span>
                      <div className="flex-1 bg-slate-800 rounded h-2 overflow-hidden">
                        <div
                          className="bg-indigo-500 h-2"
                          style={{
                            width: `${(d.holder_count / collectionHolders.total_holders) * 100}%`,
                          }}
                        />
                      </div>
                      <span className="w-10 text-right text-slate-500">{d.holder_count}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <div className="text-sm font-medium text-slate-300 mb-1">Top Holders</div>
                <ul className="text-xs text-slate-400 space-y-0.5">
                  {collectionHolders.top_holders.slice(0, 5).map((h) => (
                    <li key={h.address} className="flex justify-between">
                      <span className="truncate mr-2">{h.address}</span>
                      <span>
                        {h.quantity} ({h.pct_of_supply.toFixed(2)}%)
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}