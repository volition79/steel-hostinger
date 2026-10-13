import copy, sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import bootstrap as b
from build_auto import build_auto

def fixture(host=False):
 own={'Id':'a'*64,'Config':{'Labels':{'com.docker.compose.project':'steel-demo','com.docker.compose.service':'bootstrap'}},'NetworkSettings':{'Networks':{'steel-demo_default':{}}}}
 proxy={'Id':'b'*64,'State':{'Running':True},'Config':{'Image':'traefik:v3','Cmd':['--providers.docker=true','--entrypoints.websecure.address=:443','--certificatesresolvers.letsencrypt.acme.email=test@example.com'],'Env':[]},'NetworkSettings':{'Networks':{'proxy_default':{}}},'HostConfig':{'NetworkMode':'host' if host else 'bridge'}}
 return [own,proxy]

class BootstrapTests(unittest.TestCase):
 def test_without_buzz(self):
  for host in (True,False):
   plan=b.discover(fixture(host),'a'*12,'srv123')
   self.assertEqual(plan['base'],'srv123.hstgr.cloud')
   self.assertEqual(plan['network'],'steel-demo_default' if host else 'proxy_default')
   self.assertTrue(plan['host'].startswith('steel-'))
 def test_environment_traefik_configuration(self):
  items=fixture();items[1]['Config']['Cmd']=[]
  items[1]['Config']['Env']=['TRAEFIK_PROVIDERS_DOCKER=true','TRAEFIK_ENTRYPOINTS_WEBSECURE_ADDRESS=:443','TRAEFIK_CERTIFICATESRESOLVERS_LE_ACME_EMAIL=x@example.com']
  self.assertEqual(b.discover(items,'a'*12,'srv123')['resolver'],'le')
 def test_disabled_provider(self):
  items=fixture();items[1]['Config']['Cmd'][0]='--providers.docker=false'
  with self.assertRaisesRegex(b.Pending,'provider'):b.discover(items,'a'*12,'srv123')

 def test_custom_provider_rejected(self):
  for flag in ['--providers.docker.constraints=Label(`custom`,`required`)','--providers.docker.endpoint=tcp://other:2375','--providers.docker.watch=false']:
   items=fixture();items[1]['Config']['Cmd'].append(flag)
   with self.assertRaisesRegex(b.Pending,'requires_review'):b.discover(items,'a'*12,'srv123')

 def test_missing_ambiguous_and_collision(self):
  for items,name in [(fixture()[:1],'srv123'),(fixture()+[fixture()[1]],'srv123'),(fixture(),'docker-desktop')]:
   with self.assertRaises(b.Pending):b.discover(items,'a'*12,name)
  items=fixture();items[1]['Config']['Env']=['TRAEFIK_HOST=srv456.hstgr.cloud']
  with self.assertRaisesRegex(b.Pending,'ambiguous'):b.discover(items,'a'*12,'srv123')
  items=fixture();p=b.discover(items,'a'*12,'srv123')
  items.append({'Id':'c'*64,'Config':{'Labels':{'traefik.http.routers.other.rule':'Host(`'+p['host']+'`)'}}})
  with self.assertRaisesRegex(b.Pending,'owned'):b.discover(items,'a'*12,'srv123')
 def test_preserves_services_networks_and_repeated_update(self):
  raw=build_auto('steel-bootstrap:test'); plan=b.discover(fixture(),'a'*12,'srv123')
  result=b.updated(raw,plan)
  for name in set(raw['services'])-{'gateway'}:self.assertEqual(raw['services'][name],result['services'][name])
  self.assertIn('default',result['services']['gateway']['networks'])
  self.assertEqual(result,b.updated(result,plan))
  result['services']['gateway']['labels']['traefik.http.routers.foreign.rule']='Host(`foreign.example.com`)'
  with self.assertRaises(b.Pending):b.updated(result,plan)
 def test_socket_only_in_helper_and_no_public_ports(self):
  services=build_auto('steel-bootstrap:test')['services']
  for name,service in services.items():
   self.assertNotIn('ports',service)
   if name!='bootstrap':self.assertNotIn('docker.sock',str(service))
  self.assertEqual(services['gateway']['labels']['traefik.enable'],'false')
  for name in ('auth-init','steel-api','gateway'):
   self.assertEqual(services[name]['depends_on']['bootstrap']['condition'],'service_started')

if __name__=='__main__':unittest.main()
