"""Run only against a disposable local Steel stack (creates/edits a browser tab).

STEEL_TEST_URL=https://localhost:18443 STEEL_TEST_PASSWORD=... python tests/live_smoke.py
Requires Playwright + installed Chromium. Local TLS uses a self-signed certificate.
"""
import base64
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

base = os.environ.get('STEEL_TEST_URL', 'https://localhost:18443').rstrip('/')
if not base.startswith('https://localhost:'):
    raise SystemExit('This smoke test is restricted to the disposable localhost stack')
password = os.environ['STEEL_TEST_PASSWORD']
auth = 'Basic ' + base64.b64encode(('steel:' + password).encode()).decode()
# Only this test process trusts the local self-signed TLS terminator.
os.environ['NODE_TLS_REJECT_UNAUTHORIZED'] = '0'
checks = []
with sync_playwright() as p:
    unauth = p.request.new_context(ignore_https_errors=True)
    for path in ('/', '/api/v1/sessions', '/v1/sessions/debug', '/ws/'):
        assert unauth.get(base + path).status == 401, path
    assert unauth.get(base + '/', headers={'Authorization': 'Basic c3RlZWw6d3Jvbmc='}).status == 401
    checks.append('unauthenticated UI/API/viewer/WS path and wrong password denied')
    api = p.request.new_context(ignore_https_errors=True, extra_http_headers={'Authorization': auth})
    direct = api.get(base + '/v1/sessions')
    prefixed = api.get(base + '/api/v1/sessions')
    assert direct.status == prefixed.status == 200
    session = direct.json()['sessions'][0]
    assert session['websocketUrl'].startswith(base.replace('https:', 'wss:'))
    assert session['debugUrl'].startswith(base + '/v1/')
    checks.append('API prefix rewrite and generated HTTPS/WSS URLs')
    remote = p.chromium.connect_over_cdp(session['websocketUrl'], headers={'Authorization': auth})
    tab = remote.contexts[0].pages[0]
    tab.goto('https://example.com', wait_until='domcontentloaded')
    assert 'Example Domain' in tab.title()
    checks.append('authenticated root CDP and external navigation')
    tab.set_content('<html><body style="margin:0;background:#e0f4ff"><h1>Steel remote input test</h1>'
                    '<input id="probe" style="position:absolute;left:100px;top:150px;width:300px;height:50px">'
                    '</body></html>')
    browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
    context = browser.new_context(ignore_https_errors=True,
                                  http_credentials={'username': 'steel', 'password': password})
    page = context.new_page()
    frames_received = []
    page.on('websocket', lambda ws: ws.on('framereceived', lambda data: frames_received.append(len(data))))
    page.goto(base + '/', wait_until='networkidle')
    frame = page.frame_locator('iframe')
    canvas = frame.locator('canvas').first
    canvas.wait_for(state='visible')
    page.wait_for_timeout(1500)
    box = canvas.bounding_box()
    remote_size = tab.evaluate('({width:innerWidth,height:innerHeight})')
    page.mouse.click(box['x'] + 200 * box['width'] / remote_size['width'],
                     box['y'] + 175 * box['height'] / remote_size['height'])
    page.keyboard.type('Steel input works')
    tab.wait_for_function('document.querySelector("#probe").value === "Steel input works"')
    assert any(n > 1000 for n in frames_received), 'no viewer image frames'
    checks.append('real viewer frames, remote canvas click and keyboard input')
    out = Path('.local'); out.mkdir(exist_ok=True)
    page.screenshot(path=str(out / 'live-smoke.png'), full_page=True)
    (out / 'live-smoke.json').write_text(json.dumps({'passed': checks}, indent=2))
    print(json.dumps({'passed': checks}, indent=2))
    browser.close()
    remote.close()
