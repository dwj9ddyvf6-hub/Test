// tensor_research_hands.mjs — the Sable / Autopilot Edge paper hands (autopilot-desk src/lib/scanner/scout-hands.mjs
// planEdgeHands and its lineage doctrines, vendored byte-exact) for each named lineage's book.
//
// stdin  {books: [{lineage, parked: [...], desk, tensorReads, brief, candidates}]}
// stdout {ok, results: [{lineage, plan}]}
import { planEdgeHands } from "../vendor/foliotend_research/autopilot/scout-hands.mjs";
import { alwaysOnEdgePolicy, applyLineage, LINEAGES } from "../vendor/foliotend_research/autopilot/lineage.mjs";

const chunks = [];
for await (const chunk of process.stdin) chunks.push(chunk);
const request = JSON.parse(Buffer.concat(chunks).toString("utf8"));
const results = [];
for (const book of request.books || []) {
  const lineage = LINEAGES[book.lineage] || LINEAGES.ptj;
  // the always-on Edge policy under the named lineage, with its optional paper hands armed (the lane's switch)
  const policy = { ...applyLineage(alwaysOnEdgePolicy(), lineage), hands: "paper", parkedSymbols: book.parked || [] };
  const plan = planEdgeHands({ policy, brief: book.brief || {}, desk: book.desk || {}, tensorReads: book.tensorReads || [],
    candidates: book.candidates || [] });
  results.push({ lineage: lineage.id, plan });
}
process.stdout.write(JSON.stringify({ ok: true, lineages: Object.keys(LINEAGES), results }) + "\n");
