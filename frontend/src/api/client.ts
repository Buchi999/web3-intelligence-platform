export interface ReadyResponse {
  status: string;
  demo_mode: boolean;
  env: string;
}

export interface ApiErrorBody {
  error: string;
  message: string;
  retryable: boolean;
}

export class ApiError extends Error {
  code: string;
  retryable: boolean;

  constructor(body: ApiErrorBody) {
    super(body.message);
    this.code = body.error;
    this.retryable = body.retryable;
  }
}

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    let body: ApiErrorBody;
    try {
      body = await res.json();
    } catch {
      throw new Error(`Request failed: HTTP ${res.status}`);
    }
    throw new ApiError(body);
  }
  return res.json();
}

export async function fetchReady(): Promise<ReadyResponse> {
  return getJson("/api/v1/ready");
}

// -- Wallet -----------------------------------------------------------------

export interface ProviderMeta {
  source: string;
  retrieved_at: string;
  confidence: "real" | "estimated" | "synthetic";
  block_number: number | null;
}

export interface WalletOverview {
  address: string;
  native_balance_wei: string;
  native_balance_native_unit: number;
  meta: ProviderMeta;
}

export interface BehaviorClassification {
  label: string;
  confidence: number;
  factors: string[];
}

export interface RiskFactor {
  description: string;
  points: number;
}

export interface RiskAssessment {
  score: number;
  factors: RiskFactor[];
  disclaimer: string;
}

export interface WalletAnalysis {
  address: string;
  wallet_age_days: number | null;
  classifications: BehaviorClassification[];
  risk: RiskAssessment;
  ai_summary: string | null;
}

export async function fetchWalletOverview(address: string): Promise<WalletOverview> {
  return getJson(`/api/v1/wallet/${address}`);
}

export async function fetchWalletAnalysis(address: string): Promise<WalletAnalysis> {
  return getJson(`/api/v1/wallet/${address}/analysis`);
}

// -- Collection ---------------------------------------------------------------

export interface CollectionOverview {
  address: string;
  name: string | null;
  is_verified: boolean;
  meta: ProviderMeta;
}

export interface DistributionBucket {
  label: string;
  holder_count: number;
}

export interface TopHolder {
  address: string;
  quantity: number;
  pct_of_supply: number;
}

export interface CollectionHolders {
  address: string;
  total_holders: number;
  total_supply_held: number;
  top_10_concentration_pct: number | null;
  top_50_concentration_pct: number | null;
  average_holdings: number | null;
  median_holdings: number | null;
  distribution: DistributionBucket[];
  top_holders: TopHolder[];
  data_note: string | null;
}

export async function fetchCollectionOverview(address: string): Promise<CollectionOverview> {
  return getJson(`/api/v1/collection/${address}`);
}

export async function fetchCollectionHolders(address: string): Promise<CollectionHolders> {
  return getJson(`/api/v1/collection/${address}/holders`);
}

// -- Reports ------------------------------------------------------------------

export type ReportTargetType = "wallet" | "collection";

/** POSTs to /api/v1/reports, then triggers a real browser file download of
 * the returned PDF. Throws ApiError if the backend returns an error instead
 * of a PDF (e.g. PROVIDER_CAPABILITY_UNAVAILABLE with no ALCHEMY_API_KEY). */
export async function downloadReport(targetType: ReportTargetType, address: string): Promise<void> {
  const res = await fetch("/api/v1/reports", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target_type: targetType, address }),
  });

  if (!res.ok) {
    let body: ApiErrorBody;
    try {
      body = await res.json();
    } catch {
      throw new Error(`Report generation failed: HTTP ${res.status}`);
    }
    throw new ApiError(body);
  }

  const blob = await res.blob();
  const disposition = res.headers.get("Content-Disposition") || "";
  const match = disposition.match(/filename="?([^"]+)"?/);
  const filename = match ? match[1] : `${targetType}-report-${address}.pdf`;

  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}