import importlib.util
import sys
from pathlib import Path
import unittest
from unittest.mock import patch
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import login

class LoginTests(unittest.TestCase):
    def test_existing_bcrypt_hash(self):
        hashed=login.crypt.crypt('a-correct-password-123',login.crypt.mksalt(login.crypt.METHOD_BLOWFISH))
        self.assertTrue(login.password_ok('a-correct-password-123',hashed))
        self.assertFalse(login.password_ok('a-different-password',hashed))
        self.assertFalse(login.password_ok('a'*73,hashed))
    def test_sessions_expire_and_password_change_revokes(self):
        token='test-token';key=login.hashlib.sha256(token.encode()).hexdigest()
        with patch.dict(login.SESSIONS,{key:(time.time()+10,'hash')},clear=True):
            self.assertTrue(login.session_ok(login.COOKIE+'='+token,'hash'))
            self.assertFalse(login.session_ok(login.COOKIE+'='+token,'newhash'))
            self.assertFalse(login.session_ok('','hash'))
            login.SESSIONS[key]=(time.time()-1,'hash')
            self.assertFalse(login.session_ok(login.COOKIE+'='+token,'hash'))
    def test_languages(self):
        self.assertEqual(login.language('','ko-KR, en;q=0.9'),'ko')
        self.assertEqual(login.language('','en-US, ko;q=0.8'),'en')
        self.assertEqual(login.language('lang=en','ko-KR'),'en')
    def test_cookie_parser_malformed(self):
        for cookie in ['garbage','x="','__Host-steel_session=']:
            self.assertFalse(login.session_ok(cookie,'hash'))
