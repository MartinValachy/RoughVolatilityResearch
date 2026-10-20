from pathlib import Path
from pypdf import PdfReader
import json
R=Path(__file__).resolve().parents[1]
for p in sorted((R/'literature/raw').glob('*.pdf')):
    if (R/'literature/text'/f'{p.stem}_pages.json').exists():continue
    reader=PdfReader(p)
    pages=[page.extract_text() or '' for page in reader.pages]
    (R/'literature/text'/f'{p.stem}.txt').write_text('\n\n'.join(f'=== PDF PAGE {i+1} ===\n'+t for i,t in enumerate(pages)),encoding='utf8')
    (R/'literature/text'/f'{p.stem}_pages.json').write_text(json.dumps(pages,ensure_ascii=False),encoding='utf8')
    print(p.stem,len(pages),sum(map(len,pages)),flush=True)
