"""Bind editable lecture text/tables/chart caches to its checked content source."""
from pathlib import Path
import argparse, json, math, re, zipfile
from xml.etree import ElementTree as ET
from phase1_support import ROOT, record_run, sha

NS={'a':'http://schemas.openxmlformats.org/drawingml/2006/main',
    'c':'http://schemas.openxmlformats.org/drawingml/2006/chart',
    'r':'http://schemas.openxmlformats.org/package/2006/relationships'}


def normalize(s):return re.sub(r'\s+',' ',str(s)).strip()


def check(path):
    content=json.loads((ROOT/'docs/presentation/lecture_content.json').read_text(encoding='utf8'))
    facts={r['key']:r for r in json.loads((ROOT/'paper/generated/claims.json').read_text())}
    facts.update({'B_'+r['key']:r for r in json.loads((ROOT/'paper/generated/breadth_claims.json').read_text())})
    count=0;chart_count=0;table_count=0
    with zipfile.ZipFile(path) as z:
        if z.testzip() is not None:raise AssertionError('PPTX CRC failed')
        actual={int(re.search(r'slide(\d+)\.xml$',n).group(1)) for n in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml',n)}
        assert actual==set(range(1,len(content['slides'])+1))
        for slide in content['slides']:
            number=slide['slide'];part=f'ppt/slides/slide{number}.xml';xml=ET.fromstring(z.read(part))
            text=normalize(' '.join(e.text or '' for e in xml.findall('.//a:t',NS)))
            for expected in [slide['title'],slide['body'],slide['caption']]:
                assert normalize(expected) in text,(number,expected[:100]);count+=1
            notes=ET.fromstring(z.read(f'ppt/notesSlides/notesSlide{number}.xml'))
            note_text=normalize(' '.join(e.text or '' for e in notes.findall('.//a:t',NS)))
            assert normalize(slide['notes']) in note_text;count+=1
            assert all(key in facts for key in slide['sourceKeys'])
            if slide['table']:
                for row in slide['table']:
                    for cell in row:assert normalize(cell) in text;count+=1
                table_count+=1
            if slide['chart']:
                rels=ET.fromstring(z.read(f'ppt/slides/_rels/slide{number}.xml.rels'))
                paths=[r.attrib['Target'] for r in rels if r.attrib['Type'].endswith('/chart')]
                assert len(paths)==1
                target=paths[0]
                # Exported targets are relative to ppt/slides.
                from posixpath import normpath,join
                chart_path=target.lstrip('/') if target.startswith('/') else normpath(join('ppt/slides',target))
                chart=ET.fromstring(z.read(chart_path))
                series=chart.findall('.//c:ser',NS)
                assert len(series)==len(slide['chart']['series'])
                for model,encoded in zip(slide['chart']['series'],series):
                    values=[float(e.text) for e in encoded.findall('./c:val//c:pt/c:v',NS)]
                    assert len(values)==len(model['values'])
                    for a,b in zip(values,model['values']):assert a==float(b);count+=1
                    for key,value in zip(model.get('keys',[]),values):
                        assert math.isclose(value,float(facts[key]['value']),rel_tol=1e-12,abs_tol=1e-13);count+=1
                chart_count+=1
    # Independent arithmetic for the invented teaching examples.
    assert math.isclose(sum(v*v for v in [.01,-.01,.02]),.0006)
    assert math.isclose(sum(v**4 for v in [.01,-.01,.02]),1.8e-7)
    assert math.isclose(.94*10+.06*20,10.6)
    assert math.isclose(math.log(2)/(2*math.log(2)),.5)
    result=dict(status='passed_checks',slides=len(content['slides']),editable_charts=chart_count,
        editable_tables=table_count,text_note_table_chart_checks=count,presentation_sha256=sha(path),
        content_sha256=sha(ROOT/'docs/presentation/lecture_content.json'),
        source_claim_map_sha256=sha(ROOT/'paper/generated/claims.json'),
        breadth_claim_map_sha256=sha(ROOT/'paper/generated/breadth_claims.json'),
        source_checks=[json.loads((ROOT/'results'/name).read_text())['run_id'] for name in
                       ['undergraduate_paper_check.json','breadth_paper_check.json']],
        invented_examples_checked=True,chart_rounding_significant_digits=14,
        native_PowerPoint_execution_verified=False,
        boundary='Content/source binding and selected arithmetic; human comprehension and application rendering remain separate',
        code_sha256=sha(__file__))
    run=record_run('university_lecture_check',result)
    (ROOT/'results/university_lecture_check.json').write_text(json.dumps(dict(result,run_id=run),indent=2)+'\n')
    print(json.dumps(dict(result,run_id=run)))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--presentation',type=Path,required=True)
    check(p.parse_args().presentation)
