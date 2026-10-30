// SKETCH of a cloud failover ("standby") worker. Pseudocode-level JavaScript: adapt to your platform.
// Purpose: if the primary desk (your machine/VM) stops, a small scheduled cloud function still
// (a) exits positions that hit their risk exits and (b) optionally takes today's planned entries.
//
// Hard rules:
//  1. Trade ONLY when the primary heartbeat is stale (>= LOCK_MIN minutes) AND the market is open.
//  2. Use the SAME deterministic client_order_id scheme as the primary, so an overlap cannot double-order.
//  3. Never place an order that would overlap an existing live sell for the symbol.
//  4. Respect the platform's free-tier write quota (e.g. key-value writes/day): throttle heartbeat
//     writes, write the book only when it changed, probe a write before any live order and STAND DOWN if it fails.
//  5. Entries come from a PLAN the primary exported earlier ("plan for session YYYY-MM-DD"); refuse any plan
//     not dated for today's exchange date. The worker computes nothing the primary has not pre-decided.
//  6. Start in MODE=dry. Promote exits to live first, entries to live only after a clean dry day.
//  7. Mind CPU limits per invocation on free tiers; keep the plan small and decisions O(lots).

export default {
  async scheduled(event, env) {
    const hb = JSON.parse(await env.KV.get("heartbeat") || "null");
    const ageMin = hb ? (Date.now() - hb.epoch_ms) / 60000 : Infinity;
    if (ageMin < Number(env.LOCK_MIN || 10)) return;              // primary is alive: stand down
    if (!marketOpenNow()) return;
    if (env.MODE !== "live") return log("dry: would act", await decide(env));
    if (!(await kvWriteProbe(env))) return;                       // cannot record what I do: do nothing
    for (const intent of await decide(env)) {
      const cid = deterministicCid(intent);                      // same ids as the primary
      if (await brokerHasOrder(env, cid)) continue;               // idempotent
      await brokerSubmit(env, intent, cid);
    }
  },
};
// marketOpenNow, decide, kvWriteProbe, deterministicCid, brokerHasOrder, brokerSubmit: implement per broker.
