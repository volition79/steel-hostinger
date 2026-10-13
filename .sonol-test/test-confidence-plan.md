# Scoped implementation validation

Approved: CodeMap off, Sonol Test scoped, policy pack absent. No VPS mutation or publication.

New boundaries and rationale:
- Compose inline gateway: standalone URL import with no relative files. Generator contract assertion.
- Authentication covers UI/API/WS: runtime unauthenticated requests must return 401.
- HTTPS DOMAIN and USE_SSL: browser-generated URLs must use public secure origin. Runtime viewer test and source contract.
- No published control ports: network isolation contract assertion.
- Upstream paths: /v1, /api, /ws and root CDP tested with actual Steel, not just string matching.
- Persistent volumes: auth hash, logs/exports/cache; website login persistence unproven.
- Existing Buzz: separate directory and local Docker project; no changes or deployment.

Direct test evidence is recorded in VERIFICATION.md. No full-chain confidence or Hostinger release gate is claimed.

## Follow-up implementation scope

Environment-empty import parsing, runtime hostname validation, generated/preserved authentication,
API+Chromium readiness, dedicated profile persistence and exclusive ownership, memory limits,
aggregate request limiting, and bilingual recovery/update instructions.

Use real local Docker tests for authentication lifecycle, forced container recreation, unique-cookie
readback, concurrent profile-owner rejection, crash recovery and 429 enforcement. Keep Hostinger
import/Traefik issuance as explicit unverified boundaries. No VPS mutation or publication in this scope.

## AUTO-01 automatic Hostinger setup (2026-10-13)

Target: Linux Hostinger Docker Manager plus running Traefik, with or without Buzz.
Authoring: Windows/WSL local checkout. CodeMap off; scoped source/runtime verification.
New reason: bootstrap.py derives verified Hostinger DNS and routing, writes only own gateway
labels/network, preserves volumes, and never accepts arbitrary Docker commands from HTTP.
New reason: auto Compose distributes a dedicated isolated helper; browser/UI never get Docker socket.
Reviewed: existing manual Compose and authentication/browser lifecycle remain available and tested.
Generated Compose follows the generator; doc changes explain optional Steel, prerequisites and gaps.
Required: absent Buzz, ambiguous/missing proxy/domain, host/bridge network, immutable saved identity,
no changes outside own gateway, interrupted apply retry, actual empty-env Compose and local runtime.
Unresolved: real hPanel Open selection, public ACME, Hostinger first-deploy timing remain VPS acceptance.

## Authorized publication

User requested publication, retaining VPS installation/testing for themselves.
Scope: publish source and bootstrap image, verify anonymous image and immutable raw Compose access.
No VPS mutation. Existing local runtime evidence remains scoped; Hostinger acceptance remains pending.

## DNS-02 Hostinger loopback resolver correction

User authorized fixing the observed dns_mismatch and publishing a corrected installer.
CodeMap off; Sonol Test scoped; no policy pack. VPS remains user-operated.
Observed: generated hostname and Buzz resolve to public A/AAAA, base srv hostname resolves to 127.0.1.1 inside Docker.
Change: only a mismatching loopback base triggers HTTPS public DNS checks of both names; no DNS bypass.
Keep ordinary local equality unchanged and reject genuine mismatches, failed/malformed public responses,
non-public fallback addresses and unexpected local addresses. Log address-only diagnostics (no credentials).
Validate regression cases, actual container with base hostname overridden to loopback, image/source parity,
anonymous pull and raw installer verification. Existing volumes and routing code are unchanged.

## LOGIN-03 password-only browser login

User requested a dedicated login page with automatic username and bilingual password retrieval instructions.
Existing approved scope: CodeMap off; scoped tests; no policy pack, no VPS mutation.
New boundary: private login service uses read-only existing htpasswd; opaque HttpOnly/Secure/SameSite cookie;
nginx auth_request protects UI/API/WebSocket and preserves explicit Basic authentication for tools.
Runtime sessions expire after 12h and invalidate on password hash change or login-service restart.
Test bilingual/project escaping, bad password, cookie flags, origin checks, authenticated API and real WebSocket,
password-change invalidation, anonymous API denial, no native browser prompt and desktop/mobile rendering.
