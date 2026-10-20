"""Acquire lawful public papers/metadata. Never execute downloaded code."""
from pathlib import Path
import json, hashlib, datetime, re, urllib.request, urllib.error, concurrent.futures
ROOT=Path(__file__).resolve().parents[1]
def sha(b): return hashlib.sha256(b).hexdigest()
def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':'AcademicResearchPilot/0.1 (local noncommercial literature audit)'})
    with urllib.request.urlopen(req,timeout=50) as r: return r.read(),r.url,dict(r.headers)
def one(s):
    s=dict(s); events=[]; s['draft_entry']=True
    aid=re.search(r'arxiv.org/(?:abs|pdf|html)/(\d+\.\d+)',s['primary_url'])
    urls=[]
    if aid:
        try:
            b,u,h=fetch('https://arxiv.org/abs/'+aid[1]); html=b.decode('utf8','replace')
            path=ROOT/'literature/raw'/f"{s['id']}_arxiv_metadata.html"; path.write_bytes(b)
            metas=dict(re.findall(r'<meta\s+name="([^"]+)"\s+content="([^"]*)"',html))
            s['verified_metadata']={k:v for k,v in metas.items() if k.startswith('citation_')}
            authors=re.findall(r'<meta\s+name="citation_author"\s+content="([^"]*)"',html)
            s['verified_metadata']['authors']=authors
            lic=re.search(r'<a[^>]+href="([^"]+)"[^>]*>\s*(?:view license|license)',html)
            s['license']=lic[1] if lic else 'Not established; arXiv access does not imply redistribution permission'
            pdf=metas.get('citation_pdf_url','https://arxiv.org/pdf/'+aid[1]);urls.append(pdf)
            s['metadata_sha256']=sha(b);s['metadata_path']=str(path.relative_to(ROOT))
        except Exception as e: events.append({'url':s['primary_url'],'error':repr(e)})
    cand=s.get('candidate_acquisition_url')
    if cand and cand not in urls: urls.append(cand)
    s['acquisition_attempts']=events
    for url in urls:
        try:
            b,u,h=fetch(url)
            if not b.startswith(b'%PDF'): raise ValueError('Response is not PDF')
            p=ROOT/'literature/raw'/f"{s['id']}.pdf"
            if p.exists() and p.read_bytes()!=b: raise ValueError('Immutable input already differs')
            p.write_bytes(b);s.update(full_text_downloaded=True,sha256=sha(b),local_path=str(p.relative_to(ROOT)),download_url=u,download_bytes=len(b),retrieved_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),http_last_modified=h.get('Last-Modified'),inspection_status='downloaded_pending_fulltext_audit')
            break
        except Exception as e: events.append({'url':url,'error':repr(e)})
    print(s['id'],s['full_text_downloaded'],s.get('download_bytes',''),flush=True)
    return s
def main():
    sources=json.loads((ROOT/'protocol/inputs/source_register.json').read_text(encoding='utf8'))['sources']
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex: results=list(ex.map(one,sources))
    (ROOT/'manifests/source_register_audited.json').write_text(json.dumps({'audit_stage':'acquisition and metadata; claim audit separately in evidence cards','sources':results},indent=2),encoding='utf8')
    for name,url in [('volare_home','https://volare.unime.it/'),('volare_docs','https://volare.unime.it/documentation'),('uzh_finance_faq','https://www.df.uzh.ch/de/studies/studierendenleben-und-beratung/abschlussarbeiten/faq.html')]:
        try:
            b,u,h=fetch(url);(ROOT/'literature/raw'/f'{name}.html').write_bytes(b);print(name,len(b),flush=True)
        except Exception as e: print(name,repr(e),flush=True)
if __name__=='__main__':main()
