import type { DiscoveryCandidate } from "./discovery-data.ts";

export type ApertureSession = "PREMARKET" | "REGULAR" | "AFTERHOURS" | "CLOSED";
export type ApertureFreshness = "LIVE" | "BASELINE" | "LAGGING" | "STALE" | "CLOSED" | "WARMING" | "OFFLINE";
export type ApertureConnection = "CONNECTED" | "DEGRADED" | "OFFLINE" | "CONFIGURATION REQUIRED";
export type ApertureScanState = "WAITING" | "INGESTING" | "HARVESTING" | "EVALUATING" | "PUBLISHING" | "COMPLETE" | "FAILED";

export type LiveDecisionAction = "BUY" | "WAIT" | "AVOID" | "HOLD" | "TRIM" | "SELL" | "NO VIEW";

export type LiveDiscoveryDecision = DiscoveryCandidate & {
  dataMode: "live";
  provider: string;
  barEndAt: string;
  generatedAt: string;
  freshness: ApertureFreshness;
  decisionUsable: boolean;
  nonOwnerAction: LiveDecisionAction;
  ownerAction: LiveDecisionAction;
  chaseBuffer: string;
  indicators: {
    rsi14: string;
    rsiState: string;
    macdHistogram: string;
    macdState: string;
    atr14: string;
    vwap: string;
    distanceFrom60dLow: string;
  };
  packet: DiscoveryCandidate["packet"] & {
    policyEligible: boolean;
    decisionUsable: boolean;
    orderExecutable: false;
    inputHash: string;
    policyHash: string;
    supersedesDecisionId: string | null;
  };
};

export type LiveTriggerSummary = {
  id: string;
  label: string;
  purpose: string;
  gate: string;
  ttl: string;
  active: number;
};

export type LiveDiscoveryView = {
  schema: "aperture-live-view.v1";
  dataMode: "live" | "unconfigured";
  provider: string;
  feed: string;
  connection: ApertureConnection;
  freshness: ApertureFreshness;
  session: ApertureSession;
  sessionLabel: string;
  marketNextTransitionAt: string | null;
  generatedAt: string;
  inputWatermarkAt: string | null;
  barEndAt: string | null;
  validUntil: string | null;
  etag: string;
  authority: {
    decisionSupport: true;
    orderRoute: false;
    tensorWrite: false;
    galathWrite: false;
    folioTendWrite: false;
  };
  universe: {
    id: string;
    count: number;
    hash: string;
    eligible: number;
    covered: number;
    unsupported: number;
  };
  scan: {
    state: ApertureScanState;
    elapsedMs: number | null;
    harvested: number;
    deepCandidates: number;
    decisions: number;
    executable: 0;
    stages: Array<{ label: string; value: string; note: string; tone: "cyan" | "default" | "amber" }>;
  };
  summary: Array<{ label: string; value: string; note: string; tone: "cyan" | "default" | "amber" }>;
  backdrop: Array<{ label: string; value: string; detail: string; tone: "positive" | "neutral" | "warning" | "danger" }>;
  triggers: LiveTriggerSummary[];
  decisions: LiveDiscoveryDecision[];
  quality: {
    flags: string[];
    missingInputs: string[];
    coveragePct: number;
  };
};

export type LiveIngestEnvelope = {
  schema: "aperture-live-ingest.v1";
  universeHash: string;
  publishedAt: string;
  nonce: string;
  view: LiveDiscoveryView;
};

function object(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function iso(value: unknown, nullable = false): boolean {
  if (nullable && value === null) return true;
  return typeof value === "string" && value.length >= 20 && Number.isFinite(new Date(value).getTime());
}

function oneOf<T extends string>(value: unknown, values: readonly T[]): value is T {
  return typeof value === "string" && values.includes(value as T);
}

function strings(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}

function nonnegativeInteger(value: unknown): value is number {
  return typeof value === "number" && Number.isInteger(value) && value >= 0;
}

function validDecision(value: unknown, view: Record<string, unknown>): value is LiveDiscoveryDecision {
  if (!object(value) || !object(value.packet) || !object(value.trigger) || !object(value.proof) || !object(value.indicators)) return false;
  const packet = value.packet;
  const trigger = value.trigger;
  const proof = value.proof;
  const liveActions = ["BUY", "WAIT", "AVOID", "HOLD", "TRIM", "SELL", "NO VIEW"] as const;
  const tiers = ["S", "A", "B", "FORMING", "AVOID", "NO VIEW"] as const;
  const verdicts = ["BUY NOW", "WAIT", "AVOID", "NO VIEW"] as const;
  const triggerStates = ["APPROACH", "SEED", "CONFIRMED", "FAILED", "EXPIRED"] as const;
  const proofStates = ["SUPPORTED", "MIXED", "OBSERVING", "INSUFFICIENT", "REJECTED", "QUARANTINED"] as const;
  if (value.dataMode !== "live"
    || typeof value.id !== "string"
    || typeof value.symbol !== "string"
    || value.provider !== view.provider
    || value.barEndAt !== view.barEndAt
    || value.generatedAt !== view.generatedAt
    || value.freshness !== view.freshness
    || typeof value.decisionUsable !== "boolean"
    || !oneOf(value.tier, tiers)
    || !oneOf(value.verdict, verdicts)
    || !oneOf(value.nonOwnerAction, liveActions)
    || !oneOf(value.ownerAction, liveActions)
    || !oneOf(trigger.state, triggerStates)
    || !oneOf(proof.state, proofStates)
    || !iso(value.barEndAt)
    || !iso(value.generatedAt)
    || typeof packet.policyEligible !== "boolean"
    || typeof packet.decisionUsable !== "boolean"
    || packet.orderExecutable !== false
    || packet.executionEligible !== false
    || packet.shadowOnly !== true
    || typeof packet.inputHash !== "string"
    || packet.inputHash.length < 32
    || typeof packet.policyHash !== "string"
    || packet.policyHash.length < 32
    || !iso(packet.decisionAt)
    || !iso(packet.validUntil)
    || !strings(trigger.lifecycle)
    || !iso(trigger.seedBar)
    || !iso(trigger.expiresAt)
    || !strings(packet.reasonCodes)
    || !strings(packet.blockers)) return false;

  const buy = value.nonOwnerAction === "BUY" || value.tier === "S" || value.verdict === "BUY NOW";
  if (buy && !(value.nonOwnerAction === "BUY"
    && value.tier === "S"
    && value.verdict === "BUY NOW"
    && value.decisionUsable === true
    && packet.decisionUsable === true
    && packet.policyEligible === true
    && trigger.state === "CONFIRMED"
    && proof.state === "SUPPORTED"
    && view.freshness === "LIVE"
    && view.session === "REGULAR")) return false;
  return true;
}

export function isLiveDiscoveryView(value: unknown): value is LiveDiscoveryView {
  if (!object(value) || !object(value.authority) || !object(value.universe) || !object(value.scan) || !object(value.quality)) return false;
  const view = value;
  const sessions = ["PREMARKET", "REGULAR", "AFTERHOURS", "CLOSED"] as const;
  const freshness = ["LIVE", "BASELINE", "LAGGING", "STALE", "CLOSED", "WARMING", "OFFLINE"] as const;
  const connections = ["CONNECTED", "DEGRADED", "OFFLINE", "CONFIGURATION REQUIRED"] as const;
  const scanStates = ["WAITING", "INGESTING", "HARVESTING", "EVALUATING", "PUBLISHING", "COMPLETE", "FAILED"] as const;
  if (view.schema !== "aperture-live-view.v1"
    || !oneOf(view.dataMode, ["live", "unconfigured"] as const)
    || typeof view.provider !== "string"
    || typeof view.feed !== "string"
    || !oneOf(view.connection, connections)
    || !oneOf(view.freshness, freshness)
    || !oneOf(view.session, sessions)
    || typeof view.sessionLabel !== "string"
    || !iso(view.generatedAt)
    || !iso(view.inputWatermarkAt, true)
    || !iso(view.barEndAt, true)
    || !iso(view.validUntil, true)
    || !iso(view.marketNextTransitionAt, true)
    || typeof view.etag !== "string"
    || view.authority.decisionSupport !== true
    || view.authority.orderRoute !== false
    || view.authority.tensorWrite !== false
    || view.authority.galathWrite !== false
    || view.authority.folioTendWrite !== false
    || typeof view.universe.id !== "string"
    || typeof view.universe.hash !== "string"
    || !nonnegativeInteger(view.universe.count)
    || !nonnegativeInteger(view.universe.eligible)
    || !nonnegativeInteger(view.universe.covered)
    || !nonnegativeInteger(view.universe.unsupported)
    || view.universe.covered > view.universe.eligible
    || view.universe.eligible + view.universe.unsupported > view.universe.count
    || !oneOf(view.scan.state, scanStates)
    || view.scan.executable !== 0
    || !nonnegativeInteger(view.scan.harvested)
    || !nonnegativeInteger(view.scan.deepCandidates)
    || !nonnegativeInteger(view.scan.decisions)
    || !Array.isArray(view.summary)
    || !Array.isArray(view.backdrop)
    || !Array.isArray(view.triggers)
    || !Array.isArray(view.decisions)
    || !strings(view.quality.flags)
    || !strings(view.quality.missingInputs)
    || typeof view.quality.coveragePct !== "number"
    || !Number.isFinite(view.quality.coveragePct)
    || view.quality.coveragePct < 0
    || view.quality.coveragePct > 100
    || view.scan.decisions !== view.decisions.length
    || view.decisions.length > 16
    || !view.decisions.every((decision) => validDecision(decision, view))) return false;

  if (view.dataMode === "live") {
    if (!view.barEndAt || !view.inputWatermarkAt || !view.validUntil || view.inputWatermarkAt !== view.barEndAt || view.scan.state !== "COMPLETE") return false;
    if (new Date(view.barEndAt).getTime() > new Date(view.generatedAt).getTime()) return false;
    if ((view.freshness !== "LIVE" || view.session !== "REGULAR")
      && view.decisions.some((decision) => decision.nonOwnerAction === "BUY" || decision.tier === "S" || decision.verdict === "BUY NOW")) return false;
  } else if (view.decisions.length !== 0) return false;
  return true;
}
