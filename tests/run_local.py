"""Disposable local TLS integration test. Requires Docker Compose, OpenSSL,
PyYAML, Playwright and its Chromium. Does not access the Hostinger VPS.
"""
import os
import secrets
import shutil
import subprocess
import sys
import time
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
docker = os.environ.get('STEEL_TEST_DOCKER') or shutil.which('docker')
if not docker or not Path(docker).exists():
    docker = '/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe'
local = ROOT / '.local'
local.mkdir(exist_ok=True)
password = secrets.token_urlsafe(32)
(local / 'test.env').write_text(f'STEEL_HOST=localhost:18443\nSTEEL_PASSWORD={password}\n')
subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes',
                '-keyout', str(local / 'key.pem'), '-out', str(local / 'cert.pem'),
                '-days', '1', '-subj', '/CN=localhost'], check=True, capture_output=True)
(local / 'tls.conf').write_text('''events {}
http { resolver 127.0.0.11 valid=1s ipv6=off;
server { listen 443 ssl; ssl_certificate /cert.pem; ssl_certificate_key /key.pem;
location / { set $backend gateway:8080; proxy_pass http://$backend;
proxy_http_version 1.1; proxy_set_header Host $http_host;
proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection "upgrade";
proxy_read_timeout 3600s; } } }
''')
pins = yaml.safe_load((ROOT / 'images.yaml').read_text())
(local / 'override.yaml').write_text(yaml.safe_dump({'services': {'test-tls': {
    'image': pins['nginx'], 'ports': ['127.0.0.1:18443:443'],
    'volumes': ['./.local/tls.conf:/etc/nginx/nginx.conf:ro',
                './.local/cert.pem:/cert.pem:ro', './.local/key.pem:/key.pem:ro'],
    'depends_on': ['gateway']}}}))
compose = [docker, 'compose', '--env-file', '.local/test.env', '-p', 'steel-package-test',
           '-f', 'compose.hostinger.yaml', '-f', '.local/override.yaml']

def wait_ready():
    # Probe inside the Docker network: no dependency on host loopback forwarding.
    probe = 'fetch("http://steel-api:3000/v1/health").then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))'
    for _ in range(60):
        r = subprocess.run(compose + ['exec', '-T', 'steel-api', 'node', '-e', probe],
                           capture_output=True)
        if r.returncode == 0:
            return
        time.sleep(2)
    raise RuntimeError('Steel did not become ready in 120 seconds')

try:
    subprocess.run(compose + ['config', '--quiet'], check=True)
    subprocess.run(compose + ['up', '-d'], check=True)
    wait_ready()
    env = {**os.environ, 'STEEL_TEST_PASSWORD': password}
    subprocess.run([sys.executable, 'tests/live_smoke.py'], env=env, check=True)
    subprocess.run(compose + ['restart', 'steel-api', 'steel-ui', 'gateway'], check=True)
    wait_ready()
    subprocess.run([sys.executable, 'tests/live_smoke.py'], env=env, check=True)
finally:
    # Preserve test volumes for diagnosis; never remove user volumes.
    subprocess.run(compose + ['stop'], check=False)
