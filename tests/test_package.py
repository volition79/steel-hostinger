import sys
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
        self.assertIn('${STEEL_HOST:?', env['DOMAIN'])


if __name__ == '__main__':
    unittest.main()
