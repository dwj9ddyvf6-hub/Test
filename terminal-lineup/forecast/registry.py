"""Family registry loader/validator for the Forecast Engines 30 program.

The registry (registry.json, beside this module) assigns every input of
every engine to exactly one evidence family, records each engine's
forecast form, horizons, grading rule id, kill criterion, proving
threshold and state, and carries the C14 defect-tagged sources.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PATH = os.path.join(HERE, "registry.json")


# Edge card fields (DEEP-PASS 3.2 item 3): the language strengthening
# fields every engine's registry entry must carry, alongside the
# proving threshold and grading rule id it already carries. Wording
# is authored per engine in registry.json from FORECAST-ENGINES-30.md;
# a field that is absent or empty fails validation, so no engine's
# claim can travel without naming who pays, where it breaks, whether
# it can be held, what execution leaves, and which price aware
# baseline it must beat.
EDGE_CARD_FIELDS = ("payer", "bad_state", "holdability_and_co_losses",
                    "execution_net", "price_aware_baseline")

# Calibration attestation (DEEP-PASS 3.2 item 5): the publishing
# gate's registry field. Every engine carries the field; null means
# not attested, and the engine's numbers may then be published only
# as uncalibrated scores, never as probabilities. A non-null
# attestation must be complete: status calibrated_out_of_sample, a
# stated basis, and an attested_on date. A partial attestation is
# refused at load, so the gate can never be half opened by a
# malformed entry.
ATTESTATION_FIELD = "calibration_attestation"
ATTESTATION_OK = "calibrated_out_of_sample"


# Aperture proof gate rule (DEEP-PASS 3.2 item 2): the episode
# rule is frozen per engine in the registry, not per scan. An
# engine that carries proof_gate_rule must carry the complete
# rule, the state language must be provisional, the multiple
# testing correction must be Benjamini-Hochberg over the scanned
# universe, and the forward check must name its ledger engine
# and horizon. A partial or altered rule fails validation, so
# no scan can quietly loosen the gate that lets a name print
# SUPPORTED.
PROOF_GATE_RULE_SECTIONS = ("entry_condition", "episode", "split",
                            "thresholds", "multiple_testing",
                            "forward_check")


def _validate_proof_gate_rule(eng):
    rule = eng.get("proof_gate_rule")
    if rule is None:
        return
    if not isinstance(rule, dict) or not str(rule.get("id") or "").strip():
        raise RegistryError(
            f"engine {eng['id']} carries a malformed proof_gate_rule "
            f"(needs an id)")
    if rule.get("state_language") != "provisional":
        raise RegistryError(
            f"engine {eng['id']} proof_gate_rule state language must "
            f"be provisional: an in sample proof state may never be "
            f"registered as proven")
    for section in PROOF_GATE_RULE_SECTIONS:
        if not isinstance(rule.get(section), dict) or not rule[section]:
            raise RegistryError(
                f"engine {eng['id']} proof_gate_rule missing section "
                f"{section}")
    mt = rule["multiple_testing"]
    if mt.get("method") != "benjamini_hochberg" \
            or mt.get("scope") != "scanned_universe":
        raise RegistryError(
            f"engine {eng['id']} proof_gate_rule multiple testing "
            f"must be benjamini_hochberg across the scanned universe")
    alpha = mt.get("alpha")
    if not isinstance(alpha, (int, float)) or not 0 < alpha < 1:
        raise RegistryError(
            f"engine {eng['id']} proof_gate_rule alpha must lie "
            f"in (0, 1)")
    fc = rule["forward_check"]
    if not str(fc.get("ledger_engine_id") or "").strip() \
            or not isinstance(fc.get("horizon_sessions"), int) \
            or fc["horizon_sessions"] <= 0 \
            or not str(fc.get("quantity") or "").strip():
        raise RegistryError(
            f"engine {eng['id']} proof_gate_rule forward check must "
            f"name a ledger engine, a positive horizon and a quantity")
    th = rule["thresholds"]
    for field in ("supported_min_episodes", "train_hit_rate_min",
                  "train_median_min", "holdout_hit_rate_min",
                  "holdout_median_min", "mixed_min_episodes"):
        if th.get(field) is None:
            raise RegistryError(
                f"engine {eng['id']} proof_gate_rule thresholds "
                f"missing {field}")


class RegistryError(Exception):
    pass


class Registry:
    def __init__(self, path=DEFAULT_PATH):
        with open(path, "r", encoding="utf-8") as fh:
            self.data = json.load(fh)
        self.path = path
        self.families = {f["id"]: f for f in self.data["families"]}
        self.engines = {e["id"]: e for e in self.data["engines"]}
        self.rules = {r["id"]: r for r in self.data["grading_rules"]}
        self.validate()

    def validate_family(self, family_id):
        if family_id not in self.families:
            raise RegistryError(f"unregistered evidence family: {family_id!r}")

    def validate_engine(self, engine_id):
        if engine_id not in self.engines:
            raise RegistryError(f"unregistered engine: {engine_id!r}")
        return self.engines[engine_id]

    def edge_card(self, engine_id):
        eng = self.validate_engine(engine_id)
        return eng["edge_card"]

    def calibration_attestation(self, engine_id):
        eng = self.validate_engine(engine_id)
        return eng[ATTESTATION_FIELD]

    def proof_gate_rule(self, engine_id):
        eng = self.validate_engine(engine_id)
        rule = eng.get("proof_gate_rule")
        if rule is None:
            raise RegistryError(
                f"engine {engine_id} carries no frozen proof gate rule")
        return rule

    def research_questions(self):
        return {r["id"]: r for r in self.data.get("research_questions", [])}

    def grading_convention(self, engine_id):
        """The engine's registered grading convention (RC-19 cure,
        2026-10-30), or None when the engine's issued values and
        the shared resolver already share a scale. A convention
        records the issued value scale, the realised scale, the
        resolver kind that produces it, the legacy kind map for
        rows issued before the convention, its effective date,
        and the outstanding rows it affects."""
        eng = self.validate_engine(engine_id)
        return eng.get("grading_convention")

    def grading_rule(self, engine_id):
        eng = self.validate_engine(engine_id)
        if eng["grading_rule_id"] not in self.rules:
            raise RegistryError(
                f"engine {engine_id} names unregistered grading rule "
                f"{eng['grading_rule_id']!r}")
        return self.rules[eng["grading_rule_id"]]

    def validate(self):
        """Structural law: every engine complete; every input in exactly
        one family; every family used is registered; defect sources tagged."""
        required = ("id", "number", "name", "forecast_form", "horizons",
                    "grading_rule_id", "kill_criterion", "proving_threshold",
                    "state", "inputs")
        for eng in self.data["engines"]:
            for field in required:
                if field not in eng or eng[field] in (None, "", []):
                    raise RegistryError(
                        f"engine {eng.get('id')} missing field {field}")
            if ATTESTATION_FIELD not in eng:
                raise RegistryError(
                    f"engine {eng['id']} missing field "
                    f"{ATTESTATION_FIELD}")
            att = eng[ATTESTATION_FIELD]
            if att is not None:
                # Two complete forms (RC-22 cure, 2026-10-30): the
                # calibrated form that opens the probability gate,
                # and an explicit not_attested record built from the
                # engine's own graded record (status not_attested, a
                # stated basis, a recorded_on date). The not_attested
                # form never opens the gate: grading.
                # calibration_attestation returns None for it.
                is_calibrated = isinstance(att, dict) \
                    and att.get("status") == ATTESTATION_OK \
                    and str(att.get("basis") or "").strip() \
                    and str(att.get("attested_on") or "").strip()
                is_not_attested = isinstance(att, dict) \
                    and att.get("status") == "not_attested" \
                    and str(att.get("basis") or "").strip() \
                    and str(att.get("recorded_on") or "").strip()
                if not (is_calibrated or is_not_attested):
                    raise RegistryError(
                        f"engine {eng['id']} carries a malformed "
                        f"calibration attestation (needs status "
                        f"{ATTESTATION_OK} with a stated basis and "
                        f"an attested_on date, or status not_attested "
                        f"with a stated basis and a recorded_on date, "
                        f"or null)")
            conv = eng.get("grading_convention")
            if conv is not None:
                if not isinstance(conv, dict):
                    raise RegistryError(
                        f"engine {eng['id']} carries a malformed "
                        f"grading_convention (needs a record)")
                for field in ("id", "effective_date",
                              "issued_value_scale", "realised_scale",
                              "resolver_kind",
                              "affected_outstanding"):
                    if conv.get(field) in (None, "", []):
                        raise RegistryError(
                            f"engine {eng['id']} grading_convention "
                            f"missing field {field}")
                aff = conv["affected_outstanding"]
                if not isinstance(aff, dict) \
                        or not isinstance(aff.get("count"), int) \
                        or not str(aff.get("named_in") or "").strip():
                    raise RegistryError(
                        f"engine {eng['id']} grading_convention "
                        f"affected_outstanding must carry a count "
                        f"and the record that names the rows")
            _validate_proof_gate_rule(eng)
            card = eng.get("edge_card")
            if not isinstance(card, dict):
                raise RegistryError(
                    f"engine {eng['id']} missing edge_card")
            for field in EDGE_CARD_FIELDS:
                if not isinstance(card.get(field), str) \
                        or not card[field].strip():
                    raise RegistryError(
                        f"engine {eng['id']} edge card missing field "
                        f"{field}")
            if eng["grading_rule_id"] not in self.rules:
                raise RegistryError(
                    f"engine {eng['id']} grading rule not registered")
            seen = {}
            for inp in eng["inputs"]:
                self.validate_family(inp["family"])
                if inp["name"] in seen:
                    raise RegistryError(
                        f"engine {eng['id']} input {inp['name']!r} assigned "
                        f"twice (must be exactly one family)")
                seen[inp["name"]] = inp["family"]
        for eng in self.data["engines"]:
            rule = eng.get("proof_gate_rule")
            if rule is not None and rule["forward_check"][
                    "ledger_engine_id"] not in self.engines:
                raise RegistryError(
                    f"engine {eng['id']} proof_gate_rule forward check "
                    f"names unregistered ledger engine "
                    f"{rule['forward_check']['ledger_engine_id']!r}")
        # Research questions (DEEP-PASS 3.2 item 15): the new
        # territory FE entries. They are registry entries, not
        # engines: each carries its question or form, its data
        # routes with an honest status, and its decision rule.
        # A conditioner must name engines that exist; an input
        # form must name the engine it applies to and its fields.
        # Nothing here issues a forecast, so no entry may carry
        # an engine's grading fields as if it were gradeable.
        rq_seen = set()
        for rq in self.data.get("research_questions", []):
            for field in ("id", "source_fe", "kind", "name",
                          "statement", "data_routes",
                          "decision_rule", "state"):
                if field not in rq or rq[field] in (None, "", []):
                    raise RegistryError(
                        f"research question {rq.get('id')} missing "
                        f"field {field}")
            if rq["id"] in rq_seen:
                raise RegistryError(
                    f"research question {rq['id']} registered twice")
            rq_seen.add(rq["id"])
            if rq["kind"] not in ("research_question", "conditioner",
                                  "input_form"):
                raise RegistryError(
                    f"research question {rq['id']} has unknown kind "
                    f"{rq['kind']!r}")
            for rt in rq["data_routes"]:
                self.validate_family(rt["family"])
                if rt.get("status") not in ("existing", "partial",
                                            "absent"):
                    raise RegistryError(
                        f"research question {rq['id']} route "
                        f"{rt.get('name')!r} has unregistered status "
                        f"{rt.get('status')!r}")
            if rq["kind"] == "conditioner":
                targets = rq.get("target_engine_ids") or []
                if not targets:
                    raise RegistryError(
                        f"conditioner {rq['id']} names no target "
                        f"engines")
                for tid in targets:
                    self.validate_engine(tid)
            if rq["kind"] == "input_form":
                self.validate_engine(rq.get("applies_to_engine_id"))
                if not rq.get("form_fields"):
                    raise RegistryError(
                        f"input form {rq['id']} carries no fields")
        for src in self.data.get("defect_sources", []):
            if "defect" not in (src.get("tags") or []):
                raise RegistryError(
                    f"defect source {src.get('id')} is not defect-tagged")
        return True


def load(path=DEFAULT_PATH):
    return Registry(path)
