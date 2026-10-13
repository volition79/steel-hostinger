# Verification — 2026-10-13

Scope: standalone Steel deployment package. Existing Buzz and Hostinger VPS were not modified.

## Passed

- Docker Compose parsed the standalone file with environment interpolation. Router label keys use list syntax so the project name is interpolated.
- Three Python package contract tests passed. Generated YAML matches source; images are digest-pinned; backend ports are not published; generated public URLs use TLS.
- Nginx configuration syntax passed inside the pinned gateway image.
- Actual pinned Steel API/UI ran on Docker Desktop Engine 28.3.3 (Linux containers).
- Local HTTPS terminator + authenticated gateway + official UI + official API were tested together.
- Unauthenticated requests to UI, API, viewer and WebSocket paths returned 401. Incorrect credentials returned 401.
- `/v1/sessions` and `/api/v1/sessions` returned successful responses. An initial proxy rewrite-order defect caused `/api/v1/sessions` to return 500; moving backend assignment before `rewrite ... break` fixed it. The live test explicitly asserts both paths return 200.
- Steel returned HTTPS debug URLs and a WSS CDP URL at the public origin.
- Playwright connected over authenticated root CDP and navigated the actual remote browser to example.com.
- The real viewer received image frames. Clicking the viewer canvas and typing changed a remote HTML input; the value was checked through CDP. The input page is a test fixture injected after the external navigation, not part of example.com.
- After API/UI/gateway restart, the same live navigation/viewer/input checks passed again.
- A short password was rejected by `auth-init`; the existing authentication file remained unchanged.

## Reproduction

Install Python 3, PyYAML, Playwright with Chromium, Docker Compose, and OpenSSL.

```sh
python3 -m unittest discover -s tests -v
python3 tests/run_local.py
```

The integration runner uses only the `steel-package-test` local project and localhost port 18443.
It generates a disposable password and self-signed certificate under ignored `.local/`,
runs the browser checks before/after restart, and stops the test containers afterwards.
Test volumes remain for diagnosis. It does not connect to the Hostinger VPS.
TLS certificate verification is disabled only inside that local self-signed test process.
The shipped Compose enables HTTPS URLs and does not disable TLS verification.

## Remaining validation

- Hostinger URL import, Open-button discovery, wildcard hostname resolution and Let's Encrypt issuance have NOT been tested for this package.
- The local TLS terminator exercises secure forwarding, but is not a Hostinger Traefik deployment test.
- Mobile remote input, DevTools UI, downloads, uploads, and long-running/recovery behavior are not certified by this smoke test.
- Website login persistence is unverified; cache/log/export volumes alone do not establish it.
- Buzz agent tool integration is not included.
- This report records local implementation verification before GitHub publication; publication does not prove Hostinger deployment.

Scoped direct test evidence only; no full Sonol confidence-plan or policy release-gate certification is claimed.
