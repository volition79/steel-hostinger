"""Real automatic bootstrap/Traefik fixture without Buzz. Local Docker only."""
import os, sys, subprocess, time, json, ssl, urllib.request, urllib.error, base64, hashlib
from pathlib import Path
import yaml
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from build_auto import build_auto
ROOT=Path(__file__).resolve().parents[1];os.chdir(ROOT)
D=os.environ['STEEL_TEST_DOCKER']; P=os.environ.get('STEEL_TEST_PROJECT','steel-auto-fresh'); C=P+'-controller'; N=P+'-proxy'
def run(args,check=True):return subprocess.run([D,*args],check=check,capture_output=True,text=True).stdout
local=ROOT/'.local';local.mkdir(exist_ok=True)
host='steel-'+hashlib.sha256(P.encode()).hexdigest()[:12]+'.srv900001.hstgr.cloud'
model=build_auto('steel-bootstrap:test')
model['services']['bootstrap']['extra_hosts']=[host+':127.0.0.1','srv900001.hstgr.cloud:127.0.0.1']
# Empty password exercises first-install generation in the real stack.
(local/'auto.yaml').write_text(yaml.safe_dump(model,sort_keys=False))
try:
 run(['network','create',N],False)
 run(['run','-d','--name',P+'-traefik','--network',N,'-p','127.0.0.1:19443:443','-v','/var/run/docker.sock:/var/run/docker.sock:ro','-e','TRAEFIK_HOST=srv900001.hstgr.cloud','traefik:v3.6','--providers.docker=true','--providers.docker.exposedbydefault=false','--entrypoints.websecure.address=:443','--certificatesresolvers.fixture.acme.email=test@example.com','--certificatesresolvers.fixture.acme.caserver=http://127.0.0.1:9/directory','--certificatesresolvers.fixture.acme.httpchallenge.entrypoint=websecure'])
 run(['run','-d','--name',C,'-v','/var/run/docker.sock:/var/run/docker.sock','-v','/docker/'+P+':/docker/'+P,'--entrypoint','sleep','steel-bootstrap:test','infinity'])
 run(['cp','.local/auto.yaml',C+':/docker/'+P+'/docker-compose.yml'])
 compose=['exec',C,'docker','compose','-p',P,'-f','/docker/'+P+'/docker-compose.yml']
 run(compose+['up','-d'])
 for _ in range(90):
  state=json.loads(run(['inspect',P+'-bootstrap-1']))[0]['State']
  if not state['Running']:
   assert state['ExitCode']==0,run(['logs',P+'-bootstrap-1']);break
  time.sleep(3)
 else: raise AssertionError('bootstrap did not finish: '+run(['logs',P+'-bootstrap-1']))
 gw=json.loads(run(['inspect',P+'-gateway-1']))[0]
 assert gw['Config']['Labels']['traefik.http.routers.'+P+'.rule']=='Host(`'+host+'`)'
 assert N in gw['NetworkSettings']['Networks'] and P+'_default' in gw['NetworkSettings']['Networks']
 authlog=run(['logs',P+'-auth-init-1'])
 password=next(x.split('Password: ',1)[1] for x in authlog.splitlines() if x.startswith('Password: '))
 assert len(password)==48
 def req(auth=False):
  headers={'Host':host}
  if auth: headers['Authorization']='Basic '+base64.b64encode(('steel:'+password).encode()).decode()
  try:
   with urllib.request.urlopen(urllib.request.Request('https://localhost:19443/api/v1/sessions',headers=headers),context=ssl._create_unverified_context(),timeout=10) as r:return r.status,r.read().decode()
  except urllib.error.HTTPError as e:return e.code,''
 for _ in range(20):
  if req()[0]==401:break
  time.sleep(2)
 assert req()[0]==401
 status,data=req(True);assert status==200,(status,data)
 assert host in data and 'https://' in data,data
 print('PASS: no Buzz, auto hostname, actual Compose route/network, unauthenticated 401, authenticated Steel API HTTPS',flush=True)
 before=gw['Id'];run(compose+['restart','bootstrap'])
 for _ in range(60):
  s=json.loads(run(['inspect',P+'-bootstrap-1']))[0]['State']
  if not s['Running']:assert s['ExitCode']==0;break
  time.sleep(2)
 else: raise AssertionError('repeat bootstrap did not finish')
 assert json.loads(run(['inspect',P+'-gateway-1']))[0]['Id']==before
 print('PASS: repeated bootstrap preserves gateway identity',flush=True)
finally:
 if run(['ps','-q','--filter','name=^/'+C+'$']).strip():run(['exec',C,'docker','compose','-p',P,'-f','/docker/'+P+'/docker-compose.yml','stop'],False)
 for name in (C,P+'-traefik'):run(['rm','-f',name],False)
