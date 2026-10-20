"""Small maintainer-distributed SPY pilot; downloads immutable commit-pinned files.

VOLARE currently requires an account. No accounts are created or credentials
read by this script. Dataset contents are locally retained, not redistributed.
"""
from pathlib import Path
import urllib.request,json,hashlib,datetime
R=Path(__file__).resolve().parents[1]
def get(u):
 with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'local-research-pilot'}),timeout=45) as h:return h.read()
def main():
 repo='jonathancornelissen/highfrequency'
 commit=json.loads(get('https://api.github.com/repos/'+repo+'/commits/master'))['sha']
 rows=[]
 for remote,local in [('data/SPYRM.rda','data/raw/SPYRM.rda'),('man/SPYRM.Rd','data/raw/SPYRM.Rd'),('DESCRIPTION','data/raw/highfrequency_DESCRIPTION'),('R/data.R','data/raw/highfrequency_data.R'),('data/sampleOneMinuteData.rda','data/raw/sampleOneMinuteData.rda')]:
  url=f'https://raw.githubusercontent.com/{repo}/{commit}/{remote}';b=get(url);p=R/local
  if p.exists() and p.read_bytes()!=b:raise ValueError('Existing raw input differs')
  p.write_bytes(b);rows.append({'url':url,'commit':commit,'path':local,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'license':'Package license in DESCRIPTION; dataset-specific provenance/redistribution unresolved','purpose':'local pilot only'})
 (R/'manifests/data_acquisition.json').write_text(json.dumps(rows,indent=2),encoding='utf8')
 print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
