"""Add independently checked A13 facts/tables to the complete working paper."""
from pathlib import Path
import argparse,json,math,shutil
import pandas as pd
from phase1_support import ROOT,record_run,sha


def prepare(report_directory=None):
    paper=ROOT/'paper';generated=paper/'generated';facts=[];inputs={};cache={}
    analysis=json.loads((ROOT/'results/etf_breadth_analysis.json').read_text())
    check=json.loads((ROOT/'results/etf_breadth_independent_check.json').read_text())
    if check['status']!='passed_checks' or check['analysis_run_id']!=analysis['run_id']:raise ValueError('A13 check does not bind current analysis')
    cfg=json.loads((ROOT/'configs/etf_breadth.json').read_text())
    def fact(key,source,field,selector=None,scale=1,digits=0):
        path=ROOT/source;inputs[source]=sha(path)
        if source.endswith('.json'):
            value=json.loads(path.read_text())[field]
        else:
            if source not in cache:
                columns=['symbol','frequency_seconds','case','lag_max',field] if '_H.' in source else ['symbol','frequency_seconds','case',field]
                # Read only fields used by this fixed table/fact family.
                if '_incidence.' in source:columns=['symbol','frequency_seconds','case','RV_material_days','RV_valid_pairs','RV_missing_pairs','RQ_material_days','RQ_valid_pairs']
                elif '_risk.' in source:columns=['symbol','frequency_seconds','case','post_warmup_origins','mean_absolute_weight_difference','mean_absolute_uncapped_difference','origins_above_5pp','cap_attenuation_fraction']
                elif '_H.' in source:columns=['symbol','frequency_seconds','case','lag_max','H_tilde']
                pd.read_csv(path,usecols=columns,nrows=5);cache[source]=pd.read_csv(path,usecols=columns)
            frame=cache[source]
            for name,wanted in selector.items():frame=frame[frame[name].eq(wanted)]
            if len(frame)!=1:raise ValueError('Ambiguous breadth fact selector: '+key)
            value=frame.iloc[0][field]
        value=float(value)*scale
        value=None if not math.isfinite(value) else value
        display='withheld' if value is None else f'{value:,.{digits}f}'
        facts.append(dict(key=key,source=source,field=field,selector=selector,scale=scale,digits=digits,value=value,display=display))
        return '\\BF{'+key+'}'
    for key,field in [('pairs','input_symbol_days'),('newPairs','new_symbol_days'),('reusePairs','previous_January_pairs'),('sessions','calendar_dates'),('eligible','primary_eligible_dates_per_fund')]:
        fact(key,'results/etf_breadth_analysis.json',field)
    fact('checks','results/etf_breadth_independent_check.json','scalar_checks')
    fact('members','results/etf_breadth_export_verified.json','member_hashes_verified')
    # SPY398 plus all1,592 ETF pairs:January ETF pairs are counted once.
    value=analysis['calendar_dates']+analysis['input_symbol_days']
    facts.append(dict(key='unionPairs',source='results/etf_breadth_analysis.json',field='calendar_dates+input_symbol_days',
        selector=None,scale=1,digits=0,value=value,display=f'{value:,}',operation='sum_json_fields'))
    cases=[('M','millisecond_time__millisecond_flags'),('L','legacy_time__legacy_flags'),('T','millisecond_time__legacy_flags'),
           ('C','legacy_time__millisecond_flags'),('B','legacy_restore_modern_category_B')]
    labels={15:'15s',30:'30s',60:'1m',300:'5m',900:'15m',1800:'30m'}
    for measure in ['RV','RQ']:
        lines=['\\begin{tabular}{llrrrrr}\\toprule','Fund & Grid & Modern & Legacy & Time only & Cond. only & B restored \\\\ \\midrule']
        for symbol in cfg['panel']:
            for freq in cfg['frequencies_seconds']:
                cells=[symbol,labels[freq]]
                for short,case in cases:
                    sel=dict(symbol=symbol,frequency_seconds=freq,case=case);prefix=symbol+str(freq)+short+measure
                    cells.append(fact(prefix+'N','results/etf_breadth_incidence.csv',measure+'_material_days',sel)+'/'+
                                 fact(prefix+'D','results/etf_breadth_incidence.csv',measure+'_valid_pairs',sel))
                lines.append(' & '.join(cells)+' \\\\')
            if symbol!=cfg['panel'][-1]:lines.append('\\midrule')
        lines.append('\\bottomrule\\end{tabular}')
        (generated/('breadth_'+measure.lower()+'_table.tex')).write_text('\n'.join(lines)+'\n',encoding='utf8',newline='\n')
    lines=['\\begin{tabular}{llrrrrr}\\toprule','Fund & Grid & Modern & Legacy & Time only & Cond. only & B restored \\\\ \\midrule']
    for symbol in cfg['panel']:
        for freq in cfg['frequencies_seconds']:
            cells=[symbol,labels[freq]]
            for short,case in cases:
                cells.append(fact(symbol+str(freq)+short+'H','results/etf_breadth_H.csv','H_tilde',dict(symbol=symbol,frequency_seconds=freq,case=case,lag_max=10),digits=4))
            lines.append(' & '.join(cells)+' \\\\')
        if symbol!=cfg['panel'][-1]:lines.append('\\midrule')
    lines.append('\\bottomrule\\end{tabular}')
    (generated/'breadth_h_table.tex').write_text('\n'.join(lines)+'\n',encoding='utf8',newline='\n')
    lines=['\\begin{tabular}{llrrrrr}\\toprule','Fund & Grid & RV hits/valid & RQ hits/valid & Capped pp & Uncapped pp & Large origins \\\\ \\midrule']
    for symbol in cfg['panel']:
        for freq in [60,300]:
            prefix=symbol+str(freq);sel=dict(symbol=symbol,frequency_seconds=freq,case=cases[1][1])
            fact(prefix+'origins','results/etf_breadth_risk.csv','post_warmup_origins',sel)
            cells=[symbol,labels[freq],'\\BF{'+prefix+'LRVN}/\\BF{'+prefix+'LRVD}',
                '\\BF{'+prefix+'LRQN}/\\BF{'+prefix+'LRQD}']
            for key,field,scale,digits in [('capped','mean_absolute_weight_difference',100,4),('uncapped','mean_absolute_uncapped_difference',100,4),('large','origins_above_5pp',1,0)]:
                cells.append(fact(prefix+key,'results/etf_breadth_risk.csv',field,sel,scale,digits))
            lines.append(' & '.join(cells)+' \\\\')
    lines.append('\\bottomrule\\end{tabular}')
    (generated/'breadth_risk_table.tex').write_text('\n'.join(lines)+'\n',encoding='utf8',newline='\n')
    fact('EFA60attenuation','results/etf_breadth_risk.csv','cap_attenuation_fraction',dict(symbol='EFA',frequency_seconds=60,case=cases[1][1]),100,2)
    fact('TLT60missing','results/etf_breadth_incidence.csv','RV_missing_pairs',dict(symbol='TLT',frequency_seconds=60,case=cases[1][1]))
    if len({f['key'] for f in facts})!=len(facts):raise ValueError('Duplicate breadth fact key')
    macros='\\newcommand{\\BF}[1]{\\csname breadth@#1\\endcsname}\n'+''.join(
        '\\expandafter\\def\\csname breadth@'+f['key']+'\\endcsname{'+f['display']+'}\n' for f in facts)
    (generated/'breadth_facts.tex').write_text(macros,encoding='utf8',newline='\n')
    (generated/'breadth_claims.json').write_text(json.dumps(facts,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n')
    report=json.loads((ROOT/'results/etf_breadth_report.json').read_text())
    source=Path(report_directory) if report_directory else ROOT/'docs/A13'
    for name in ['incidence_rv','cap_comparison']:
        for extension in ['pdf','png']:
            relative='figures/'+name+'.'+extension
            if sha(source/relative)!=report['output_files_sha256'][relative]:raise ValueError('Checked breadth figure changed')
            shutil.copyfile(source/relative,paper/'figures'/('breadth_'+name+'.'+extension))
    generated_files={p.relative_to(paper).as_posix():sha(p) for p in generated.glob('breadth_*')}
    generated_files.update({p.relative_to(paper).as_posix():sha(p) for p in (paper/'figures').glob('breadth_*')})
    result=dict(status='prepared',analysis_run=analysis['run_id'],independent_run=check['run_id'],named_facts=len(facts),
        source_inputs_sha256=inputs,generated_files_sha256=generated_files,code_sha256=sha(__file__))
    run=record_run('breadth_paper_inputs',result)
    (ROOT/'results/breadth_paper_inputs.json').write_text(json.dumps(dict(result,run_id=run),indent=2)+'\n')
    print(json.dumps(dict(run_id=run,named_facts=len(facts))));return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report-directory',type=Path,help='Checked report folder containing figures/; defaults to docs/A13')
    prepare(parser.parse_args().report_directory)
