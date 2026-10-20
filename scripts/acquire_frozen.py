"""Restore hash-pinned accessible inputs; keep existing bytes immutable."""
from pathlib import Path
import argparse,json,hashlib,requests,datetime
R=Path(__file__).resolve().parents[1]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--kind',choices=['data','literature','all'],default='all');args=ap.parse_args();items=[]
 if args.kind in ['all','data']:items+=json.loads((R/'manifests/data_acquisition.json').read_text())
 if args.kind in ['all','literature']:
  for s in json.loads((R/'manifests/source_register_audited.json').read_text(encoding='utf8'))['sources']:
   if s.get('full_text_downloaded'):items.append({'path':s['local_path'],'sha256':s['sha256'],'url':s.get('download_url') or s.get('candidate_acquisition_url')})
 log=[]
 for item in items:
  p=R/item['path'];p.parent.mkdir(parents=True,exist_ok=True)
  try:
   if p.exists():b=p.read_bytes();status='verified_local'
   else:
    if not item.get('url'):raise ValueError('No verified acquisition URL')
    response=requests.get(item['url'],timeout=(20,60));response.raise_for_status();b=response.content;status='downloaded'
   digest=hashlib.sha256(b).hexdigest()
   if digest!=item['sha256']:raise ValueError('Hash mismatch; refusing to use or overwrite changed input')
   if not p.exists():p.write_bytes(b)
   log.append({'path':item['path'],'status':status,'sha256':digest})
  except Exception as e:log.append({'path':item['path'],'status':'failed','error':repr(e)})
 out=R/'runs'/datetime.datetime.now(datetime.timezone.utc).strftime('acquire_%Y%m%dT%H%M%SZ');out.mkdir(exist_ok=True)
 (out/'acquisition_log.json').write_text(json.dumps(log,indent=2));print('Verified',sum(x['status']!='failed' for x in log),'of',len(log),'pinned inputs')
 if any(x['status']=='failed' for x in log):raise SystemExit('See acquisition log; public availability/versions may have changed. Other simulations can proceed independently.')
if __name__=='__main__':main()
