"""Independent standard-library audit of every A13 paper fact and display."""
from pathlib import Path
import copy,csv,json,math,re
from phase1_support import ROOT,record_run,sha


def check():
    paper=ROOT/'paper';facts=json.loads((paper/'generated/breadth_claims.json').read_text())
    metadata=json.loads((ROOT/'results/breadth_paper_inputs.json').read_text());cache={}
    def verify(f):
        name=f['source']
        if name not in cache:
            if name.endswith('.json'):cache[name]=json.loads((ROOT/name).read_text())
            else:
                with (ROOT/name).open(newline='',encoding='utf8') as stream:cache[name]=list(csv.DictReader(stream))
        if f.get('operation')=='sum_json_fields':value=sum(cache[name][key] for key in f['field'].split('+'))
        elif name.endswith('.json'):value=cache[name][f['field']]
        else:
            def match(row):
                return all((float(row[key])==wanted if isinstance(wanted,(float,int)) else row[key]==wanted) for key,wanted in f['selector'].items())
            selected=[r for r in cache[name] if match(r)];assert len(selected)==1
            value=float(selected[0][f['field']]) if selected[0][f['field']] else math.nan
        value=float(value)*f['scale'];value=None if not math.isfinite(value) else value
        assert (value is None and f['value'] is None) or (value is not None and f['value'] is not None and math.isclose(value,f['value'],rel_tol=1e-12,abs_tol=1e-12)),f['key']
        expected='withheld' if value is None else f"{value:,.{f['digits']}f}"
        assert expected==f['display'],f['key']
    for fact in facts:verify(fact)
    planted=copy.deepcopy(facts[0]);planted['value']+=1
    try:verify(planted)
    except AssertionError:pass
    else:raise AssertionError('Planted breadth paper fact escaped')
    macros=(paper/'generated/breadth_facts.tex').read_text()
    for fact in facts:assert '\\csname breadth@'+fact['key']+'\\endcsname{'+fact['display']+'}' in macros
    narrative=[paper/name for name in ['main.tex','reader_guide.tex','study.tex','breadth.tex','breadth_appendix.tex'] if (paper/name).exists()]
    sources=narrative+list((paper/'generated').glob('breadth_*_table.tex'))
    refs=set(re.findall(r'\\BF\{([^}]+)\}','\n'.join(p.read_text() for p in sources)))
    assert refs<={f['key'] for f in facts}
    for name,digest in metadata['source_inputs_sha256'].items():assert sha(ROOT/name)==digest
    for name,digest in metadata['generated_files_sha256'].items():assert sha(paper/name)==digest
    text='\n'.join(p.read_text() for p in narrative)
    for wording in ['follow-up','not untouched','missing','withheld','post-result']:
        assert wording in text.lower(),wording
    result=dict(status='passed_checks',named_facts_checked=len(facts),unique_facts_referenced=len(refs),
        planted_altered_fact_rejected=True,source_check='csv/json/math independent of pandas preparation',
        code_sha256=sha(__file__),paper_source_sha256={p.name:sha(p) for p in narrative},input_run=metadata['run_id'])
    run=record_run('breadth_paper_check',result)
    (ROOT/'results/breadth_paper_check.json').write_text(json.dumps(dict(result,run_id=run),indent=2)+'\n')
    print(json.dumps(dict(run_id=run,facts=len(facts),referenced=len(refs),status='passed_checks')))


if __name__=='__main__':check()
