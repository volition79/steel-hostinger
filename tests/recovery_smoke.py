"""Local stack only: exclusive ownership, crash recovery and real rate limiting."""
import os, subprocess, time, ssl, urllib.request, urllib.error, secrets
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT)
docker=os.environ['STEEL_TEST_DOCKER']
compose=[docker,'compose','--env-file','.local/test.env','-p','steel-package-test','-f','compose.hostinger.yaml','-f','.local/override.yaml']
api=yaml.safe_load(Path('images.yaml').read_text())['api']
def cmd(args,**kw): return subprocess.run(args,check=True,capture_output=True,text=True,**kw)
def ready():
 for _ in range(60):
  r=subprocess.run(compose+['exec','-T','steel-api','node','-e','fetch("http://127.0.0.1:9222/json/version").then(r=>r.json()).then(j=>process.exit(j.webSocketDebuggerUrl?0:1)).catch(()=>process.exit(1))'],capture_output=True)
  if r.returncode==0: return
  time.sleep(2)
 raise AssertionError('browser not ready')
try:
 cmd(compose+['up','-d']); ready()
 before=cmd(compose+['exec','-T','steel-api','readlink','/data/browser/SingletonLock']).stdout
 r=subprocess.run([docker,'run','--rm','-v','steel-package-test_browser:/data/browser','--entrypoint','/bin/sh',api,'-ec',Path('profile-start.sh').read_text()],capture_output=True,text=True)
 assert r.returncode==73,(r.returncode,r.stderr)
 after=cmd(compose+['exec','-T','steel-api','readlink','/data/browser/SingletonLock']).stdout
 assert before==after
 print('PASS: concurrent profile owner blocked, existing SingletonLock unchanged',flush=True)
 env={**os.environ,'STEEL_TEST_COOKIE_NONCE':secrets.token_hex(16),'STEEL_TEST_PASSWORD':next(x.split('=',1)[1] for x in Path('.local/test.env').read_text().splitlines() if x.startswith('STEEL_PASSWORD='))}
 cmd([os.sys.executable,'tests/profile_probe.py','seed'],env=env)
 cmd(compose+['up','-d','--force-recreate','--no-deps','steel-api']); ready()
 cmd([os.sys.executable,'tests/profile_probe.py','verify'],env=env)
 print('PASS: unique cookie survives forced recreation',flush=True)
 cmd(compose+['kill','-s','SIGKILL','steel-api'])
 cmd(compose+['up','-d','--no-deps','steel-api']); ready()
 cmd([os.sys.executable,'tests/profile_probe.py','verify'],env=env)
 print('PASS: SIGKILL recovery, persistent cookie retained',flush=True)
 # No authenticated session creation: unauthorized requests still hit nginx's rate gate.
 def request(_):
  try:
   with urllib.request.urlopen('https://localhost:18443/',context=ssl._create_unverified_context(),timeout=15) as r:return r.status
  except urllib.error.HTTPError as e:return e.code
 with ThreadPoolExecutor(max_workers=60) as pool: counts=Counter(pool.map(request,range(240)))
 assert counts[429]>0,counts
 print('PASS: request burst limited:',dict(counts),flush=True)
finally:
 subprocess.run(compose+['stop'],check=False)
