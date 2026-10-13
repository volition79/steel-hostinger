"""Hostinger-only bootstrap. No web listener; only own gateway is reconciled."""
import copy
import fcntl
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request

NAME = re.compile(r'[a-z0-9][a-z0-9_-]{0,62}\Z')
BASE = re.compile(r'(?:^|\.)(srv[0-9]+\.hstgr\.cloud)\Z')
TOKEN = re.compile(r'[A-Za-z0-9_-]+\Z')
MANAGED = 'steel-hostinger-auto-v1'

class Pending(Exception): pass

def run(args):
    p = subprocess.run(['docker', *args], capture_output=True, timeout=90)
    if p.returncode:
        raise Pending('docker_operation_failed')  # Never leak inspect/env or command output.
    return p.stdout.decode()

def labels(c): return c.get('Config', {}).get('Labels') or {}
def env(c): return dict(x.split('=',1) for x in c.get('Config',{}).get('Env',[]) if '=' in x)
def networks(c): return set(c.get('NetworkSettings',{}).get('Networks',{})) - {'host','none','bridge'}
def running(c): return c.get('State',{}).get('Running',False)
def host_valid(h):
    return (len(h)<=253 and '.' in h and not h.endswith('.invalid') and
            all(re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?',x) for x in h.split('.')))

def discover(items, self_id, daemon_name, explicit=''):
    own=[c for c in items if len(self_id)>=12 and c['Id'].startswith(self_id)]
    if len(own)!=1: raise Pending('bootstrap_identity_missing')
    own=own[0]; project=labels(own).get('com.docker.compose.project','')
    if not NAME.fullmatch(project) or labels(own).get('com.docker.compose.service')!='bootstrap':
        raise Pending('bootstrap_identity_invalid')
    proxies=[c for c in items if running(c) and c.get('Config',{}).get('Image','').split('@')[0].split(':')[0]
             in {'traefik','library/traefik','docker.io/library/traefik','docker.io/traefik'}]
    if len(proxies)!=1: raise Pending('traefik_missing_or_ambiguous')
    proxy=proxies[0]; opts={}
    for arg in proxy.get('Config',{}).get('Cmd') or []:
        if arg=='--providers.docker': opts['providers.docker']='true'
        if arg.startswith('--') and '=' in arg:
            k,v=arg[2:].split('=',1); opts[k.lower()]=v
    for k,v in env(proxy).items():
        if k.startswith('TRAEFIK_ENTRYPOINTS_') and k.endswith('_ADDRESS'):
            opts['entrypoints.'+k[len('TRAEFIK_ENTRYPOINTS_'):-len('_ADDRESS')].lower()+'.address']=v
        if k.startswith('TRAEFIK_CERTIFICATESRESOLVERS_') and '_ACME_' in k:
            resolver=k[len('TRAEFIK_CERTIFICATESRESOLVERS_'):].split('_ACME_',1)[0].lower()
            opts['certificatesresolvers.'+resolver+'.acme.environment']=v
        if k=='TRAEFIK_PROVIDERS_DOCKER': opts['providers.docker']=v
        if k=='TRAEFIK_PROVIDERS_DOCKER_NETWORK': opts['providers.docker.network']=v
        if k=='TRAEFIK_PROVIDERS_DOCKER_CONSTRAINTS': opts['providers.docker.constraints']=v
        if k=='TRAEFIK_PROVIDERS_DOCKER_ENDPOINT': opts['providers.docker.endpoint']=v
        if k=='TRAEFIK_PROVIDERS_DOCKER_WATCH': opts['providers.docker.watch']=v
    provider=opts.get('providers.docker','').lower()
    if provider not in ('true','1'):
        raise Pending('docker_provider_disabled_or_unconfirmed')
    if (opts.get('providers.docker.constraints') or
        opts.get('providers.docker.endpoint','unix:///var/run/docker.sock')!='unix:///var/run/docker.sock' or
        opts.get('providers.docker.watch','true').lower() not in ('true','1')):
        raise Pending('custom_docker_provider_requires_review')
    entries={k.split('.')[1] for k,v in opts.items() if re.fullmatch(r'entrypoints\.[^.]+\.address',k) and v.split('/')[0].endswith(':443')}
    resolvers={k.split('.')[1] for k in opts if re.match(r'certificatesresolvers\.[^.]+\.acme\.',k)}
    bases=set()
    for candidate in [daemon_name,env(proxy).get('TRAEFIK_HOST','')]:
        if re.fullmatch(r'srv[0-9]+',candidate): candidate += '.hstgr.cloud'
        match=BASE.search(candidate.lower())
        if match: bases.add(match[1])
    # Existing router labels are configuration evidence, not proof of live routing.
    routes=[]
    for c in items:
        if not running(c) or labels(c).get('com.docker.compose.project')==project: continue
        if labels(c).get('traefik.enable')!='true': continue
        if proxy.get('HostConfig',{}).get('NetworkMode')!='host' and not (networks(c)&networks(proxy)): continue
        for k,v in labels(c).items():
            if not (k.startswith('traefik.http.routers.') and k.endswith('.rule')): continue
            hosts=re.findall(r'Host\(`([a-zA-Z0-9.-]+)`\)',v)
            valid=[BASE.search(h.lower()) for h in hosts]
            if not any(valid): continue
            bases.update(m[1] for m in valid if m)
            prefix=k[:-5]; entry=labels(c).get(prefix+'.entrypoints',''); resolver=labels(c).get(prefix+'.tls.certresolver','')
            if TOKEN.fullmatch(entry) and TOKEN.fullmatch(resolver): routes.append((entry,resolver))
    pairs={(a,b) for a in entries for b in resolvers} or set(routes)
    if len(pairs)!=1: raise Pending('https_settings_missing_or_ambiguous')
    entry,resolver=pairs.pop()
    if not TOKEN.fullmatch(entry) or not TOKEN.fullmatch(resolver): raise Pending('https_settings_invalid')
    if len(bases)!=1: raise Pending('hostinger_domain_missing_or_ambiguous')
    base=bases.pop()
    host=explicit or 'steel-'+hashlib.sha256(project.encode()).hexdigest()[:12]+'.'+base
    if not host_valid(host): raise Pending('hostname_invalid')
    for c in items:
        if labels(c).get('com.docker.compose.project')==project: continue
        if any(host in re.findall(r'Host\(`([a-zA-Z0-9.-]+)`\)',v) for k,v in labels(c).items() if k.endswith('.rule')):
            raise Pending('hostname_already_owned')
    if proxy.get('HostConfig',{}).get('NetworkMode')=='host':
        candidates=networks(own)
    else:
        candidates=networks(proxy)
        configured=opts.get('providers.docker.network')
        if configured: candidates &= {configured}
    if len(candidates)!=1: raise Pending('proxy_network_missing_or_ambiguous')
    network=candidates.pop()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}',network): raise Pending('proxy_network_invalid')
    return dict(project=project,host=host,base=base,network=network,entrypoint=entry,resolver=resolver,host_proxy=proxy.get('HostConfig',{}).get('NetworkMode')=='host')

def public_addresses(host):
    """TLS-verified DNS lookup independent of the VPS's local hostname mapping."""
    result=set()
    try:
        for record_type,version in ((1,4),(28,6)):
            query=urllib.parse.urlencode({'name':host,'type':record_type,
                                         'edns_client_subnet':'0.0.0.0/0'})
            with urllib.request.urlopen('https://dns.google/resolve?'+query,timeout=6) as response:
                raw=response.read(65537)
            if len(raw)>65536: raise ValueError('oversized response')
            data=json.loads(raw)
            if data.get('Status')!=0 or data.get('TC',False):
                raise ValueError('DNS query unsuccessful')
            for answer in data.get('Answer',[]):
                if answer.get('type')!=record_type: continue
                address=ipaddress.ip_address(answer['data'])
                if address.version!=version or not address.is_global:
                    raise ValueError('non-public address')
                result.add(str(address))
    except (OSError,ValueError,KeyError,TypeError,AttributeError):
        raise Pending('public_dns_unavailable') from None
    if not result: raise Pending('public_dns_no_addresses')
    return result

def verify_dns(plan):
    def addresses(host):
        try:
            return {str(ipaddress.ip_address(x[4][0]))
                    for x in socket.getaddrinfo(host,443,type=socket.SOCK_STREAM)}
        except (OSError,ValueError): raise Pending('dns_not_ready') from None
    host_ips=addresses(plan['host']); base_ips=addresses(plan['base'])
    if host_ips and host_ips==base_ips: return
    # Hostinger can resolve its own srv hostname to 127.0.1.1 inside Docker.
    # Only this specific local alias case permits independent public verification.
    loopback={ip for ip in base_ips if ipaddress.ip_address(ip).is_loopback}
    details=f"host={plan['host']}:{','.join(sorted(host_ips))} base={plan['base']}:{','.join(sorted(base_ips))}"
    if host_ips and loopback and all(ipaddress.ip_address(ip).is_global for ip in host_ips):
        print('Steel DNS local alias / 내부 주소 별칭: '+details,flush=True)
        public_host=public_addresses(plan['host']); public_base=public_addresses(plan['base'])
        if (public_host==public_base and host_ips<=public_host
                and (base_ips-loopback)<=public_base):
            print('Steel DNS verified using public DNS / 공인 DNS 확인 완료: '+','.join(sorted(public_base)),flush=True)
            return
        details+=f" public_host={','.join(sorted(public_host))} public_base={','.join(sorted(public_base))}"
    raise Pending('dns_mismatch '+details)

def inspect_all():
    ids=run(['ps','-aq']).split()
    if len(ids)>200: raise Pending('discovery_limit')
    return json.loads(run(['inspect',*ids])) if ids else []

def route_labels(plan):
    p=plan['project']; prefix='traefik.http.routers.'+p
    return {'traefik.enable':'true','traefik.docker.network':plan['network'],
            'io.steel-hostinger.managed':MANAGED,
            prefix+'.rule':'Host(`'+plan['host']+'`)',prefix+'.entrypoints':plan['entrypoint'],
            prefix+'.tls.certresolver':plan['resolver'],prefix+'.service':p,
            'traefik.http.services.'+p+'.loadbalancer.server.port':'8080'}

def updated(raw, plan):
    result=copy.deepcopy(raw)
    if set(result['services'])!={'bootstrap','auth-init','gateway','steel-api','steel-ui'}:
        raise Pending('unexpected_compose_services')
    gateway=result['services']['gateway']
    old=gateway.get('labels',{})
    if isinstance(old,list): old=dict(x.split('=',1) for x in old)
    if old.get('io.steel-hostinger.managed')!=MANAGED: raise Pending('gateway_not_owned')
    # Never discard unrelated labels or an administrator's custom router.
    wanted=route_labels(plan)
    for k,v in old.items():
        if k not in wanted or (k!='traefik.enable' and v!=wanted[k]): raise Pending('gateway_labels_changed')
    gateway['labels']=wanted
    if plan['host_proxy']: return result
    gateway.setdefault('networks',{})['steel_proxy']={}
    desired={'name':plan['network'],'external':True}
    current=result.setdefault('networks',{}).get('steel_proxy')
    if current and current!=desired: raise Pending('network_changed')
    result['networks']['steel_proxy']=desired
    return result

def atomic(path, data):
    if path.is_symlink(): raise Pending('symlink_refused')
    fd,tmp=tempfile.mkstemp(dir=path.parent,prefix='.steel-')
    try:
        with os.fdopen(fd,'wb') as f:
            f.write(data); f.flush(); os.fsync(f.fileno()); os.fchmod(f.fileno(),0o600)
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def reconcile(plan, items):
    project=plan['project']; path=Path('/docker')/project/'docker-compose.yml'
    own=next(c for c in items if c['Id'].startswith(os.environ['HOSTNAME']))
    if labels(own).get('com.docker.compose.project.config_files')!=str(path): raise Pending('compose_path_mismatch')
    if any(p.is_symlink() for p in (path,path.parent,path.parent.parent)) or not path.is_file() or path.stat().st_size>32768:
        raise Pending('compose_path_invalid')
    cmd=['compose','--project-directory',str(path.parent),'-p',project,'-f',str(path)]
    lockfd=os.open(path.parent/'.steel-bootstrap.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
    with os.fdopen(lockfd,'w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        original=path.read_bytes()
        raw=json.loads(run(cmd+['config','--format','json','--no-interpolate','--no-env-resolution','--no-path-resolution','--no-normalize']))
        proposed=updated(raw,plan)
        # Full resolved equality outside our gateway labels/network + external network.
        before=json.loads(run(cmd+['config','--format','json']))
        fd,tmp=tempfile.mkstemp(dir=path.parent,prefix='.steel-check-',suffix='.json')
        try:
            with os.fdopen(fd,'w') as f: json.dump(proposed,f)
            after=json.loads(run(cmd[:-1]+[tmp,'config','--format','json']))
        finally: os.unlink(tmp)
        for model in (before,after):
            model['services']['gateway'].pop('labels',None)
            model['services']['gateway'].get('networks',{}).pop('steel_proxy',None)
            model.get('networks',{}).pop('steel_proxy',None)
        if before!=after: raise Pending('unrelated_compose_change')
        if path.read_bytes()!=original: raise Pending('compose_changed_concurrently')
        data=(json.dumps(proposed,indent=2)+'\n').encode()
        backup=path.parent/'.steel-compose-before-auto'
        if not backup.exists(): atomic(backup,original)
        if data!=original:
            if path.read_bytes()!=original: raise Pending('compose_changed_concurrently')
            atomic(path,data)
        try:
            run(cmd+['up','-d','--no-deps','--pull','never','gateway'])
        except Exception:
            # Keep desired, recoverable state for the next attempt; never destroy volumes.
            raise Pending('gateway_apply_pending') from None
    return path

def main():
    state=Path('/setup'); state.mkdir(exist_ok=True)
    for attempt in range(90):
        try:
            items=inspect_all()
            plan=discover(items,os.environ.get('HOSTNAME',''),json.loads(run(['info','--format','{{json .Name}}'])),os.environ.get('STEEL_HOST',''))
            verify_dns(plan)
            saved=state/'plan.json'
            if saved.exists() and json.loads(saved.read_text())!=plan: raise Pending('saved_configuration_changed')
            atomic(saved,(json.dumps(plan)+'\n').encode())
            atomic(state/'host',(plan['host']+'\n').encode())
            # Wait for initial deployment to finish its gateway startup before replacing it.
            gateways=[c for c in items if labels(c).get('com.docker.compose.project')==plan['project'] and labels(c).get('com.docker.compose.service')=='gateway']
            if len(gateways)!=1 or gateways[0].get('State',{}).get('Health',{}).get('Status')!='healthy':
                raise Pending('waiting_for_initial_gateway')
            reconcile(plan,items)
            current=[c for c in inspect_all() if labels(c).get('com.docker.compose.project')==plan['project'] and labels(c).get('com.docker.compose.service')=='gateway']
            if len(current)!=1 or not running(current[0]) or any(labels(current[0]).get(k)!=v for k,v in route_labels(plan).items()) or plan['network'] not in networks(current[0]):
                raise Pending('gateway_verification_pending')
            print('Steel setup ready / 설정 완료: https://'+plan['host'],flush=True)
            print('Docker Manager → Open / 열기. TLS issuance may take a few minutes.',flush=True)
            return
        except (Pending,OSError,ValueError,subprocess.TimeoutExpired) as exc:
            reason=str(exc) if isinstance(exc,Pending) else 'discovery_temporarily_unavailable'
            print('Steel setup pending / 설정 대기: '+reason,flush=True)
            time.sleep(5)
    print('Check running Traefik and Hostinger hostname/DNS, then restart this project. / Traefik·호스트명·DNS 확인 후 프로젝트를 다시 시작하세요.',flush=True)
    raise SystemExit(1)

if __name__=='__main__': main()
