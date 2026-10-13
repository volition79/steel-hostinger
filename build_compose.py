"""Build a standalone URL-importable Compose; no relative file dependencies."""
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent

def build():
    config = (ROOT / 'gateway.conf').read_text()
    pins = yaml.safe_load((ROOT / 'images.yaml').read_text())
    host = '${STEEL_HOST:?Enter the Steel hostname without https or a path}'
    result = {'services': {
        'auth-init': {
            'image': pins['httpd'], 'restart': 'no',
            'entrypoint': ['/bin/sh', '-ec'],
            'command': ['umask 077; test "$${#STEEL_PASSWORD}" -ge 16 || { echo "Use a password of at least 16 characters" >&2; exit 1; }; '
                        'printf "%s\\n" "$$STEEL_PASSWORD" | htpasswd -i -B -C 12 -c /auth/users.new steel; '
                        'chmod 644 /auth/users.new; mv /auth/users.new /auth/users'],
            'environment': {'STEEL_PASSWORD': '${STEEL_PASSWORD:?Set a unique password of at least 16 characters}'},
            'volumes': ['auth:/auth'], 'network_mode': 'none',
        },
        'gateway': {
            'image': pins['nginx'], 'restart': 'unless-stopped',
            'entrypoint': ['/bin/sh', '-ec'],
            'command': ["cat > /tmp/steel-nginx.conf <<'STEEL_NGINX'\n" + config.replace('$', '$$') +
                        "STEEL_NGINX\nexec nginx -c /tmp/steel-nginx.conf -g 'daemon off;'"],
            'expose': ['8080'], 'volumes': ['auth:/auth:ro'],
            'depends_on': {'auth-init': {'condition': 'service_completed_successfully'},
                           'steel-api': {'condition': 'service_started'},
                           'steel-ui': {'condition': 'service_started'}},
            'labels': {
                'traefik.enable': 'true',
                'traefik.http.routers.${COMPOSE_PROJECT_NAME}.rule': 'Host(`'+host+'`)',
                'traefik.http.routers.${COMPOSE_PROJECT_NAME}.entrypoints': 'websecure',
                'traefik.http.routers.${COMPOSE_PROJECT_NAME}.tls.certresolver': 'letsencrypt',
                'traefik.http.routers.${COMPOSE_PROJECT_NAME}.service': '${COMPOSE_PROJECT_NAME}',
                'traefik.http.services.${COMPOSE_PROJECT_NAME}.loadbalancer.server.port': '8080',
            },
        },
        'steel-ui': {
            'image': pins['ui'], 'restart': 'unless-stopped',
            'environment': {'API_URL': 'http://steel-api:3000'},
            'labels': {'traefik.enable': 'false'},
        },
        'steel-api': {
            'image': pins['api'], 'restart': 'unless-stopped', 'shm_size': '1gb',
            'environment': {'DOMAIN': host, 'USE_SSL': 'true',
                            'LOG_STORAGE_ENABLED': 'true',
                            'LOG_STORAGE_PATH': '/data/logs/browser-logs.duckdb'},
            'volumes': ['logs:/data/logs', 'exports:/tmp/steel-browser-exports', 'cache:/app/.cache'],
            'labels': {'traefik.enable': 'false'},
        },
    }, 'volumes': {name: {} for name in ('auth', 'logs', 'exports', 'cache')}}
    for service in result['services'].values():
        service['logging'] = {'driver': 'json-file', 'options': {'max-size': '5m', 'max-file': '2'}}
    result['services']['gateway']['labels'] = [f'{k}={v}' for k, v in result['services']['gateway']['labels'].items()]
    return result

if __name__ == '__main__':
    (ROOT / 'compose.hostinger.yaml').write_text(yaml.safe_dump(build(), sort_keys=False))
