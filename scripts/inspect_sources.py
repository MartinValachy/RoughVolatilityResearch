from pathlib import Path
import re,json,sys,urllib.request
R=Path(__file__).resolve().parents[1]
if sys.argv[1]=='frontend':
 s=(R/'literature/raw/volare_frontend.js').read_text()
 pats=[r'baseURL.{0,170}',r'.{0,80}/api/.{0,130}',r'.{0,90}SPY.{0,100}',r'.{0,100}assetList.{0,150}',r'.{0,90}getSymbols.{0,180}']
 for pat in pats:
  for m in re.finditer(pat,s):print(m.group())
elif sys.argv[1]=='pages':
 sid=sys.argv[2]; pages=json.loads((R/f'literature/text/{sid}_pages.json').read_text())
 for i in map(int,sys.argv[3:]):print(f'=== {sid} PDF PAGE {i} ===\n'+pages[i-1].replace('\0',''))
elif sys.argv[1]=='find':
 sid=sys.argv[2];pat=sys.argv[3];pages=json.loads((R/f'literature/text/{sid}_pages.json').read_text())
 for i,s in enumerate(pages):
  for m in re.finditer(pat,s,re.I):print(f'{sid} PDF p{i+1}: '+s[max(0,m.start()-170):m.end()+450].replace('\0','').replace('\n',' '))
elif sys.argv[1]=='url':
 url=sys.argv[2]; name=sys.argv[3];b=urllib.request.urlopen(url,timeout=45).read();(R/'literature/raw'/name).write_bytes(b);print(name,len(b))
