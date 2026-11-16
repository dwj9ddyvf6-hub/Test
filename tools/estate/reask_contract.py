#!/usr/bin/env python3
"""Validation-error reask contract, with cost stamped on the result (A-29).

Every local step that asks a model for structured output follows this
contract:
  - retry ONLY on schema or parse failure (ValidationFailure); any other
    error propagates immediately, unretried;
  - the validation error is fed back to the next call VERBATIM;
  - the loop is capped by attempts AND by a token budget; hitting either
    cap raises BudgetExhausted instead of retrying forever;
  - the returned envelope states attempts used and total cost, so a
    result never hides how expensive its own validation was.

The model is a callable: model(feedback) -> (raw, tokens_used), where
feedback is None on the first attempt and the verbatim validation error
afterwards. validate(raw) returns the parsed object or raises
ValidationFailure.

Usage: reask_contract.py selftest
"""
import sys

class ValidationFailure(Exception):
    """Schema or parse failure: the only retryable class."""

class BudgetExhausted(Exception):
    pass

def reask(model, validate, max_attempts=3, token_budget=100000):
    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")
    feedback = None
    total_tokens = 0
    errors = []
    for attempt in range(1, max_attempts + 1):
        raw, tokens = model(feedback)
        total_tokens += tokens or 0
        if total_tokens > token_budget:
            raise BudgetExhausted(
                f"token budget {token_budget} exceeded at attempt {attempt} ({total_tokens} tokens)")
        try:
            obj = validate(raw)
        except ValidationFailure as e:
            errors.append(str(e))
            feedback = str(e)  # verbatim into the next call
            continue
        return {"result": obj, "attempts": attempt, "total_tokens": total_tokens,
                "validation_errors": errors}
    raise BudgetExhausted(
        f"attempt cap {max_attempts} reached; last validation error: {errors[-1] if errors else 'none'}")

def selftest():
    seen_feedback = []
    state = {"n": 0}
    def flaky_model(feedback):
        seen_feedback.append(feedback)
        state["n"] += 1
        return ({"ok": state["n"] >= 3}, 100)
    def validate(raw):
        if not raw.get("ok"):
            raise ValidationFailure("schema: field 'ok' must be true (attempt payload invalid)")
        return {"value": 42}
    out = reask(flaky_model, validate)
    assert out["attempts"] == 3 and out["total_tokens"] == 300, out
    assert seen_feedback[0] is None and "field 'ok'" in seen_feedback[1], seen_feedback
    assert out["validation_errors"] and out["result"] == {"value": 42}, out
    calls = {"n": 0}
    def broken_model(feedback):
        calls["n"] += 1
        raise RuntimeError("transport down")
    try:
        reask(broken_model, validate)
        raise SystemExit("non-validation error must propagate")
    except RuntimeError:
        assert calls["n"] == 1, "non-validation error must not be retried"
    try:
        reask(lambda fb: ({"ok": False}, 10), validate, max_attempts=2)
        raise SystemExit("attempt cap must raise BudgetExhausted")
    except BudgetExhausted:
        pass
    try:
        reask(lambda fb: ({"ok": False}, 60000), validate, max_attempts=5, token_budget=100000)
        raise SystemExit("token budget must raise BudgetExhausted")
    except BudgetExhausted:
        pass
    print("SELFTEST PASS reask_contract: retries only on validation failure with verbatim feedback, attempts=3 and total_tokens=300 stamped, non-validation error unretried, attempt and token caps raise BudgetExhausted")
    return 0

if __name__ == "__main__":
    raise SystemExit(selftest() if len(sys.argv) > 1 and sys.argv[1] == "selftest" else print(__doc__))
