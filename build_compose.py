"""Build a standalone URL-importable Compose; no relative file dependencies."""
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent

def build():
    config = (ROOT / 'gateway.conf').read_text()
    pins = yaml.safe_load((ROOT / 'images.yaml').read_text())
    host = '${STEEL_HOST:-setup.invalid}'
    validation = (ROOT / 'validate-host.sh').read_text()
    auth = (ROOT / 'init-auth.sh').read_text().replace('# VALIDATE_HOST', validation)
    result = {'services': {
        'auth-init': {
            'image': pins['httpd'], 'restart': 'no',
            'entrypoint': ['/bin/sh', '-ec'],
            'command': [auth.replace('$', '$$')],
            'environment': {'STEEL_HOST': host, 'STEEL_PASSWORD': '${STEEL_PASSWORD:-}'},
            'volumes': ['auth:/auth'], 'network_mode': 'none',
        },
        'gateway': {
            'image': pins['nginx'], 'restart': 'unless-stopped',
            'entrypoint': ['/bin/sh', '-ec'],
            'command': [validation.replace('$', '$$') + "\ntest -s /auth/users || { echo 'Authentication missing; redeploy auth-init' >&2; exit 1; }\ncat > /tmp/steel-nginx.conf <<'STEEL_NGINX'\n" + config.replace('$', '$$') +
                        "STEEL_NGINX\nexec nginx -c /tmp/steel-nginx.conf -g 'daemon off;'"],
            'environment': {'STEEL_HOST': host},
            'mem_limit': '192m', 'cpus': 1, 'pids_limit': 64,
            'expose': ['8080'], 'volumes': ['auth:/auth:ro'],
            'depends_on': {'auth-init': {'condition': 'service_completed_successfully'},
                           'steel-api': {'condition': 'service_healthy'},
                           'login': {
            'image': pins['bootstrap'], 'restart': 'unless-stopped', 'init': True,
            'command': ['python', '/app/login.py'], 'user': '10002:10002',
            'read_only': True, 'cap_drop': ['ALL'],
            'security_opt': ['no-new-privileges:true'],
            'mem_limit': '96m', 'cpus': 0.5, 'pids_limit': 48,
            'environment': {'STEEL_PROJECT': '${COMPOSE_PROJECT_NAME}'},
            'volumes': ['auth:/auth:ro'],
            'depends_on': {'auth-init': {'condition': 'service_completed_successfully'}},
            'labels': {'traefik.enable': 'false'},
        },
        'steel-ui': {'condition': 'service_healthy'},
                           'login': {'condition': 'service_started'}},
            'labels': {
                'traefik.enable': 'true',
                'traefik.http.routers.${COMPOSE_PROJECT_NAME}.rule': 'Host(`'+host+'`)',
                'traefik.http.routers.${COMPOSE_PROJECT_NAME}.entrypoints': 'websecure',
                'traefik.http.routers.${COMPOSE_PROJECT_NAME}.tls.certresolver': 'letsencrypt',
                'traefik.http.routers.${COMPOSE_PROJECT_NAME}.service': '${COMPOSE_PROJECT_NAME}',
                'traefik.http.services.${COMPOSE_PROJECT_NAME}.loadbalancer.server.port': '8080',
            },
        },
        'login': {
            'image': pins['bootstrap'], 'restart': 'unless-stopped', 'init': True,
            'command': ['python', '/app/login.py'], 'user': '10002:10002',
            'read_only': True, 'cap_drop': ['ALL'],
            'security_opt': ['no-new-privileges:true'],
            'mem_limit': '96m', 'cpus': 0.5, 'pids_limit': 48,
            'environment': {'STEEL_PROJECT': '${COMPOSE_PROJECT_NAME}'},
            'volumes': ['auth:/auth:ro'],
            'depends_on': {'auth-init': {'condition': 'service_completed_successfully'}},
            'labels': {'traefik.enable': 'false'},
        },
        'steel-ui': {
            'image': pins['ui'], 'restart': 'unless-stopped',
            'environment': {'API_URL': 'http://steel-api:3000'},
            'healthcheck': {'test': ['CMD-SHELL', 'wget -q -O /dev/null http://127.0.0.1/ || exit 1'], 'interval': '10s', 'timeout': '5s', 'retries': 12},
            'labels': {'traefik.enable': 'false'},
        },
        'steel-api': {
            'image': pins['api'], 'restart': 'unless-stopped', 'shm_size': '512m', 'init': True, 'stop_grace_period': '30s',
            'mem_limit': '${STEEL_MEMORY_LIMIT:-2g}', 'pids_limit': 512,
            'entrypoint': ['/bin/sh', '-ec'],
            'command': [(ROOT / 'profile-start.sh').read_text().replace('$', '$$')],
            'depends_on': {'auth-init': {'condition': 'service_completed_successfully'}},
            'healthcheck': {'test': ['CMD', 'node', '-e', 'Promise.all([fetch("http://127.0.0.1:3000/v1/health").then(r=>{if(!r.ok)throw Error()}),fetch("http://127.0.0.1:9222/json/version").then(r=>r.json()).then(j=>{if(!j.webSocketDebuggerUrl)throw Error()})]).then(()=>process.exit(0)).catch(()=>process.exit(1))'], 'interval': '10s', 'timeout': '5s', 'retries': 18, 'start_period': '60s'},
            'environment': {'DOMAIN': host, 'USE_SSL': 'true',
                            'CHROME_USER_DATA_DIR': '/data/browser',
                            'LOG_STORAGE_ENABLED': 'true',
                            'LOG_STORAGE_PATH': '/data/logs/browser-logs.duckdb'},
            'volumes': ['logs:/data/logs', 'exports:/tmp/steel-browser-exports', 'cache:/app/.cache', 'browser:/data/browser'],
            'labels': {'traefik.enable': 'false'},
        },
    }, 'volumes': {name: {} for name in ('auth', 'logs', 'exports', 'cache', 'browser')}}
    for service in result['services'].values():
        service['logging'] = {'driver': 'json-file', 'options': {'max-size': '5m', 'max-file': '2'}}
    result['services']['gateway']['labels'] = [f'{k}={v}' for k, v in result['services']['gateway']['labels'].items()]
    return result

if __name__ == '__main__':
    (ROOT / 'compose.hostinger.yaml').write_text(yaml.safe_dump(build(), sort_keys=False))
