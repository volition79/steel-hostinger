# Steel Browser for Hostinger

Uses official Steel API/UI images with an authenticated, same-origin gateway.
This is a separate package and does not change Buzz. **Local Docker checks passed; Hostinger VPS validation remains outstanding.**

## Install

1. Ensure Hostinger's Traefik is running.
2. Docker Manager → Compose from URL:
   `https://raw.githubusercontent.com/volition79/steel-hostinger/main/compose.hostinger.yaml`
   Replace `main` with a commit SHA to pin the package version. No relative files or image builds are needed.
3. Choose a unique project name, such as `steel-browser`.
4. Set `STEEL_HOST` to a hostname pointing to your VPS, e.g. `steel-browser.srv123456.hstgr.cloud`, without a scheme, port or path.
5. Set `STEEL_PASSWORD` to a unique password of at least 16 characters. Long random alphanumeric values avoid environment-file escaping issues.
6. Deploy and open `https://YOUR-STEEL_HOST`. Hostinger's Open-button discovery still requires VPS verification.
7. In the browser authentication prompt, enter username **steel** and your chosen password.
8. When the default browser viewer appears, enter a website address in its address bar.

Requires Traefik's `websecure` entrypoint and `letsencrypt` resolver. The package targets
the observed Hostinger host-network Traefik configuration. A bridge-network Traefik
needs a shared Docker network added to the gateway.

## Operation

The browser runs on the VPS; sign into websites through its viewer.
Installing this package does not automatically equip Buzz agents with a browser tool.
Automation clients must send authentication too. API/UI/WebSocket share one protected origin;
API and CDP ports are not published to the host.

Logs, exports and cache have persistent volumes. Website login persistence across session
recreation or container restarts is **not guaranteed** by those volumes.

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
