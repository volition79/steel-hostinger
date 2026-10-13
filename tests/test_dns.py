import io
import json
import socket
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch
import bootstrap as b

PLAN={'host':'steel-test.srv123.hstgr.cloud','base':'srv123.hstgr.cloud'}
PUBLIC={'201.18.219.95','2a02:4780:5e:62ad::1'}

def resolver(host_ips,base_ips):
    def resolve(host,*args,**kwargs):
        ips=host_ips if host==PLAN['host'] else base_ips
        return [(socket.AF_INET,socket.SOCK_STREAM,6,'',(ip,443)) for ip in ips]
    return resolve

class DnsRegression(unittest.TestCase):
    def test_normal_match_never_calls_public_dns(self):
        with patch.object(b.socket,'getaddrinfo',side_effect=resolver(PUBLIC,PUBLIC)) as local, patch.object(b,'public_addresses') as public:
            b.verify_dns(PLAN)
            self.assertEqual(local.call_count,2)
            public.assert_not_called()

    def test_loopback_base_with_public_match(self):
        for base in ({'127.0.1.1'},{'::1'},{'127.0.1.1','201.18.219.95'}):
            with self.subTest(base=base), patch.object(b.socket,'getaddrinfo',side_effect=resolver(PUBLIC,base)), patch.object(b,'public_addresses',return_value=PUBLIC) as public, redirect_stdout(io.StringIO()) as log:
                b.verify_dns(PLAN)
                self.assertEqual(public.call_count,2)
                self.assertIn('공인 DNS 확인 완료',log.getvalue())

    def test_mismatching_public_dns_is_rejected(self):
        with patch.object(b.socket,'getaddrinfo',side_effect=resolver(PUBLIC,{'127.0.1.1'})), patch.object(b,'public_addresses',side_effect=[PUBLIC,{'8.8.8.8'}]), redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(b.Pending,'dns_mismatch.*public_base'): b.verify_dns(PLAN)

    def test_unexpected_local_address_still_rejected(self):
        for host,base in [({'8.8.8.8'},{'127.0.1.1'}),(PUBLIC,{'127.0.1.1','8.8.8.8'})]:
            with self.subTest(host=host,base=base), patch.object(b.socket,'getaddrinfo',side_effect=resolver(host,base)), patch.object(b,'public_addresses',return_value=PUBLIC), redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(b.Pending,'dns_mismatch'): b.verify_dns(PLAN)

    def test_ordinary_mismatch_does_not_trigger_fallback(self):
        with patch.object(b.socket,'getaddrinfo',side_effect=resolver(PUBLIC,{'8.8.8.8'})), patch.object(b,'public_addresses') as public:
            with self.assertRaisesRegex(b.Pending,'dns_mismatch.*host='): b.verify_dns(PLAN)
            public.assert_not_called()

    def test_fallback_failure_is_not_bypassed(self):
        with patch.object(b.socket,'getaddrinfo',side_effect=resolver(PUBLIC,{'127.0.1.1'})), patch.object(b,'public_addresses',side_effect=b.Pending('public_dns_unavailable')), redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(b.Pending,'public_dns_unavailable'): b.verify_dns(PLAN)

    def test_public_A_AAAA_queries(self):
        responses=[{'Status':0,'Answer':[{'type':5,'data':'alias.example.'},{'type':1,'data':'201.18.219.95'}]}, {'Status':0,'Answer':[{'type':28,'data':'2a02:4780:5e:62ad::1'}]}]
        with patch.object(b.urllib.request,'urlopen',side_effect=[io.BytesIO(json.dumps(r).encode()) for r in responses]) as fetch:
            self.assertEqual(b.public_addresses(PLAN['base']),PUBLIC)
            self.assertIn('type=1&',fetch.call_args_list[0].args[0])
            self.assertIn('type=28&',fetch.call_args_list[1].args[0])
            self.assertEqual(fetch.call_args.kwargs['timeout'],6)

    def test_public_bad_response_fails_closed(self):
        for payload in [b'not json',b'{}',b'null',b'{"Status":2}',b'{"Status":0,"TC":true}',b'{"Status":0,"Answer":[{"type":1,"data":"127.0.1.1"}]}',b'x'*65537]:
            with self.subTest(payload=payload[:80]),patch.object(b.urllib.request,'urlopen',return_value=io.BytesIO(payload)):
                with self.assertRaisesRegex(b.Pending,'public_dns_unavailable'): b.public_addresses(PLAN['base'])
        with patch.object(b.urllib.request,'urlopen',side_effect=[io.BytesIO(b'{"Status":0}'),io.BytesIO(b'{"Status":0}')]):
            with self.assertRaisesRegex(b.Pending,'public_dns_no_addresses'): b.public_addresses(PLAN['base'])
        with patch.object(b.urllib.request,'urlopen',side_effect=OSError('offline')):
            with self.assertRaisesRegex(b.Pending,'public_dns_unavailable'): b.public_addresses(PLAN['base'])
