"""Normalize prose spacing only; preserve originals, URLs, code and identifiers."""
from pathlib import Path
import re
R=Path(__file__).resolve().parents[1]
def polish_segment(s):
 s=s.replace('preregistered','prespecified').replace('Seventeen evidence cards','Eighteen evidence cards')
 for a,b in [('RQunits','RQ units'),('sessionM','session M'),('empiricalHinterpretation','empirical H interpretation'),('inferentialH','inferential H'),('source-supportedSPYRMquarticity','source-supported SPYRM quarticity'),('dailyGaussian','daily Gaussian'),('localPDFs','local PDFs'),('localPDF','local PDF'),('missingNYSEsessions','missing NYSE sessions'),('missingNYSE','missing NYSE'),('publicSPYdevelopment','public SPY development'),('SPYRMquarticity','SPYRM quarticity'),('PDFpp','PDF pages '),('PDFp','PDF page '),('S09PDF','S09 PDF')]:s=s.replace(a,b)
 # Explicit prose substitutions avoid changing scientific notation and identifiers.
 for a,b in [('PattonTable','Patton Table'),('preprintTable','preprint Table'),
             ('naiveH','naive H'),('spotH','spot H'),('lowH','low H'),
             ('restoreH','restore H'),('absoluteH','absolute H'),('latentH','latent H'),
             ('calibratedH','calibrated H'),('LevelB','Level B'),('rawRQ','raw RQ'),
             ('DividingRQ','Dividing RQ'),('ExactM','Exact M'),
             ('expectedXNYSsessions','expected XNYS sessions'),
             ('independentKL','independent KL'),('kernelPDF','kernel PDF'),
             ('runIDs','run IDs'),('logIV','log IV'),('logRV','log RV'),
             ('minuteRV','minute RV'),('publicSPY','public SPY'),
             ('finite-bandH','finite-band H'),('SPY750','SPY 750'),('SPYRQ','SPY RQ'),
             ('SankhyaB','Sankhya B'),('s 13571','s13571'),
             ('nbaa 049','nbaa049'),('nbp 001','nbp001'),
             ('was-1.496','was -1.496')]:s=s.replace(a,b)
 s=re.sub(r'([,;])(?=\S)',r'\1 ',s)
 s=re.sub(r'\b(MCSE|SE)(?=\d)',r'\1 ',s)
 s=re.sub(r'\bDOI(?=\d)', 'DOI ',s)
 s=re.sub(r'(?<=%)(?=[A-Za-z])',' ',s)
 s=re.sub(r'(?<=\d)(?=\([A-Za-z])',' ',s)
 s=re.sub(r'(\d(?:\.\d+)?[eE])\s+([+-]?\d+)',r'\1\2',s)
 return s
def polish_text(s):
 out=[];fence=False
 for line in s.splitlines(keepends=True):
  if line.lstrip().startswith('```'):fence=not fence;out.append(line);continue
  if fence:out.append(line);continue
  parts=re.split(r'(`[^`]*`|!?\[[^\]]*\]\([^)]+\)|https?://\S+|\bv\d[\w.]*\b)',line)
  out.append(''.join(p if i%2 else polish_segment(p) for i,p in enumerate(parts)))
 return ''.join(out)
def main():
 paths=list(R.glob('*.md'))
 for folder in ['manuscript','literature/cards','data','thesis']:
  paths+=list((R/folder).glob('*.md'))
 paths+=list((R/'protocol').glob('*.md'));paths+=list((R/'literature').glob('*.md'))
 for p in paths:p.write_text(polish_text(p.read_text(encoding='utf8')),encoding='utf8')
 print('Polished',len(paths),'owned Markdown files; original inputs untouched')
if __name__=='__main__':main()
