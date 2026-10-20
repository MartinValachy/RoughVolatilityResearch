from pathlib import Path
import json,urllib.request,concurrent.futures,hashlib
R=Path(__file__).resolve().parents[1]
def acquire(pair):
 name,url=pair
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'local-research-audit'}),timeout=30) as f:b=f.read()
  (R/'literature/raw'/name).write_bytes(b);print(name,len(b),flush=True)
 except Exception as e:print(name,repr(e),flush=True)
def main():
 commit=json.loads((R/'manifests/data_acquisition.json').read_text())[0]['commit']
 urls=[('S09.pdf','https://fba.um.edu.mo/wp-content/uploads/RePEc/doc/202537.pdf'),('D05.pdf','https://www.jstatsoft.org/article/download/v104i08/4398'),('SYZ_author_page.html','https://lingnan.sysu.edu.cn/en/faculty/ZhangChen')]
 for p in ['R/HARmodel.R','R/realizedMeasures.R','man/rQuar.Rd']:
  urls.append((p.rsplit('/',1)[-1],f'https://raw.githubusercontent.com/jonathancornelissen/highfrequency/{commit}/{p}'))
 for p in ['estimateFractalIndex.m','estimateFractalIndexRobust.m','illustration_run.m']:
  urls.append((p,'https://raw.githubusercontent.com/mbennedsen/Semiparametric-Estimation-of-Fractal-Index/main/'+p))
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:list(ex.map(acquire,urls))
if __name__=='__main__':main()
