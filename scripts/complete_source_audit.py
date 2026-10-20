from pathlib import Path
import urllib.request,json,re,hashlib,concurrent.futures,difflib,datetime,sys
R=Path(__file__).resolve().parents[1]
def get(u):
 with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'local-research-audit/0.1'}),timeout=25) as h:return h.read()
def query(s):
 title=s['title']
 if s['id']=='S03':title='Consistent estimation for fractional stochastic volatility model under high-frequency asymptotics'
 from urllib.parse import urlencode
 try:
  b=get('https://api.crossref.org/works?'+urlencode({'query.title':title,'rows':3}));(R/f"literature/raw/{s['id']}_crossref.json").write_bytes(b)
  out=[]
  for v in json.loads(b)['message']['items']:
   actual=' '.join(v.get('title',[]));score=difflib.SequenceMatcher(None,title.lower(),actual.lower()).ratio()
   out.append({'title':actual,'DOI':v.get('DOI'),'authors':v.get('author'),'container':v.get('container-title'),'published':v.get('published'),'score_title_match':score,'license':v.get('license'),'type':v.get('type')})
  return s['id'],out
 except Exception as e:return s['id'],[{'lookup_failure':repr(e)}]
def main():
 p=R/'manifests/source_register_audited.json';obj=json.loads(p.read_text());sources=obj['sources']
 if '--offline' in sys.argv:matches={s['id']:s.get('crossref_candidates',[]) for s in sources}
 else:
  with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:matches=dict(ex.map(query,[s for s in sources if s['id'].startswith('S')]))
 for sid,title,authors,url in [('D05','Analyzing Intraday Financial Data in R: The highfrequency Package','Boudt; Kleen; Sjoerup','https://www.jstatsoft.org/article/download/v104i08/4398'),('S21','Multi-factor approximation of rough volatility models','Abi Jaber; El Euch','https://arxiv.org/pdf/1801.10359v3'),('S22','Things we think we know','L.C.G.Rogers','https://www.skokholm.co.uk/wp-content/uploads/2019/11/TWTWKpaper.pdf')]:
  if not any(s['id']==sid for s in sources):sources.append({'id':sid,'title':title,'authors':authors,'primary_url':url,'download_url':url,'full_text_downloaded':False,'priority':'targeted_addition','license':None,'acquisition_attempts':[]})
 for s in sources:
  sid=s['id'];pdf=R/f'literature/raw/{sid}.pdf';s['crossref_candidates']=matches.get(sid,[])
  if pdf.exists() and pdf.read_bytes().startswith(b'%PDF'):
   s.update(full_text_downloaded=True,local_path=str(pdf.relative_to(R)),sha256=hashlib.sha256(pdf.read_bytes()).hexdigest(),download_bytes=pdf.stat().st_size)
   s['version_policy']='Exact local bytes hashed; arXiv author version is distinct from journal version. Crossref candidates require author/title reconciliation.'
   from pypdf import PdfReader
   reader=PdfReader(pdf);first=reader.pages[0].extract_text() or '';s['pdf_pages']=len(reader.pages);s.pop('cover_excerpt',None);s['cover_first_line']=first.splitlines()[0].strip() if first.strip() else 'Image-only cover; OCR not performed'
   version=re.search(r'arXiv:\s*(\d+\.\d+v\d+)',first)
   if version:s['arxiv_local_version']=version[1];s['download_url']='https://arxiv.org/pdf/'+version[1]
   html=R/f'literature/raw/{sid}_arxiv_metadata.html'
   if html.exists():
    licenses=re.findall(r'href="([^"]*(?:creativecommons.org|arxiv.org/licenses)[^"]*)"',html.read_text(encoding='utf8'))
    if licenses:s['license']=licenses[0]
  if sid=='S02':s['download_url']='https://arxiv.org/pdf/2203.13820';s['version_note']='Lawful arXiv author version; journal DOI 10.1007/s13571-024-00322-2'
  if sid=='S03':s['journal_successor']={'title':'Consistent estimation for fractional stochastic volatility model under high-frequency asymptotics','DOI':'10.1111/mafi.12354','year':2022,'journal':'Mathematical Finance','volume':32,'issue':4,'pages':'1086-1132'}
  if sid=='S17':s['download_url']='https://www.nber.org/system/files/working_papers/t0169/t0169.pdf'
  if sid=='S20':s['download_url']='https://www.nber.org/system/files/working_papers/w22208/w22208.pdf'
  if sid=='S10':s['download_url']='https://statmath.wu.ac.at/~hauser/LVs/FinEtricsQF/References/Corsi2009JFinEtrics_LMmodelRealizedVola.pdf'
  if sid=='S13':s['download_url']='https://public.econ.duke.edu/~boller/Published_Papers/joe_11b.pdf'
  if sid=='S09':s['acquisition_attempts'] += [{'url':'https://fba.um.edu.mo/wp-content/uploads/RePEc/doc/202537.pdf','error':'First retrieval IncompleteRead (2683159 received,1042299 remaining); retry recorded separately'}]
  if sid=='S09' and pdf.exists():s['download_url']='https://fba.um.edu.mo/wp-content/uploads/RePEc/doc/202537.pdf';s['successful_retrieval_log']='manifests/S09_retrieval_log.json'
  if s.get('license') is None:s['license']='Not established; public reading does not grant redistribution rights'
  s['method_audited']=False;s['targeted_method_audit']=(R/f'literature/cards/{sid}.md').exists();s['inspection_status']='targeted_evidence_card' if s['targeted_method_audit'] else 'acquired_not_yet_audited' if s['full_text_downloaded'] else 'metadata_or_access_block_only'
  if sid=='S01':s['journal_identity']={'year':2018,'DOI':'10.1080/14697688.2017.1393551','verification':'Publisher record inspected20October2026; downloaded author version separately identified'}
  if sid=='S04':s['journal_identity']={'year':2023,'DOI':'10.1016/j.jeconom.2022.06.009','verification':'Publisher record inspected20October2026; author version remains separate'}
  if sid=='S05':s['journal_identity']={'year':2022,'DOI':'10.1093/jjfinec/nbaa049','verification':'Author/institution publication record inspected20October2026'}
  if sid=='S14':s['acquisition_attempts']+=[{'url':'https://shephard.scholars.harvard.edu/sites/g/files/omnuum7741/files/ecta08.pdf','error':'Local HTTP403; publishedPDF accessible via web reader, first4PDFpages inspected; no local acquisition claimed'}]
  if s.get('arxiv_local_version'):s['download_url']='https://arxiv.org/pdf/'+s['arxiv_local_version']
  if s.get('acquisition_attempts'):s['acquisition_attempts']=list({json.dumps(v,sort_keys=True):v for v in s['acquisition_attempts']}.values())
 obj.update(audit_date='2026-10-20',source_version_policy='Preserve draft register as original; current corpus and targeted evidence audit here',sources=sources)
 p.write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf8')
 print('Source register updated;',sum(s['full_text_downloaded'] for s in sources),'local PDFs;',len(sources),'source entries including3targeted additions')
if __name__=='__main__':main()
