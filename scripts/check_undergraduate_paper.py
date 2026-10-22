"""Independent paper-fact and TeX consistency audit using the standard library."""
from pathlib import Path
import copy
import csv
import json
import math
import re

from phase1_support import ROOT,record_run,sha


def check():
    paper=ROOT/'paper'
    facts=json.loads((paper/'generated/claims.json').read_text(encoding='utf-8'))
    metadata=json.loads((ROOT/'results/undergraduate_paper_inputs.json').read_text(encoding='utf-8'))
    cache={}
    def expected(f):
        name=f['source']
        if name not in cache:
            if f['kind']=='json':cache[name]=json.loads((ROOT/name).read_text(encoding='utf-8'))
            else:
                with (ROOT/name).open(encoding='utf-8',newline='') as stream:cache[name]=list(csv.DictReader(stream))
        data=cache[name]
        if f['kind']=='json':
            value=data
            for part in f['field'].split('.'):value=value[part]
            return float(value)
        selected=[]
        for row in data:
            match=True
            for key,value in f['selector'].items():
                if isinstance(value,(int,float)):match &= math.isclose(float(row[key]),value,rel_tol=0,abs_tol=1e-13)
                else:match &= row[key]==value
            if match:selected.append(float(row[f['field']]))
        op=f['operation']
        if op=='value':
            if len(selected)!=1:raise AssertionError('Nonunique independent selector')
            value=selected[0]
        elif op=='min':value=min(selected)
        elif op=='max':value=max(selected)
        elif op=='count_ge':value=sum(x>=f['threshold'] for x in selected)
        else:raise AssertionError('Unknown operation')
        return value*f['scale']
    def verify_fact(f):
        value=expected(f)
        assert math.isclose(value,f['value'],rel_tol=1e-12,abs_tol=1e-13),f['key']
        display=f'{value:,.0f}' if f['kind']=='json' and f['digits']==0 else f'{value:.{f["digits"]}f}'
        assert display==f['display'],f['key']
    for f in facts:verify_fact(f)
    altered=copy.deepcopy(facts[0]);altered['value']+=1
    try:verify_fact(altered)
    except AssertionError:pass
    else:raise AssertionError('Planted altered paper fact not rejected')
    macros=(paper/'generated/facts.tex').read_text(encoding='utf-8')
    for f in facts:assert '\\csname fact@'+f['key']+'\\endcsname{'+f['display']+'}' in macros
    narrative=['main.tex','theory.tex']+[name for name in ['breadth.tex','breadth_appendix.tex'] if (paper/name).exists()]
    content='\n'.join((paper/name).read_text(encoding='utf-8') for name in narrative)
    sources=[paper/name for name in narrative]+list((paper/'generated').glob('*_table.tex'))
    refs=set(re.findall(r'\\Fact\{([^}]+)\}','\n'.join(p.read_text(encoding='utf-8') for p in sources)))
    keys={f['key'] for f in facts}
    assert refs<=keys,refs-keys
    assert len(keys)==len(facts)
    bibliography=(paper/'references.tex').read_text(encoding='utf-8')
    citations=set()
    for group in re.findall(r'\\cite\{([^}]+)\}',content):citations.update(group.split(','))
    bibkeys=set(re.findall(r'\\bibitem\{([^}]+)\}',bibliography))
    assert citations==bibkeys,(citations,bibkeys)
    labels=re.findall(r'\\label\{([^}]+)\}',content)
    assert len(labels)==len(set(labels))
    for label in re.findall(r'\\(?:ref|eqref)\{([^}]+)\}',content):assert label in labels,label
    for source,digest in metadata['source_inputs_sha256'].items():assert sha(ROOT/source)==digest,source
    for file,digest in metadata['generated_files_sha256'].items():assert sha(paper/file)==digest,file
    # Explicit scope/interpretation gates; no automatic scientific truth assertion.
    for wording in ['post-result','not identify latent','not a new confirmatory','Human','does not evaluate returns']:
        assert wording.lower() in content.lower(),wording
    for cfg,checks in [('configs/source_replication.json',{'EWMA_lambda':.94,'EWMA_warmup':126,'bootstrap_draws':3999,'target_annual_volatility':.1,'weight_cap':1}),('configs/side_project.json',{'paths':128,'days':504,'fine_steps_per_day':780})]:
        payload=json.loads((ROOT/cfg).read_text(encoding='utf-8'))
        for name,value in checks.items():assert payload[name]==value
    summary=dict(status='passed_checks',paper_input_run_id=metadata['run_id'],named_facts_checked=len(facts),
        unique_facts_referenced=len(refs),all_printed_macros_match_sources=True,planted_altered_fact_rejected=True,
        bibliography_entries=len(bibkeys),citations_resolve=True,tex_references_resolve=True,
        code_sha256=sha(__file__),paper_source_sha256=sha(paper/'main.tex'),theory_source_sha256=sha(paper/'theory.tex'),
        source_check='csv/json/math independent of pandas fact preparation',
        human_peer_review_completed=False,published_online=False,sealed_data_opened=False)
    run=record_run('undergraduate_paper_check',summary)
    (ROOT/'results/undergraduate_paper_check.json').write_text(json.dumps(dict(summary,run_id=run),indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(run_id=run,facts_checked=len(facts),referenced_facts=len(refs),citations=len(bibkeys),status='passed_checks')))


if __name__=='__main__':check()
