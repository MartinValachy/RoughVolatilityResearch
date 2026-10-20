"""Inspect public metadata and author repositories, with no authentication bypass."""
from pathlib import Path
from urllib.request import urlopen,Request
import re,json,hashlib,datetime
R=Path(__file__).resolve().parents[1]
def get(url):
 with urlopen(Request(url,headers={'User-Agent':'local-research-audit'}),timeout=45) as r:return r.read()
def save(name,url):
 try:
  b=get(url);(R/'literature/raw'/name).write_bytes(b);print(name,len(b),flush=True);return b
 except Exception as e: print(name,repr(e),flush=True);return b''
b=save('bennedsen_research.html','https://sites.google.com/site/mbennedsen/research')
links=sorted(set(re.findall(r'https?[^\s<>"\\]+',b.decode('utf8','replace'))))
print('\n'.join(x for x in links if 'github' in x or 'zenodo' in x),flush=True)
for repo in ['jamesgatheral/rough_volatility','JimGatheral/rough_volatility','mbennedsen/rough_volatility','mbennedsen/decoupling']:
 b=save(repo.replace('/','_')+'_repo.json','https://api.github.com/repos/'+repo)
 if b:
  obj=json.loads(b);branch=obj['default_branch'];tree=save(repo.replace('/','_')+'_tree.json','https://api.github.com/repos/'+repo+'/git/trees/'+branch+'?recursive=1')
  if tree:
   paths=[x['path'] for x in json.loads(tree)['tree']];print(repo,paths[:150],flush=True)
save('uzh_theses.html','https://www.oec.uzh.ch/de/studies/theses.html')
save('S09_alternate.pdf','https://fba.um.edu.mo/wp-content/uploads/2025/10/VolatilityForecast_draft8.pdf')
