# Evidence-contract emitter pattern — adopted input (Codex, 2026-10-28B)

Status: SPECCED FOR BUILD. This is an adopted-input note, not a build.
Source: Codex commit 3484d58a18 (STRONG in CODEX-NEW-20261028B), the
option lab's migration to the evidence contract.

## Adopted pattern

1. **Cross-runtime SHA-256.** Contract hashing uses a cross-runtime
   sha256Hex (WebCrypto, with node:crypto webcrypto fallback) so a
   browser emitter and a Node emitter produce identical hashes. Our
   Morning Map emitter is Python today; any future JS emitter in the
   lineup uses this pattern instead of a Node-only createHash import.
   Completing proof named: the sha256("abc") vector
   ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad
   asserted in the emitter's fixture suite (the same vector Codex's
   fixture asserts, recomputed independently in the 20261028B analysis).
2. **Stable observation IDs, async with a version bump.** The stable-ID
   derivation string is unchanged, but the function becomes async under
   WebCrypto. NOT adopted in place: any lineup port ships with a
   version bump, never as a silent signature change, because a sync
   consumer of an async ID gets undefined at runtime.
3. **Record shape for user-scenario emissions.** See the Payoff Sketch
   (tool 6) adopted-input note in LINEUP-DESIGN-2026-10-28.md: inferred
   state, all five clocks explicitly absent with named reasons,
   implementation / parameters / result SHA-256 lineage, eligibility
   assessed and blockers rendered.

## Non-claims

No lineup tool emits this pattern yet beyond the Morning Map Python
contract block adopted in the prior round. This spec adopts the
pattern for the next emitter build; it does not claim any tool
already conforms to it.
