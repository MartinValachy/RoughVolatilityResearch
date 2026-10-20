from pathlib import Path
import requests,zipfile,io,json,hashlib,datetime
R=Path(__file__).resolve().parents[1]
url='https://lingnan.sysu.edu.cn/lingnan-prod/sites/default/files/inline-files/data.zip'
record={'author_landing_page':'https://lingnan.sysu.edu.cn/en/faculty/ZhangChen','link_label':'Data for Shi, Yu, Zhang, Realized Volatility Forecasting','url':url,'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'attempting','policy':'Inspect ZIP filenames only; never open data members or evaluate2020-2025 values'}
try:
 with requests.get(url,stream=True,timeout=(20,40)) as r:
  record['http_status']=r.status_code;r.raise_for_status();chunks=[];size=0
  for b in r.iter_content(65536):
   size+=len(b)
   if size>30_000_000:raise ValueError('Archive exceeds30MB small-pilot cap; download stopped before parsing')
   chunks.append(b)
 b=b''.join(chunks);z=zipfile.ZipFile(io.BytesIO(b));record['inventory']=[{'name':x.filename,'uncompressed_bytes':x.file_size,'compressed_bytes':x.compress_size} for x in z.infolist()]
 p=R/'data/sealed/SYZ_official_data.zip'
 if p.exists() and p.read_bytes()!=b:raise ValueError('Immutable input differs')
 p.write_bytes(b);record.update(status='acquired_sealed_filename_inventory_only',bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),local_path=str(p.relative_to(R)),license='Not supplied by author landing page; redistribution not established')
except Exception as e:record.update(status='blocked_or_unavailable',failure=repr(e))
(R/'manifests/official_replication_inventory.json').write_text(json.dumps(record,indent=2));print(json.dumps(record,indent=2)[:7500])
