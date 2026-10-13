"""Actual Steel + nginx + login through disposable localhost TLS. No VPS access."""
import os,sys,time,secrets,subprocess,json,ssl,urllib.request,base64
from pathlib import Path
import yaml
from playwright.sync_api import sync_playwright
os.environ['NODE_TLS_REJECT_UNAUTHORIZED']='0'  # Only local test TLS.
ROOT=Path(__file__).resolve().parents[1];os.chdir(ROOT);sys.path.insert(0,str(ROOT))
from build_compose import build
D='/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe'
local=ROOT/'.local';local.mkdir(exist_ok=True)
password=secrets.token_urlsafe(32)
(local/'login.env').write_text('STEEL_HOST=steel-test.example.com\nSTEEL_PASSWORD='+password+'\n')
subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(local/'login-key.pem'),'-out',str(local/'login-cert.pem'),'-days','1','-subj','/CN=localhost'],check=True,capture_output=True)
(local/'login-tls.conf').write_text('''events {}\nhttp { resolver 127.0.0.11 valid=1s ipv6=off;
server { listen 443 ssl; ssl_certificate /cert.pem; ssl_certificate_key /key.pem;
location / { set $backend gateway:8080; proxy_pass http://$backend;
proxy_http_version 1.1; proxy_set_header Host $http_host;
proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection "upgrade"; } } }''')
c=build();c['services']['login']['image']='steel-bootstrap:login'
c['services']['steel-api']['environment']['DOMAIN']='localhost:18443'
c['services']['test-tls']={'image':c['services']['gateway']['image'],'ports':['127.0.0.1:18443:443'],'volumes':['./.local/login-tls.conf:/etc/nginx/nginx.conf:ro','./.local/login-cert.pem:/cert.pem:ro','./.local/login-key.pem:/key.pem:ro'],'depends_on':['gateway']}
(local/'login-compose.yaml').write_text(yaml.safe_dump(c,sort_keys=False))
cmd=[D,'compose','--project-directory',str(ROOT),'--env-file','.local/login.env','-p','steel-package-test','-f','.local/login-compose.yaml']
# Windows Docker needs a Windows project directory.
cmd[3]='C:/Users/LEEDONGGEUN/Desktop/Hostinger/steel-hostinger'
try:
 subprocess.run(cmd+['up','-d'],check=True)
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True)
  context=browser.new_context(ignore_https_errors=True,locale='ko-KR',viewport={'width':1280,'height':900})
  page=context.new_page();page.goto('https://localhost:18443/');page.wait_for_selector('#password')
  assert '/_steel/login' in page.url
  assert page.locator('h1').inner_text()=='내 VPS 브라우저에 접속'
  assert 'steel-package-test' in page.locator('.path').inner_text()
  page.screenshot(path=str(local/'login-ko.png'),full_page=True)
  page.goto('https://localhost:18443/_steel/login?lang=en');assert 'Your VPS browser' in page.locator('h1').inner_text()
  page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(local/'login-en-mobile.png'),full_page=True)
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  # Anonymous API fails without Chrome Basic-auth challenge.
  r=context.request.get('https://localhost:18443/api/v1/sessions');assert r.status==401;assert 'www-authenticate' not in r.headers
  r=context.request.post('https://localhost:18443/_steel/login',form={'password':password},headers={'Origin':'https://evil.example'});assert r.status==403
  page.fill('#password','incorrect-password-123');page.click('button');assert page.locator('.message').inner_text()
  page.fill('#password',password);page.click('button');page.wait_for_url('https://localhost:18443/')
  cookies=context.cookies();session=next(c for c in cookies if c['name']=='__Host-steel_session')
  assert session['secure'] and session['httpOnly'] and session['sameSite']=='Strict'
  r=context.request.get('https://localhost:18443/api/v1/sessions');assert r.status==200
  data=r.json();(local/'login-session-shape.json').write_text(json.dumps(data))
  # Actual CDP WebSocket through cookie auth; browser does not need Basic auth.
  remote=p.chromium.connect_over_cdp(data['sessions'][0]['websocketUrl'],headers={'Cookie':'__Host-steel_session='+session['value']},timeout=30000)
  target=remote.contexts[0].new_page();target.goto('data:text/html,<button onclick="this.textContent=\'Clicked\'">Click</button>');target.locator('button').click();assert target.locator('button').inner_text()=='Clicked';target.close();remote.close()
  basic=base64.b64encode(('steel:'+password).encode()).decode()
  other=browser.new_context(ignore_https_errors=True)
  assert other.request.get('https://localhost:18443/api/v1/sessions',headers={'Authorization':'Basic '+basic}).status==200
  # Restart invalidates opaque sessions; password remains valid.
  subprocess.run(cmd+['restart','login'],check=True,stdout=subprocess.DEVNULL)
  time.sleep(2)
  assert context.request.get('https://localhost:18443/api/v1/sessions').status==401
  browser.close()
 print('LOGIN LIVE PASS: ko/en, actual project, mobile, no prompt, bad password, origin, cookie, API, CDP interaction, Basic compatibility, restart revocation')
finally:
 subprocess.run(cmd+['stop'],check=False)
