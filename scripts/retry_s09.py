from pathlib import Path
import requests,json,hashlib,time
R=Path(__file__).resolve().parents[1];url='https://fba.um.edu.mo/wp-content/uploads/RePEc/doc/202537.pdf';events=[];payload=bytearray()
for attempt in range(3):
 try:
  headers={'User-Agent':'AcademicResearchPilot/0.1'}
  if payload:headers['Range']=f'bytes={len(payload)}-'
  with requests.get(url,headers=headers,stream=True,timeout=(20,40)) as r:
   events.append({'attempt':attempt,'status':r.status_code,'content_range':r.headers.get('Content-Range'),'content_length':r.headers.get('Content-Length')})
   r.raise_for_status()
   if payload and r.status_code!=206:payload=bytearray()
   for chunk in r.iter_content(32768):payload.extend(chunk)
  if not payload.startswith(b'%PDF'):raise ValueError('Non-PDF response')
  from pypdf import PdfReader
  import io
  reader=PdfReader(io.BytesIO(payload));reader.pages[-1].extract_text()
  (R/'literature/raw/S09.pdf').write_bytes(payload);events.append({'result':'success','bytes':len(payload),'pages':len(reader.pages),'sha256':hashlib.sha256(payload).hexdigest()});break
 except Exception as e:events.append({'attempt':attempt,'failure':repr(e),'received_bytes':len(payload)})
(R/'manifests/S09_retrieval_log.json').write_text(json.dumps({'url':url,'attempts':events},indent=2));print(json.dumps(events,indent=2))
