"""Private gateway authentication. No Docker access; existing htpasswd is read-only."""
import base64
import crypt
import hashlib
import hmac
import html
from http.cookies import SimpleCookie, CookieError
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import secrets
import threading
import time
from urllib.parse import parse_qs, urlsplit

COOKIE='__Host-steel_session'
SESSIONS={}
LOCK=threading.Lock()
VERIFY=threading.BoundedSemaphore(2)
TTL=43200
AUTH_FILE=Path('/auth/users')
TEMPLATE=Path(__file__).with_name('login.html').read_text()
TEXT={
 'ko': {'title':'내 VPS 브라우저에 접속', 'intro':'Steel Browser를 열려면 설치 비밀번호를 입력하세요.', 'password':'비밀번호', 'button':'브라우저 열기', 'help':'비밀번호 확인 방법', 'step':'Hostinger Docker Manager → {project} → 관리 → 로그', 'detail':'auth-init 로그에서 최초 로그인 안내의 Password 값을 복사해 붙여넣으세요.', 'note':'Hostinger 계정이나 VPS root 비밀번호가 아닙니다. 사용자 이름 steel은 자동으로 처리합니다.', 'lost':'비밀번호를 직접 설정했다면 해당 비밀번호를 사용하세요. 분실했다면 환경에 STEEL_PASSWORD를 새로 지정해 저장·배포한 뒤 gateway를 다시 시작하세요.', 'error':'비밀번호를 확인한 뒤 다시 시도하세요.', 'busy':'잠시 후 다시 시도하세요.', 'footer':'브라우저는 VPS에서 실행됩니다.'},
 'en': {'title':'Your VPS browser, ready.', 'intro':'Enter your installation password to open Steel Browser.', 'password':'Password', 'button':'Open browser', 'help':'Where to find your password', 'step':'Hostinger Docker Manager → {project} → Manage → Logs', 'detail':'In auth-init logs, copy the Password value under the first-login message and paste it here.', 'note':'This is not your Hostinger account or VPS root password. The username steel is handled automatically.', 'lost':'If you set your own password, use it instead. If lost, set a new STEEL_PASSWORD in Environment, save and deploy, then restart gateway.', 'error':'Check your password and try again.', 'busy':'Please wait a moment and try again.', 'footer':'Your browser runs on the VPS.'}}

def fingerprint():
    line=next(x for x in AUTH_FILE.read_text().splitlines() if x.startswith('steel:'))
    value=line.split(':',1)[1]
    if not value.startswith(('$2y$','$2b$','$2a$')): raise ValueError('unsupported hash')
    return value

def password_ok(password, hashed):
    if not 16<=len(password)<=72 or any(ord(c)<32 or ord(c)>126 for c in password): return False
    result=crypt.crypt(password,hashed)
    return bool(result) and hmac.compare_digest(result,hashed)

def session_ok(cookie,hashed):
    try:
        parsed=SimpleCookie();parsed.load(cookie)
        token=parsed[COOKIE].value
    except (KeyError,ValueError,CookieError): return False
    with LOCK:
        item=SESSIONS.get(hashlib.sha256(token.encode()).hexdigest())
    return bool(item and item[0]>time.time() and hmac.compare_digest(item[1],hashed))

def language(query,header):
    chosen=parse_qs(query).get('lang',[''])[0]
    if chosen in TEXT:return chosen
    # Respect the first preferred language; unsupported preferences fall back to English.
    return 'ko' if header.lower().split(',')[0].split(';')[0].strip().startswith('ko') else 'en'

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass  # No credentials or session tokens in access logs.
    def reply(self,status,body=b'',headers=None):
        self.send_response(status)
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','same-origin')
        self.send_header('Content-Security-Policy',"default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'")
        for k,v in (headers or {}).items():self.send_header(k,v)
        self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    def page(self,error='',status=200):
        lang=language(urlsplit(self.path).query,self.headers.get('Accept-Language','en'))
        values={**TEXT[lang],'lang':lang,'project':os.environ.get('STEEL_PROJECT','steel-browser')}
        values['step']=values['step'].format(project=values['project'])
        values['message']=values.get(error,'')
        body=TEMPLATE
        for key,value in values.items():body=body.replace('{{'+key+'}}',html.escape(value))
        self.reply(status,body.encode(),{'Content-Type':'text/html; charset=utf-8'})
    def do_GET(self):
        path=urlsplit(self.path).path
        if path=='/_steel/login':return self.page()
        if path!='/verify':return self.reply(404)
        try:hashed=fingerprint()
        except (OSError,ValueError,StopIteration):return self.reply(503)
        if session_ok(self.headers.get('Cookie',''),hashed):return self.reply(204)
        auth=self.headers.get('Authorization','')
        if auth.startswith('Basic ') and len(auth)<512:
            try:
                username,password=base64.b64decode(auth[6:],validate=True).decode('ascii').split(':',1)
                if username=='steel' and VERIFY.acquire(blocking=False):
                    try:
                        if password_ok(password,hashed):return self.reply(204)
                    finally:VERIFY.release()
            except (ValueError,UnicodeError):pass
        return self.reply(401)
    def do_POST(self):
        if urlsplit(self.path).path!='/_steel/login':return self.reply(404)
        # Host is supplied by nginx from the incoming host, never X-Forwarded-Host.
        if self.headers.get('Origin')!='https://'+self.headers.get('Host',''):
            return self.reply(403)
        if self.headers.get('Content-Type','').split(';')[0]!='application/x-www-form-urlencoded':return self.reply(415)
        try:length=int(self.headers.get('Content-Length','0'))
        except ValueError:return self.reply(400)
        if not 0<length<=1024:return self.reply(413)
        if not VERIFY.acquire(blocking=False):return self.page('busy',429)
        try:
            password=parse_qs(self.rfile.read(length).decode('ascii'),max_num_fields=4).get('password',[''])[0]
            hashed=fingerprint()
            if not password_ok(password,hashed):return self.page('error',401)
            token=secrets.token_urlsafe(32)
            with LOCK:
                now=time.time()
                for key in list(SESSIONS):
                    if SESSIONS[key][0]<=now:del SESSIONS[key]
                if len(SESSIONS)>=256:del SESSIONS[next(iter(SESSIONS))]
                SESSIONS[hashlib.sha256(token.encode()).hexdigest()]=(now+TTL,hashed)
            return self.reply(303,headers={'Location':'/','Set-Cookie':f'{COOKIE}={token}; Path=/; Secure; HttpOnly; SameSite=Strict; Max-Age={TTL}'})
        except (OSError,ValueError,StopIteration,UnicodeError):return self.page('busy',503)
        finally:VERIFY.release()

if __name__=='__main__':
    class Server(ThreadingHTTPServer):
        daemon_threads=True
        def get_request(self):
            connection,address=super().get_request();connection.settimeout(10);return connection,address
    Server(('0.0.0.0',8081),Handler).serve_forever()
