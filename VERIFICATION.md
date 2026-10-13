# Verification — 2026-10-13

Scope: standalone Steel package. Existing Buzz and Hostinger VPS were not modified.

## Passed locally

- Five package contract tests: generated YAML parity, routed/authenticated boundary, secure URL settings, hostname validation, readiness/profile configuration.
- Docker Compose parses with an empty environment. This proves Compose parsing only, not Hostinger import. Missing STEEL_HOST intentionally blocks initialization with an actionable message.
- Actual pinned Steel API/UI and authenticated Nginx gateway run on Docker Desktop Linux containers, with a local self-signed TLS terminator.
- Unauthenticated UI/API/viewer/WebSocket requests and wrong credentials return 401.
- Both `/v1/sessions` and `/api/v1/sessions` work; generated viewer/CDP URLs use HTTPS/WSS.
- Authenticated root CDP navigation, real viewer frames, canvas clicks and keyboard input pass before and after forced API/gateway recreation.
- Authentication initializes a random password once, preserves an existing hash when no override is set, rejects short/overlong/multiline passwords and invalid hostnames without replacing the hash, and applies a valid explicit replacement.
- Chromium's actual readiness endpoint is checked along with API health. During development, API health alone returned 200 even when Chromium was blocked by a stale profile lock. The wrapper now obtains an exclusive profile lock before removing exactly three stale Chromium singleton paths.

- A second container using the same profile is rejected with exit 73; the running owner's SingletonLock is unchanged.
- A fresh random cookie value survives forced API container recreation after a 35-second disk-write wait.

- The same committed random cookie survives SIGKILL followed by API startup.
- A 240-request unauthenticated burst returns 92 responses with 401 and 148 with 429, proving the aggregate rate gate is active.

## Reproduction

Python 3, PyYAML, Playwright with Chromium, Docker Compose, and OpenSSL are required.

```sh
python3 -m unittest discover -s tests -v
python3 tests/auth_smoke.py
python3 tests/run_local.py
python3 tests/recovery_smoke.py
```

Set STEEL_TEST_DOCKER to the Docker executable for the recovery test. Run these sequentially.
The integration tests use only `steel-package-test` and localhost port 18443.
Disposable secrets and certificates are under ignored `.local/`; test containers are stopped afterwards and volumes retained for diagnosis.
Self-signed TLS verification is disabled only in local test processes, not shipped configuration.
Cookie tests wait 35 seconds for Chromium's batched disk writes. They do not guarantee survival of changes immediately preceding a crash, session-only cookies, or website-issued authentication expiry.

## Remaining validation

- Hostinger URL import, Open-button discovery, wildcard DNS and Let's Encrypt issuance still require a real VPS test. Local Compose parsing and TLS forwarding do not prove these.
- Mobile interaction, DevTools UI, file uploads/downloads and long-duration workloads are not certified by this smoke test.
- Buzz browser-tool integration is not included.
- A healthcheck becoming unhealthy does not itself cause Docker to restart a container.
- Profile volumes must not be shared with unrelated or older containers that bypass this package's ownership lock.

Scoped direct evidence only; no full Sonol release-gate certification is claimed.

## Automatic setup follow-up

- Twelve scoped unit/contract tests pass, including no-Buzz discovery, host/bridge network selection, environment-form Traefik configuration, disabled provider rejection, ambiguity/collision rejection and preservation of unrelated services.
- Real local Docker fixture (no Buzz): bootstrap starts the official Steel services, discovers a synthetic Hostinger hostname from Traefik, modifies its actual Compose file, and attaches gateway to the proxy network while preserving the default network.
- Real Traefik forwards HTTPS: unauthenticated requests return 401; a generated first-install password allows Steel API access; generated public URLs contain the discovered hostname.
- Re-running bootstrap exits successfully and preserves the gateway container ID.
- Fixture DNS and certificates are synthetic. Host-mode selection is unit-tested; the real forwarding fixture uses bridge networking. Public ACME and Hostinger deployment/Open are still unverified.
- Bootstrap publication: GitHub Actions run 38356917229 succeeded. Anonymous GHCR manifest access returned HTTP 200. compose.auto.yaml now references the published immutable helper digest. VPS acceptance remains pending.

- Published image verification: real Docker pull with an empty authentication config succeeded; embedded bootstrap.py SHA256 matches source; bundled Docker Compose v2.40.3 runs. Generated automatic file matches generator and parses with no user environment variables.

## DNS loopback incident fix (2026-10-13)

User VPS evidence showed the base hostname resolving to 127.0.1.1 while the generated hostname resolves to public A/AAAA. The old exact local-set comparison blocked initialization.
Twenty scoped tests now pass. A real read-only Docker helper container with the base hostname overridden to 127.0.1.1 successfully verified both public names through HTTPS DNS. Local IPv4-only resolution is accepted only as a subset of the matching public A/AAAA records. Genuine mismatches and unavailable/malformed public DNS remain blocked. Routing, credentials and persistent volumes are unchanged. Hostinger redeployment remains the user's acceptance test.

- Corrected release: Actions 38360900823 succeeded; anonymous Docker pull and the loopback regression passed again on the published image. Embedded source hash matches checkout. Automatic Compose changed only the bootstrap image and still parses with empty environment.

## Password-only login follow-up

24 unit/contract tests passed. Actual nginx + Steel + private login service behind local TLS: Korean/English and project-specific instructions rendered; mobile layout inspected; bad password and cross-origin submissions blocked without a native Basic-auth challenge. Successful form login sets a Secure/HttpOnly/SameSite=Strict opaque cookie. Cookie-authenticated Steel API and actual CDP browser interaction passed, as did explicit Basic API compatibility and restart revocation. Password-change/expiry invalidation is unit-tested. Source is pinned to Python 3.12, whose crypt module supports the existing bcrypt hashes; moving to Python 3.13 requires replacing that verifier.

The no-Buzz automatic Docker/Traefik fixture passed with the additional login service, including gateway reconciliation and idempotent bootstrap rerun. Hostinger UI acceptance remains user-operated. This release requires the full Compose change (login service plus gateway), not just a bootstrap image change. Existing volumes/passwords are preserved.
