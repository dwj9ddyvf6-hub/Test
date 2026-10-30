# Narrow network activation guide

Status: not activated. The engine's original preflight correctly detected an enforced host restriction. No HTTP request occurred in that failed engine probe, and no policy was bypassed. Existing previously captured data can be imported without claiming outbound collection.

## Supported operator step

Open Settings → Codex Cloud → Environments, edit the intended environment, and review Additional allowed domains. For the initial non-Cboe sources, the narrowly required hosts are:

- www.federalreserve.gov
- www.frbsf.org
- wikimedia.org

Do not enable unrestricted public access merely to run this package. Save and republish the reviewed configuration, then start a new task and verify each permitted GET, parser, persistence and repeat-collection path. Existing tasks retain their own state. Workspace Agent Security requirements may also apply; environment configuration cannot override them.

Source permission is separate from network reachability. Cboe stays gated pending its reviewed canonical endpoint and applicable use rights. Wikimedia requires an identifying public project-contact User-Agent; no private email is needed. A host approval does not authorize arbitrary redistribution or paid subscriptions.

The available tools in this session did not expose an environment-network settings write operation. The operator or administrator must perform that reviewed change; no credentials or account settings were created.

Official documentation: https://learn.chatgpt.com/docs/environments/cloud-environments#connect-to-services

## Acceptance evidence after approval

1. Record configuration version and exact approved host; retain no secret values.
2. Run one bounded source request and record attempt, status, timestamps and response hash.
3. Validate schema, observation clocks, units, rights and source-specific freshness.
4. Repeat collection, proving unchanged items are idempotent and new items do not collide.
5. Restart and restore the private local store; verify journal/observation counts and known snapshot.
6. Only then authorize the intended persistent operating schedule and monitor its actual health.

No uptime, future scheduler wake or forecast accuracy is established by a successful setup probe.
