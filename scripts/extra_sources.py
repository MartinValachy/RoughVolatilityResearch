from pathlib import Path
import urllib.request,json,re,hashlib,datetime,concurrent.futures
R=Path(__file__).resolve().parents[1]
def get(u):
 with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'local-academic-research'}),timeout=25) as h:return h.read()
def repo(name):
 try:
  meta=json.loads(get('https://api.github.com/repos/'+name)); b=get('https://api.github.com/repos/'+name+'/git/trees/'+meta['default_branch']+'?recursive=1');obj=json.loads(b)
  (R/'literature/raw'/(name.replace('/','_')+'_inventory.json')).write_bytes(b)
  print(name,'branch',meta['default_branch'],'license',meta.get('license'),flush=True)
  print('\n'.join(str({k:x.get(k) for k in ['path','size','sha']}) for x in obj['tree'] if re.search(r'SPY|README|LICENSE|[Dd]ata|[Rr]eplic',x['path']))[:9000],flush=True)
 except Exception as e:print(name,repr(e),flush=True)
def main():
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:list(ex.map(repo,['jgatheral/rough_volatility','jonathancornelissen/highfrequency','mbennedsen/Semiparametric-Estimation-of-Fractal-Index']))
 for sid,url in [('S10','https://www1.unisg.ch/www/afi/afi_web.nsf/SysWebRessources/Corsi_2009/%24FILE/Corsi_2009.pdf'),('S17','https://www.nber.org/system/files/working_papers/t0169/t0169.pdf'),('S20','https://www.nber.org/system/files/working_papers/w22208/w22208.pdf')]:
  try:
   b=get(url)
   if not b.startswith(b'%PDF'):raise ValueError('Not PDF')
   (R/f'literature/raw/{sid}.pdf').write_bytes(b);print(sid,len(b),flush=True)
  except Exception as e:print(sid,repr(e),flush=True)
if __name__=='__main__':main()
