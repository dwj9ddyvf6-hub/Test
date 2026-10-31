import {
  APERTURE_UNIVERSE_COUNT,
  APERTURE_UNIVERSE_HASH,
  APERTURE_UNIVERSE_ID,
} from "./aperture-universe.ts";
import { inferUsEquitySession, sessionLabel } from "./freshness.ts";
import type { LiveDiscoveryView, LiveTriggerSummary } from "./live-contracts.ts";

export const LIVE_TRIGGER_REGISTRY: LiveTriggerSummary[] = [
  { id: "sweep-reclaim", label: "Sweep / reclaim", purpose: "Liquidity pierces declared support, then a completed bar reclaims it.", gate: "Support cluster · strong close · below chase line", ttl: "3 bars", active: 0 },
  { id: "structural-hold", label: "Structural hold", purpose: "Repeated support contact survives and produces completed-bar follow-through.", gate: "Two closes · higher close · valid support", ttl: "4 bars", active: 0 },
  { id: "rotation-ignition", label: "Rotation ignition", purpose: "RSI and MACD curl from support while the move remains early.", gate: "RSI curl · MACD curl · location", ttl: "6 bars", active: 0 },
];

export function makeUnconfiguredView(now = new Date()): LiveDiscoveryView {
  const generatedAt = now.toISOString();
  const session = inferUsEquitySession(now);
  return {
    schema: "aperture-live-view.v1",
    dataMode: "unconfigured",
    provider: "ALPACA IEX",
    feed: "AWAITING PRIVATE MARKET-DATA CONNECTION",
    connection: "CONFIGURATION REQUIRED",
    freshness: "OFFLINE",
    session,
    sessionLabel: sessionLabel(session),
    marketNextTransitionAt: null,
    generatedAt,
    inputWatermarkAt: null,
    barEndAt: null,
    validUntil: null,
    etag: 'W/"aperture-live-unconfigured-v1"',
    authority: {
      decisionSupport: true,
      orderRoute: false,
      tensorWrite: false,
      galathWrite: false,
      folioTendWrite: false,
    },
    universe: {
      id: APERTURE_UNIVERSE_ID,
      count: APERTURE_UNIVERSE_COUNT,
      hash: APERTURE_UNIVERSE_HASH,
      eligible: 0,
      covered: 0,
      unsupported: APERTURE_UNIVERSE_COUNT,
    },
    scan: {
      state: "WAITING",
      elapsedMs: null,
      harvested: 0,
      deepCandidates: 0,
      decisions: 0,
      executable: 0,
      stages: [
        { label: "Feed", value: "NOT CONNECTED", note: "private Alpaca key required", tone: "amber" },
        { label: "Universe", value: "0 / 413", note: "no live bars accepted", tone: "default" },
        { label: "Sealed bar", value: "—", note: "waiting for collector", tone: "default" },
        { label: "Decisions", value: "0", note: "no synthetic fallback", tone: "default" },
        { label: "Orders", value: "0", note: "no order route", tone: "amber" },
      ],
    },
    summary: [
      { label: "Buy now", value: "0", note: "fresh S only", tone: "cyan" },
      { label: "Wait / watch", value: "0", note: "A / B / forming", tone: "default" },
      { label: "Avoid", value: "0", note: "hard vetoes", tone: "amber" },
      { label: "No view", value: "413", note: "live feed unavailable", tone: "default" },
    ],
    backdrop: [
      { label: "Market", value: "NO VIEW", detail: "live benchmark missing", tone: "neutral" },
      { label: "Breadth", value: "NO VIEW", detail: "live universe missing", tone: "neutral" },
      { label: "Volatility", value: "NO VIEW", detail: "live context missing", tone: "neutral" },
      { label: "Data", value: "OFFLINE", detail: "production does not substitute samples", tone: "warning" },
    ],
    triggers: LIVE_TRIGGER_REGISTRY,
    decisions: [],
    quality: {
      flags: ["LIVE_FEED_NOT_CONFIGURED", "NO_SYNTHETIC_FALLBACK"],
      missingInputs: ["APERTURE_ALPACA_KEY_ID", "APERTURE_ALPACA_SECRET_KEY", "LIVE_COLLECTOR"],
      coveragePct: 0,
    },
  };
}
