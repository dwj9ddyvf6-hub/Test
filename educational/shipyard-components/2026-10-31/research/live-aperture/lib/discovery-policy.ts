export type DiscoveryPolicyInput = {
  quality: "VALID" | "INVALID";
  qualityBlockers?: string[];
  hardVetoes?: string[];
  triggerState: "NONE" | "APPROACH" | "SEED" | "CONFIRMED" | "FAILED" | "EXPIRED";
  triggerFresh: boolean;
  insideEntryZone: boolean;
  anchor: "PASS" | "WATCH" | "HARD AVOID" | "NO VIEW";
  formation: "REVERSAL SEED" | "ROTATION SEED" | "BUILDING" | "ESTABLISHED" | "MATURE" | "FAILED" | "NO VIEW";
  topology: "TAILWIND" | "IDIOSYNCRATIC LEADER" | "DECOUPLING" | "NEUTRAL" | "HEADWIND" | "NO VIEW";
  participation: "CONFIRMED" | "EARLY" | "MIXED" | "DISTRIBUTION" | "NO VIEW";
  rewardRisk: number | null;
  belowChaseLine: boolean;
  levelsComplete: boolean;
  targetAlreadyTraded: boolean;
  proof: "SUPPORTED" | "MIXED" | "OBSERVING" | "INSUFFICIENT" | "REJECTED" | "QUARANTINED";
  /**
   * Operational controls are deliberately independent of setup quality.
   * Omitted controls fail closed so research fixtures can never become live
   * execution candidates merely because they satisfy the policy gates.
   */
  shadowOnly?: boolean;
  executionAuthority?: "NONE" | "ORDER_AUTHORIZED";
};

export type DiscoveryPolicyDecision = {
  tier: "S" | "A" | "B" | "FORMING" | "AVOID" | "NO VIEW";
  verdict: "BUY NOW" | "WAIT" | "AVOID" | "NO VIEW";
  policyEligible: boolean;
  executionEligible: boolean;
  reasonCodes: string[];
  blockers: string[];
};

const earlyFormations = new Set(["REVERSAL SEED", "ROTATION SEED", "BUILDING"]);
const positiveTopology = new Set(["TAILWIND", "IDIOSYNCRATIC LEADER"]);

function stoppedDecision(
  tier: "FORMING" | "AVOID" | "NO VIEW",
  verdict: "WAIT" | "AVOID" | "NO VIEW",
  reasonCodes: string[],
  blockers: string[],
): DiscoveryPolicyDecision {
  return { tier, verdict, policyEligible: false, executionEligible: false, reasonCodes, blockers };
}

function proofBlocker(proof: DiscoveryPolicyInput["proof"]): string {
  return `PROOF_${proof.replaceAll(" ", "_")}`;
}

/**
 * Frozen policy boundary for the standalone scanner.
 *
 * This function is intentionally ordinal and deterministic: data failure wins
 * first, then hard vetoes, then trigger lifecycle, then S/A/B qualification.
 * It does not use a blended 0–100 score or an LLM-generated probability.
 */
export function classifyDiscovery(input: DiscoveryPolicyInput): DiscoveryPolicyDecision {
  const reasonCodes: string[] = [];
  const blockers: string[] = [];

  // Proof quarantine and rejection are terminal states. Their ordering is
  // explicit so neither can fall through into a visually attractive tier.
  if (input.proof === "QUARANTINED") {
    blockers.push(...(input.qualityBlockers?.length ? input.qualityBlockers : ["PROOF_QUARANTINED"]));
    return stoppedDecision("NO VIEW", "NO VIEW", ["PROOF_QUARANTINED"], [...new Set(blockers)]);
  }

  if (input.proof === "REJECTED") {
    return stoppedDecision("AVOID", "AVOID", ["PROOF_REJECTED"], ["PROOF_REJECTED"]);
  }

  if (input.quality !== "VALID" || input.anchor === "NO VIEW" || input.formation === "NO VIEW" || input.topology === "NO VIEW" || input.participation === "NO VIEW") {
    blockers.push(...(input.qualityBlockers?.length ? input.qualityBlockers : ["MANDATORY_INPUT_UNAVAILABLE"]));
    return stoppedDecision("NO VIEW", "NO VIEW", ["DATA_INTEGRITY_STOP"], blockers);
  }

  const hardVetoes = [...(input.hardVetoes ?? [])];
  if (input.anchor === "HARD AVOID") hardVetoes.push("ANCHOR_HARD_AVOID");
  if (input.formation === "MATURE") hardVetoes.push("FORMATION_MATURE");
  if (input.formation === "FAILED") hardVetoes.push("FORMATION_FAILED");
  if (input.topology === "HEADWIND") hardVetoes.push("TOPOLOGY_HEADWIND");
  if (input.participation === "DISTRIBUTION") hardVetoes.push("PARTICIPATION_DISTRIBUTION");
  if (!input.levelsComplete) hardVetoes.push("LEVELS_INCOMPLETE");
  if (!input.belowChaseLine) hardVetoes.push("CHASE_LINE_BREACHED");
  if (input.targetAlreadyTraded) hardVetoes.push("TARGET_ALREADY_TRADED");
  if (input.rewardRisk !== null && input.rewardRisk < 1.25) hardVetoes.push("REWARD_RISK_BELOW_1_25");
  if (input.triggerState === "FAILED" || input.triggerState === "EXPIRED") hardVetoes.push(`TRIGGER_${input.triggerState}`);

  if (hardVetoes.length) {
    return stoppedDecision("AVOID", "AVOID", ["HARD_VETO"], [...new Set(hardVetoes)]);
  }

  if (input.triggerState === "NONE" || input.triggerState === "APPROACH") {
    return stoppedDecision("FORMING", "WAIT", ["TRIGGER_NOT_CONFIRMED"], ["NO_COMPLETED_TRIGGER"]);
  }

  // A stale seed or confirmation is historical evidence, not a current
  // decision. It cannot be rescued by otherwise positive context.
  if (!input.triggerFresh) {
    return stoppedDecision("FORMING", "WAIT", ["TRIGGER_STALE"], ["TRIGGER_FRESHNESS_FAILED"]);
  }

  const formationEarly = earlyFormations.has(input.formation);
  const topologyPositive = positiveTopology.has(input.topology);
  const sPass = input.triggerState === "CONFIRMED"
    && input.triggerFresh
    && input.insideEntryZone
    && input.anchor === "PASS"
    && formationEarly
    && topologyPositive
    && input.participation === "CONFIRMED"
    && input.rewardRisk !== null
    && input.rewardRisk >= 2
    && input.proof === "SUPPORTED";

  if (sPass) {
    reasonCodes.push("TRIGGER_CONFIRMED", "ANCHOR_PASS", "FORMATION_EARLY", "TOPOLOGY_POSITIVE", "PARTICIPATION_CONFIRMED", "REWARD_RISK_PASS");
    const policyEligible = true;
    const shadowOnly = input.shadowOnly !== false;
    const hasExecutionAuthority = input.executionAuthority === "ORDER_AUTHORIZED";

    if (shadowOnly) blockers.push("SHADOW_ONLY");
    if (!hasExecutionAuthority) blockers.push("NO_EXECUTION_AUTHORITY");

    return {
      tier: "S",
      verdict: "BUY NOW",
      policyEligible,
      executionEligible: policyEligible && !shadowOnly && hasExecutionAuthority,
      reasonCodes,
      blockers,
    };
  }

  const contextNotNegative = input.topology !== "HEADWIND"
    && input.topology !== "DECOUPLING"
    && input.participation !== "DISTRIBUTION"
    && input.participation !== "MIXED";
  const atLeastOneContextPositive = topologyPositive || input.participation === "CONFIRMED";
  const aPass = input.triggerState === "CONFIRMED"
    && input.anchor === "PASS"
    && formationEarly
    && contextNotNegative
    && atLeastOneContextPositive
    && input.rewardRisk !== null
    && input.rewardRisk >= 2;

  if (aPass) {
    blockers.push(input.proof === "SUPPORTED" ? "ONE_CONTEXT_FAMILY_UNCONFIRMED" : proofBlocker(input.proof));
    return { tier: "A", verdict: "WAIT", policyEligible: false, executionEligible: false, reasonCodes: ["CONFIRMED_CONDITIONAL"], blockers };
  }

  const bPass = (input.triggerState === "SEED" || input.triggerState === "CONFIRMED")
    && (input.anchor === "PASS" || input.anchor === "WATCH")
    && formationEarly
    && contextNotNegative
    && atLeastOneContextPositive
    && input.rewardRisk !== null
    && input.rewardRisk >= 1.5;

  if (bPass) {
    blockers.push(input.triggerState === "SEED" ? "TRIGGER_SEED_ONLY" : "GESTALT_INCOMPLETE");
    return { tier: "B", verdict: "WAIT", policyEligible: false, executionEligible: false, reasonCodes: ["WATCHLIST_QUALIFIED"], blockers };
  }

  return stoppedDecision("FORMING", "WAIT", ["FORMATION_INCOMPLETE"], ["NO_ACTIONABLE_CLASSIFICATION"]);
}
