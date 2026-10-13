"""Disposable Docker volume: initialize, preserve, reject, rotate authentication."""
import os, sys, subprocess, uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from build_compose import build
D=os.environ.get('STEEL_TEST_DOCKER','docker')
service=build()['services']['auth-init']
script=service['command'][0].replace('$$','$')
volume='steel-auth-test-'+uuid.uuid4().hex[:12]
def run(pw='', host='steel.example.com'):
 return subprocess.run([D,'run','--rm','--network','none','-v',volume+':/auth','-e','STEEL_HOST='+host,'-e','STEEL_PASSWORD='+pw,'--entrypoint','/bin/sh',service['image'],'-ec',script],capture_output=True,text=True)
def digest():
 return subprocess.check_output([D,'run','--rm','--network','none','-v',volume+':/auth','--entrypoint','/bin/sh',service['image'],'-c','sha256sum /auth/users'],text=True).split()[0]
try:
 first=run();assert first.returncode==0,first.stderr
 assert 'Password: ' in first.stdout
 before=digest()
 again=run();assert again.returncode==0 and 'Password: ' not in again.stdout
 assert digest()==before
 for bad in ['short','a'*73,'a'*16+'\n'+'b'*16,'a'*16+'\r']:
  result=run(bad);assert result.returncode!=0
  assert digest()==before
 assert run(host='https://invalid.example.com/path').returncode!=0
 assert digest()==before
 assert run('replacement-test-password-123').returncode==0
 assert digest()!=before
 print('PASS: generated once, hash retained, invalid passwords/host rejected without mutation, override rotates')
finally:
 subprocess.run([D,'volume','rm',volume],stdout=subprocess.DEVNULL,check=False)
