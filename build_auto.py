"""Standalone automatic Hostinger installer; manual installer remains separate."""
import yaml
from build_compose import build, ROOT

def build_auto(image=None):
    pins=yaml.safe_load((ROOT/'images.yaml').read_text())
    image=image or pins.get('bootstrap')
    if not image:
        raise ValueError('Bootstrap image is not published yet; pass --image for a local build.')
    result=build(); services=result['services']
    read=(ROOT/'read-auto-host.sh').read_text().replace('$','$$')
    services['bootstrap']={
        'image':image,'restart':'no','init':True,'read_only':True,
        'cap_drop':['ALL'],'security_opt':['no-new-privileges:true'],
        'mem_limit':'192m','cpus':0.5,'pids_limit':64,
        'environment':{'STEEL_HOST':'${STEEL_HOST:-}'},
        'tmpfs':['/tmp:size=32m,mode=1777'],
        'volumes':['/var/run/docker.sock:/var/run/docker.sock',
                   '/docker/${COMPOSE_PROJECT_NAME}:/docker/${COMPOSE_PROJECT_NAME}', 'setup:/setup'],
        'labels':{'traefik.enable':'false'},
        'logging':{'driver':'json-file','options':{'max-size':'5m','max-file':'2'}}}
    for name in ('auth-init','steel-api','gateway'):
        services[name]['volumes'].append('setup:/setup:ro')
        services[name]['command'][0]=read+services[name]['command'][0]
        services[name].setdefault('depends_on',{})['bootstrap']={'condition':'service_started'}
    services['steel-api']['environment'].pop('DOMAIN')
    services['steel-api']['command'][0]=read+'export DOMAIN="$$STEEL_HOST"\n'+(ROOT/'profile-start.sh').read_text().replace('$','$$')
    gateway=services['gateway']
    gateway['labels']={'traefik.enable':'false','io.steel-hostinger.managed':'steel-hostinger-auto-v1'}
    gateway['networks']={'default':{}}
    gateway['healthcheck']={'test':['CMD-SHELL','test "$$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/)" = 401'],
                            'interval':'5s','timeout':'3s','retries':20}
    result['volumes']['setup']={}
    return result

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--image', help='Verified bootstrap image reference (local development or published digest)')
    args=parser.parse_args()
    (ROOT/'compose.auto.yaml').write_text(yaml.safe_dump(build_auto(args.image),sort_keys=False))
