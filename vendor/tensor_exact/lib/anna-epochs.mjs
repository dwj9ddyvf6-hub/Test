/**
 * Canonical Anna epoch registry.
 *
 * Engine epochs describe creator-disclosed changes to the private signal
 * system. Template epochs describe visible chart/layout and reconstructed
 * parameter-profile changes. They are separate axes and must never be used as
 * interchangeable labels.
 */

export const ANNA_ENGINE_EPOCHS = Object.freeze([
  {
    id: "engine_pre_upgrade",
    startsAt: null,
    endsBefore: "2026-04-11T06:17:10.000Z",
    evidenceStatus: "bounded_known_by_date",
  },
  {
    id: "engine_blue_early_v1",
    startsAt: "2026-04-11T06:17:10.000Z",
    endsBefore: "2026-04-19T02:15:10.000Z",
    evidenceStatus: "creator_disclosed_upgrade",
  },
  {
    id: "engine_upgraded_99_v2",
    startsAt: "2026-04-19T02:15:10.000Z",
    endsBefore: null,
    evidenceStatus: "creator_disclosed_mostly_scripted",
  },
]);

export const ANNA_TEMPLATE_EPOCHS = Object.freeze([
  {
    id: "E0_INITIAL",
    startsOn: "0000-01-01",
    squeezeLength: 14,
    squeezeMomentumLength: 9,
    basis: "initial visible template",
  },
  {
    id: "E1_EARLIER_BUY",
    startsOn: "2026-04-11",
    squeezeLength: 14,
    squeezeMomentumLength: 9,
    basis: "earlier weak-buy disclosure",
  },
  {
    id: "E2_DECLUSTERED",
    startsOn: "2026-04-16",
    squeezeLength: 14,
    squeezeMomentumLength: 9,
    basis: "declustered signal display",
  },
  {
    id: "E3_DCB_POLICY",
    startsOn: "2026-04-27",
    squeezeLength: 14,
    squeezeMomentumLength: 9,
    basis: "manual DCB policy disclosure",
  },
  {
    id: "E4_SEVEN_PANEL",
    startsOn: "2026-05-22",
    squeezeLength: 20,
    squeezeMomentumLength: 10,
    basis: "seven-panel template",
  },
  {
    id: "E5_CONSOLIDATED",
    startsOn: "2026-07-26",
    squeezeLength: 20,
    squeezeMomentumLength: 10,
    basis: "consolidated script template",
  },
]);

export function classifyAnnaEngineEpoch(authoredAt) {
  const timestamp = Date.parse(String(authoredAt ?? ""));
  if (!Number.isFinite(timestamp)) return "epoch_unassigned";
  let selected = ANNA_ENGINE_EPOCHS[0];
  for (const epoch of ANNA_ENGINE_EPOCHS) {
    if (
      epoch.startsAt !== null &&
      timestamp >= Date.parse(epoch.startsAt)
    ) {
      selected = epoch;
    }
  }
  return selected.id;
}

export function classifyAnnaTemplateEpoch(dateKey) {
  const normalized = /^\d{4}-\d{2}-\d{2}$/.test(String(dateKey ?? ""))
    ? String(dateKey)
    : null;
  if (!normalized) return ANNA_TEMPLATE_EPOCHS[0];
  let selected = ANNA_TEMPLATE_EPOCHS[0];
  for (const epoch of ANNA_TEMPLATE_EPOCHS) {
    if (normalized >= epoch.startsOn) selected = epoch;
  }
  return selected;
}

