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
