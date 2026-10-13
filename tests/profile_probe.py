"""Local test stack only: seed/check a persistent cookie in the default profile."""
import os, sys, time
from playwright.sync_api import sync_playwright
os.environ['NODE_TLS_REJECT_UNAUTHORIZED']='0'
with sync_playwright() as p:
 import base64
 auth='Basic '+base64.b64encode(('steel:'+os.environ['STEEL_TEST_PASSWORD']).encode()).decode()
 b=p.chromium.connect_over_cdp('wss://localhost:18443/',headers={'Authorization':auth})
 c=b.contexts[0]
 if sys.argv[1]=='seed':
  c.add_cookies([{'name':'steel_persistence_probe','value':os.environ['STEEL_TEST_COOKIE_NONCE'],'domain':'example.com','path':'/','expires':time.time()+86400,'secure':True}])
  # Chromium batches cookie disk writes; crash tests cover committed data.
  time.sleep(35)
 else:
  assert any(x['name']=='steel_persistence_probe' and x['value']==os.environ['STEEL_TEST_COOKIE_NONCE'] for x in c.cookies('https://example.com'))
  print('PASS: persistent cookie survives API container recreation')
 b.close()
