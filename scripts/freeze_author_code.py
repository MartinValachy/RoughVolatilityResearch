from pathlib import Path
import urllib.request,json,hashlib,re
R=Path(__file__).resolve().parents[1];repo='mbennedsen/Semiparametric-Estimation-of-Fractal-Index'
def get(u):
 with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'local-research-audit'}),timeout=25) as f:return f.read()
def main():
 commit=json.loads(get('https://api.github.com/repos/'+repo+'/commits/main'))['sha'];folder=R/'literature/code/Bennedsen2020'/commit;folder.mkdir(parents=True,exist_ok=True);rows=[]
 for name in ['README.md','estimateFractalIndex.m','estimateFractalIndexRobust.m','illustration_run.m']:
  url=f'https://raw.githubusercontent.com/{repo}/{commit}/{name}';b=get(url);p=folder/name;p.write_bytes(b);s=b.decode('utf8','replace')
  rows.append({'path':str(p.relative_to(R)),'url':url,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'external_execution_or_network_tokens':re.findall(r'(?im)^.*(?:system\(|unix\(|webread\(|urlread\(|eval\(|!curl|!wget).*$ ',s),'executed':False})
 obj={'repository':repo,'commit':commit,'license':'No repository license file in inspected inventory; do not redistribute code','review_scope':'README, interfaces, key estimator formulas, dependency and external-command scan; not a complete line-by-line mathematical audit','required_missing_dependency':'Author requires external simFBM(H,n); not supplied by this repository','files':rows,'execution':'None. Downloaded third-party code was never executed.'}
 (R/'manifests/replication_code_review.json').write_text(json.dumps(obj,indent=2));print('Pinned',len(rows),'author code files at',commit)
if __name__=='__main__':main()
