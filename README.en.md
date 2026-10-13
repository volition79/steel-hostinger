# Steel Browser for Hostinger

Uses official Steel API/UI images with an authenticated, same-origin gateway.
This is a separate package and does not change Buzz. **Local Docker checks passed; Hostinger VPS validation remains outstanding.**

## Optional installation and support scope

**Steel Browser is optional. It is not a required component of buzz-agents.**
An existing Buzz Relay and buzz-agents can provide AI conversations, collaboration and code execution without Steel.
Consider Steel only when you need a browser on the VPS for website interaction or browser automation.
Installing Steel does not automatically connect browser tools to Buzz agents; that integration is a separate step.

Steel itself does not require Buzz or buzz-agents.
This package requires **Hostinger Docker Manager and a running Traefik instance**.
Prepare Traefik first if it is absent.

## Automatic installation by URL

1. Ensure **Traefik is running** in Hostinger Docker Manager.
2. Choose **Compose from URL** and enter:

   `https://raw.githubusercontent.com/volition79/steel-hostinger/main/compose.auto.yaml`

3. Use a unique project name, such as `steel-browser`.
4. On supported default Hostinger configurations, **leave Environment empty and deploy**. The hostname and initial password are configured automatically.
5. Once deployed, click **Open**. If absent, use the HTTPS URL in `bootstrap` logs. Initial certificate issuance can take time.
6. Enter username **steel** and the initial password from `auth-init` logs in the browser authentication prompt.
7. Open your target website inside Steel and sign in there.

This URL tracks main. Replace main with the supplied commit SHA to pin a release.
All images are publicly available and digest-pinned; no local image build is needed.
Local Docker checks without Buzz passed. **Real Hostinger URL import, Open-button discovery and public ACME remain user acceptance tests.**

## Automatic setup conditions

The flow is: deploy by URL → automatic address configuration → Open → login.
STEEL_HOST and STEEL_PASSWORD may be omitted; the initial generated password appears in auth-init logs.

- Requires one running Traefik with a confirmed Docker provider and identifiable HTTPS entrypoint/certificate resolver.
- Finds srv<number>.hstgr.cloud from the Docker server name, Traefik environment or existing router labels; Buzz is not required.
- A loopback result such as 127.0.1.1 for the VPS base hostname triggers TLS-verified [Google Public DNS](https://developers.google.com/speed/public-dns/docs/doh/json) queries for both names. Failed queries or differing public addresses remain blocked; diagnostics show only hostnames and IPs.
- Missing or conflicting candidates and unresolved DNS stop automatic configuration with a bootstrap log message. Fix the prerequisite and restart the project.
- Saved host/network identity is retained. A changed discovery result stops rather than silently changing the API's public origin.
- Only this project's gateway labels/network are reconciled. Other projects and data volumes are preserved.
- Only the helper receives the Docker socket and its own Compose directory. Docker socket access is administrator-level control over VPS containers; it is never given to the browser/API/UI.
- File-only provider configuration that cannot be confirmed, multiple Traefik instances or conflicting domains are outside the automatic support scope.

For development, build Dockerfile.bootstrap as steel-bootstrap:test, then run `python3 build_auto.py --image steel-bootstrap:test`.
The public file uses the helper digest in images.yaml; regenerate with `python3 build_auto.py`.

## Advanced: manual hostname installation

1. Ensure Hostinger's Traefik is running.
2. Docker Manager → Compose from URL:
   `https://raw.githubusercontent.com/volition79/steel-hostinger/main/compose.hostinger.yaml`
   Replace `main` with a commit SHA to pin the package version. No relative files or image builds are needed.
3. Choose a unique project name, such as `steel-browser`.
4. Set `STEEL_HOST` to a hostname pointing to your VPS, e.g. `steel-browser.srv123456.hstgr.cloud`, without a scheme, port or path.
5. Optionally set `STEEL_PASSWORD` to 16–72 printable ASCII characters on one line. If omitted on first install, a random password is generated once and shown in `auth-init` logs. Existing authentication is preserved when omitted. Keep these logs private. A missing STEEL_HOST permits Compose parsing but blocks initialization with instructions; fill Environment and redeploy.
6. Deploy and open `https://YOUR-STEEL_HOST`. Hostinger's Open-button discovery still requires VPS verification.
7. In the browser authentication prompt, enter username **steel** and your chosen or generated password.
8. When the default browser viewer appears, enter a website address in its address bar.

Requires Traefik's `websecure` entrypoint and `letsencrypt` resolver. The package targets
the observed Hostinger host-network Traefik configuration. A bridge-network Traefik
needs a shared Docker network added to the gateway.

## Operation

The browser runs on the VPS; sign into websites through its viewer.
Installing this package does not automatically equip Buzz agents with a browser tool.
Automation clients must send authentication too. API/UI/WebSocket share one protected origin;
API and CDP ports are not published to the host.

Logs, exports and cache have persistent volumes. The default browser profile now has its own `browser` volume. Previous temporary profiles are not migrated. Website expiry/logout and separately created sessions may still require login.

Before updating, finish work and back up volumes. Edit/redeploy the same project using
the new package, preserving volumes. Images are digest-pinned: the Docker Manager
Update button alone does not move to a newer release.

To change the password, edit `STEEL_PASSWORD` and redeploy. The auth initializer must
succeed before the replacement gateway starts. Use a private window if your browser caches old credentials.

## Troubleshooting

- Deployment failure: check required environment values and `auth-init` logs for password length.
- 502: allow API/UI startup time, then inspect their logs if the error persists.
- Blank viewer: confirm WebSockets use `wss://YOUR-STEEL_HOST/...`; open the HTTPS URL.
- Authentication failure: username is `steel`, not your Hostinger account.
- Reserve RAM/disk capacity for the browser alongside existing AI workloads.

Build with Python 3 and PyYAML: `python3 build_compose.py`.
Contract checks: `python3 -m unittest discover -s tests -v`.
See `VERIFICATION.md` for actual evidence and remaining checks.

Sources: https://github.com/steel-dev/steel-browser and https://docs.steel.dev/overview/self-hosting/docker

## Limits and recovery

Keep the project name unchanged: another name creates separate volumes. To recover a lost password, set STEEL_PASSWORD and redeploy, then restart gateway to disconnect existing WebSockets. Restart alone does not apply changed environment values.

API memory defaults to 2GiB; STEEL_MEMORY_LIMIT may override it (e.g. 3g), subject to VPS capacity. This protects other workloads, not a guarantee against browser OOM. Gateway traffic has an aggregate 20 requests/second limit with burst 60; wait/retry on 429. Gateway request bodies are limited to 128MiB. Connections with no upstream data for one hour may close; refresh/reconnect. This is not a total task-duration limit.

Never delete a browser profile lock while another browser may own it. Recent changes not yet written to disk may be lost on an unclean shutdown.

### Profile ownership and readiness

Only one API from this package may own the browser volume. The startup wrapper holds an exclusive file lock for the API lifetime and removes only stale Chromium singleton links after acquiring it. Do not share this volume with another service or older unwrapped container. Stop the existing API before replacing it. Exit code 73 means another owner holds the lock. Never delete the ownership lock file.

Readiness checks both the API and actual Chromium endpoint. Docker does not automatically restart a container merely because it becomes unhealthy. Recent cookie/input changes may not reach disk before a crash; persistent storage is not a guarantee of continued website authentication.

## Recovering an initial dns_mismatch deployment

If the base VPS hostname resolved to 127.0.1.1, edit the existing project YAML and replace only the bootstrap image reference with the corrected release digest, then deploy. Preserve the project name, volumes and other services. Restart alone does not update digest-pinned images.

```text
ghcr.io/volition79/steel-hostinger-bootstrap@sha256:3476916882e6b0b1144c42e6bbba91b164ab5e214a8e04b97be9bc06906246bc
```
