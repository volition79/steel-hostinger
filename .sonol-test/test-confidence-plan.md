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
