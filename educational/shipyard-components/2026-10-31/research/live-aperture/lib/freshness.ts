import type { ApertureFreshness, ApertureSession, LiveDiscoveryDecision, LiveDiscoveryView } from "./live-contracts.ts";

const ET_FORMATTER = new Intl.DateTimeFormat("en-US", {
  timeZone: "America/New_York",
  weekday: "short",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
});

const ET_DATE = new Intl.DateTimeFormat("en-CA", {
  timeZone: "America/New_York",
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
});

function etParts(now: Date) {
  return Object.fromEntries(
    ET_FORMATTER.formatToParts(now)
      .filter((part) => part.type !== "literal")
      .map((part) => [part.type, part.value]),
  );
}

function isRegularSessionBaseline(barEndAt: string, session: ApertureSession, now: Date) {
  if (session === "REGULAR" || session === "CLOSED") return false;
  const bar = new Date(barEndAt);
  const ageMs = now.getTime() - bar.getTime();
  if (!Number.isFinite(ageMs) || ageMs < 0 || ageMs > 72 * 60 * 60_000) return false;
  const parts = etParts(bar);
  const minutes = Number(parts.hour) * 60 + Number(parts.minute);
  // Yahoo's final regular bar is represented by either the 15:55–16:00
  // bucket or a 16:00–16:05 close bucket, depending on the endpoint.
  return minutes >= 15 * 60 + 55 && minutes <= 16 * 60 + 10;
}

export function inferUsEquitySession(now = new Date()): ApertureSession {
  const parts = etParts(now);
  if (parts.weekday === "Sat" || parts.weekday === "Sun") return "CLOSED";
  const minutes = Number(parts.hour) * 60 + Number(parts.minute);
  if (minutes >= 4 * 60 && minutes < 9 * 60 + 30) return "PREMARKET";
  if (minutes >= 9 * 60 + 30 && minutes < 16 * 60) return "REGULAR";
  if (minutes >= 16 * 60 && minutes < 20 * 60) return "AFTERHOURS";
  return "CLOSED";
}

export function sessionLabel(session: ApertureSession): string {
  if (session === "PREMARKET") return "Premarket · 04:00–09:30 ET";
  if (session === "REGULAR") return "Regular · 09:30–16:00 ET";
  if (session === "AFTERHOURS") return "After hours · 16:00–20:00 ET";
  return "Market closed";
}

/**
 * A completed five-minute bar is current until the next bucket has had time
 * to seal and publish. The old two-minute threshold expired valid bars before
 * their successor could exist.
 */
export function classifyFreshness(
  barEndAt: string | null,
  session: ApertureSession,
  now = new Date(),
): ApertureFreshness {
  if (!barEndAt) return "WARMING";
  const ageMs = now.getTime() - new Date(barEndAt).getTime();
  if (!Number.isFinite(ageMs) || ageMs < -60_000) return "STALE";
  if (session === "CLOSED") return ageMs <= 96 * 60 * 60_000 ? "CLOSED" : "STALE";
  if (isRegularSessionBaseline(barEndAt, session, now)) return "BASELINE";
  if (ageMs <= 6.5 * 60_000) return "LIVE";
  if (ageMs <= 8.5 * 60_000) return "LAGGING";
  return "STALE";
}

function effectiveEtag(etag: string, session: ApertureSession, freshness: ApertureFreshness) {
  const base = etag.replace(/^W\/\"/, "").replace(/\"$/, "");
  return `W/"${base}-${session.toLowerCase()}-${freshness.toLowerCase()}"`;
}

function projectDecision(decision: LiveDiscoveryDecision, session: ApertureSession, freshness: ApertureFreshness): LiveDiscoveryDecision {
  const actionableWindow = session === "REGULAR" && freshness === "LIVE";
  const originallyUsable = decision.decisionUsable && decision.packet.decisionUsable;
  if (actionableWindow) {
    return {
      ...decision,
      freshness,
      decisionUsable: originallyUsable,
      nonOwnerAction: originallyUsable ? decision.nonOwnerAction : "NO VIEW",
      packet: {
        ...decision.packet,
        decisionUsable: originallyUsable,
        policyEligible: originallyUsable && decision.packet.policyEligible,
        orderExecutable: false,
      },
    };
  }

  // Premarket and after-hours bars are useful for planning, but they do not
  // have regular-session order authority. Preserve the observed setup and
  // levels while explicitly removing BUY semantics and execution eligibility.
  if ((freshness === "LIVE" || freshness === "BASELINE") && (session === "PREMARKET" || session === "AFTERHOURS")) {
    const planningTier = decision.tier === "S" ? "A" : decision.tier;
    const planningVerdict = planningTier === "AVOID" ? "AVOID" : planningTier === "NO VIEW" ? "NO VIEW" : "WAIT";
    return {
      ...decision,
      tier: planningTier,
      verdict: planningVerdict,
      freshness,
      decisionUsable: false,
      nonOwnerAction: planningVerdict === "AVOID" ? "AVOID" : planningVerdict === "NO VIEW" ? "NO VIEW" : "WAIT",
      ownerAction: "NO VIEW",
      action: planningVerdict === "AVOID"
        ? decision.action
        : `Planning only outside the regular session. Revalidate on the next regular-session completed bar; watch ${decision.entry}.`,
      packet: {
        ...decision.packet,
        policyEligible: false,
        decisionUsable: false,
        orderExecutable: false,
        reasonCodes: [...new Set([...decision.packet.reasonCodes, `OBSERVATION_ONLY_${session}`])],
        blockers: [...new Set([...decision.packet.blockers, "NO_REGULAR_SESSION_AUTHORITY"])],
      },
    };
  }

  if (freshness === "CLOSED") {
    const historicalTier = decision.tier === "AVOID" || decision.tier === "NO VIEW" ? decision.tier : "FORMING";
    const historicalVerdict = historicalTier === "AVOID" ? "AVOID" : historicalTier === "NO VIEW" ? "NO VIEW" : "WAIT";
    return {
      ...decision,
      tier: historicalTier,
      verdict: historicalVerdict,
      freshness,
      decisionUsable: false,
      nonOwnerAction: historicalVerdict === "AVOID" ? "AVOID" : historicalVerdict === "WAIT" ? "WAIT" : "NO VIEW",
      ownerAction: "NO VIEW",
      action: "Market closed. Preserve the final bar for planning only; revalidate after the next regular-session completed bar.",
      packet: {
        ...decision.packet,
        policyEligible: false,
        decisionUsable: false,
        orderExecutable: false,
        reasonCodes: [...new Set([...decision.packet.reasonCodes, "MARKET_CLOSED_FINAL_BAR"])],
        blockers: [...new Set([...decision.packet.blockers, "NO_CURRENT_ENTRY_WINDOW"])],
      },
    };
  }

  return {
    ...decision,
    tier: "NO VIEW",
    verdict: "NO VIEW",
    freshness,
    decisionUsable: false,
    nonOwnerAction: "NO VIEW",
    ownerAction: "NO VIEW",
    action: "Expired live view. No new entry. Existing holders must use their previously stored invalidation until live data returns.",
    packet: {
      ...decision.packet,
      policyEligible: false,
      decisionUsable: false,
      orderExecutable: false,
      reasonCodes: [...new Set([...decision.packet.reasonCodes, `VIEW_${freshness}`])],
      blockers: [...new Set([...decision.packet.blockers, "CURRENT_LIVE_VIEW_UNAVAILABLE"])],
    },
  };
}

function projectedSummary(view: LiveDiscoveryView, decisions: LiveDiscoveryDecision[]) {
  const count = (tier: LiveDiscoveryDecision["tier"]) => decisions.filter((decision) => decision.tier === tier).length;
  const buy = decisions.filter((decision) => decision.tier === "S" && decision.nonOwnerAction === "BUY" && decision.decisionUsable).length;
  const providerNoView = Math.max(0, view.universe.eligible - view.universe.covered) + view.universe.unsupported;
  return [
    { label: "Buy now", value: String(buy), note: "fresh regular-session S only", tone: "cyan" as const },
    { label: "Wait / watch", value: String(count("A") + count("B") + count("FORMING")), note: "A / B / forming", tone: "default" as const },
    { label: "Avoid", value: String(count("AVOID")), note: "hard vetoes", tone: "amber" as const },
    { label: "No view", value: String(count("NO VIEW") + providerNoView), note: "missing current bar / unsupported", tone: "default" as const },
  ];
}

export function enforceViewFreshness(view: LiveDiscoveryView, now = new Date()): LiveDiscoveryView {
  let session = inferUsEquitySession(now);
  const officialTransition = view.marketNextTransitionAt ? new Date(view.marketNextTransitionAt) : null;
  if (view.session === "REGULAR"
    && officialTransition
    && Number.isFinite(officialTransition.getTime())
    && now >= officialTransition
    && ET_DATE.format(now) === ET_DATE.format(officialTransition)) {
    session = "CLOSED";
  }
  const freshness = classifyFreshness(view.barEndAt, session, now);
  const decisions = view.decisions.map((decision) => projectDecision(decision, session, freshness));
  return {
    ...view,
    session,
    sessionLabel: sessionLabel(session),
    freshness,
    connection: freshness === "LIVE" ? view.connection : freshness === "LAGGING" || freshness === "BASELINE" ? "DEGRADED" : freshness === "CLOSED" ? "DEGRADED" : "OFFLINE",
    etag: effectiveEtag(view.etag, session, freshness),
    decisions,
    summary: projectedSummary(view, decisions),
    backdrop: view.backdrop.map((item) => item.label === "Freshness"
      ? { ...item, value: freshness, detail: view.barEndAt ?? "no sealed bar", tone: freshness === "LIVE" || freshness === "BASELINE" || freshness === "CLOSED" ? "positive" : "warning" }
      : item),
    quality: {
      ...view.quality,
      flags: [...new Set([...view.quality.flags, freshness === "STALE" ? "VIEW_STALE" : `VIEW_${freshness}`])],
    },
  };
}

export function forceOfflineView(view: LiveDiscoveryView, now = new Date()): LiveDiscoveryView {
  const session = inferUsEquitySession(now);
  const closedFreshness = classifyFreshness(view.barEndAt, session, now);
  if (session === "CLOSED" && closedFreshness === "CLOSED" && view.dataMode === "live") {
    const decisions = view.decisions.map((decision) => projectDecision(decision, session, "CLOSED"));
    return {
      ...view,
      session,
      sessionLabel: sessionLabel(session),
      connection: "DEGRADED",
      freshness: "CLOSED",
      etag: effectiveEtag(view.etag, session, "CLOSED"),
      decisions,
      summary: projectedSummary(view, decisions),
      quality: {
        ...view.quality,
        flags: [...new Set([...view.quality.flags, "VIEW_CLOSED_FINAL_BAR"])],
      },
    };
  }
  if ((view.freshness === "BASELINE" || closedFreshness === "BASELINE") && session !== "REGULAR" && session !== "CLOSED" && view.dataMode === "live") {
    const decisions = view.decisions.map((decision) => projectDecision(decision, session, "BASELINE"));
    return {
      ...view,
      session,
      sessionLabel: sessionLabel(session),
      connection: "DEGRADED",
      freshness: "BASELINE",
      etag: effectiveEtag(view.etag, session, "BASELINE"),
      decisions,
      summary: projectedSummary(view, decisions),
      quality: {
        ...view.quality,
        flags: [...new Set([...view.quality.flags, "VIEW_REGULAR_SESSION_BASELINE"])],
      },
    };
  }
  const decisions = view.decisions.map((decision) => projectDecision(decision, session, "OFFLINE"));
  return {
    ...view,
    session,
    sessionLabel: sessionLabel(session),
    connection: "OFFLINE",
    freshness: "OFFLINE",
    etag: effectiveEtag(view.etag, session, "OFFLINE"),
    decisions,
    summary: projectedSummary(view, decisions),
    quality: {
      ...view.quality,
      flags: [...new Set([...view.quality.flags, "CLIENT_REFRESH_FAILED", "VIEW_OFFLINE"])],
    },
  };
}
