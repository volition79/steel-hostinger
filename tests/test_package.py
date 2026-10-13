import sys
import os
import subprocess
import unittest
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from build_compose import build


class PackageContract(unittest.TestCase):
    def test_distributed_file_matches_generator(self):
        self.assertEqual(yaml.safe_load((ROOT / 'compose.hostinger.yaml').read_text()), build())

    def test_only_authenticated_gateway_is_routed(self):
        services = build()['services']
        for name, service in services.items():
            self.assertNotIn('ports', service, name)
            self.assertIn('@sha256:', service['image'])
        self.assertEqual(services['steel-api']['labels']['traefik.enable'], 'false')
        self.assertEqual(services['steel-ui']['labels']['traefik.enable'], 'false')
        self.assertIsInstance(services['gateway']['labels'], list)
        self.assertEqual(services['gateway']['depends_on']['auth-init']['condition'],
                         'service_completed_successfully')

    def test_public_urls_use_https_and_wss(self):
        env = build()['services']['steel-api']['environment']
        self.assertEqual(env['USE_SSL'], 'true')
        self.assertEqual('${STEEL_HOST:-setup.invalid}', env['DOMAIN'])

    def test_hostname_validation(self):
        script = (ROOT / 'validate-host.sh').read_text()
        for host in ['steel.example.com', 'steel-hostinger.srv123.hstgr.cloud']:
            r = subprocess.run(['sh', '-ec', script], env={**os.environ, 'STEEL_HOST': host}, capture_output=True)
            self.assertEqual(r.returncode, 0, host)
        for host in ['', 'setup.invalid', 'https://steel.example.com', 'steel.example.com/path',
                     'localhost:18443', '-bad.example.com', 'bad..example.com', 'good.com\nevil.com']:
            r = subprocess.run(['sh', '-ec', script], env={**os.environ, 'STEEL_HOST': host}, capture_output=True)
            self.assertNotEqual(r.returncode, 0, host)
            self.assertIn(b'SETUP REQUIRED', r.stderr)

    def test_readiness_and_profile(self):
        services = build()['services']
        self.assertEqual(services['gateway']['depends_on']['steel-api']['condition'], 'service_healthy')
        self.assertIn('browser:/data/browser', services['steel-api']['volumes'])
        self.assertEqual(services['steel-api']['environment']['CHROME_USER_DATA_DIR'], '/data/browser')
        self.assertTrue(services['steel-api']['init'])


if __name__ == '__main__':
    unittest.main()
