"""Prepare paper facts, tables and six focused figures from checked outputs.

No acquisition, estimator fitting or new inferential endpoints. Every table
entry is a named fact with a source selector for independent verification.
"""
from pathlib import Path
import json
import shutil

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import FancyBboxPatch

from phase1_support import ROOT,record_run,sha
from analyze_source_replication import ewma

PAPER=ROOT/'paper'
BASE='millisecond_time__millisecond_flags'
LEGACY='legacy_time__legacy_flags'
RESTORE='legacy_restore_modern_category_B'
GRIDS=[15,30,60,300,900,1800]
LABELS=['15s','30s','1m','5m','15m','30m']
SOURCE_RUNS={'A08':'side_project_study_20261021T214152Z','A10':'source_replication_analysis_20261022T014736Z',
             'A11':'source_policy_robustness_20261022T032458Z'}


def prepare():
    for folder in ['generated','figures']:(PAPER/folder).mkdir(exist_ok=True)
    facts=[];inputs={};frames={}
    def load(name,columns):
        path=ROOT/name;pd.read_csv(path,usecols=columns,nrows=5)
        frames[name]=pd.read_csv(path,usecols=columns);inputs[name]=sha(path)
        return frames[name]
    inc=load('results/source_replication_incidence.csv',['symbol','frequency_seconds','case','RV_valid_pairs','RQ_valid_pairs','RV_material_days','RQ_material_days','mean_absolute_log_RV_ratio'])
    hs=load('results/source_replication_H.csv',['frequency_seconds','case','lag_max','H_tilde','H_difference_common_endpoints'])
    risk=load('results/source_replication_risk.csv',['frequency_seconds','case','mean_absolute_weight_difference','max_absolute_weight_difference','origins_above_5pp','longest_run_above_5pp_sessions'])
    ci=load('results/source_replication_intervals.csv',['frequency_seconds','measure','mean_block','lower_95_percentile','upper_95_percentile'])
    policies=load('results/source_policy_policies.csv',['frequency_seconds','decay','case','annual_target','weight_cap','mean_absolute_gap','uncapped_mean_absolute_gap','cap_attenuation','both_saturated_fraction','origins_above_5pp'])
    states=load('results/source_policy_states.csv',['frequency_seconds','decay','case','origins_relative_difference_above_factor','p95_absolute_log_uncapped_weight_ratio','max_absolute_log_uncapped_weight_ratio','top_one_potential_share','top_five_potential_share'])
    synthetic=load('results/side_project/summary.csv',['model','noise_sd','sampling_minutes','lag_max','H_spot_mean','H_IV_mean','H_RV_mean','H_RV_mcse'])
    def selected(name,selector):
        frame=frames[name]
        for k,v in selector.items():frame=frame[frame[k].eq(v)]
        return frame
    def fact(key,name,selector,field,operation='value',scale=1,digits=4,threshold=None):
        values=selected(name,selector)[field]
        if operation=='value':
            if len(values)!=1:raise ValueError('Nonunique paper source: '+key)
            value=float(values.iloc[0])
        elif operation=='min':value=float(values.min())
        elif operation=='max':value=float(values.max())
        elif operation=='count_ge':value=float((values>=threshold).sum())
        else:raise ValueError(operation)
        value*=scale
        display=f'{value:.{digits}f}'
        facts.append(dict(key=key,source=name,kind='csv',selector=selector,field=field,operation=operation,
            threshold=threshold,scale=scale,digits=digits,value=value,display=display))
        return '\\Fact{'+key+'}'
    def json_fact(key,name,field,digits=0):
        path=ROOT/name;payload=json.loads(path.read_text(encoding='utf-8'));inputs[name]=sha(path)
        value=payload
        for part in field.split('.'):value=value[part]
        value=float(value);display=f'{value:,.{digits}f}' if digits==0 else f'{value:.{digits}f}'
        facts.append(dict(key=key,source=name,kind='json',field=field,operation='value',scale=1,digits=digits,value=value,display=display))
    json_fact('sessions','results/source_policy_robustness.json','source_sessions')
    json_fact('origins','results/source_policy_robustness.json','evaluated_origins')
    json_fact('symbolDays','results/source_replication_analysis.json','input_symbol_days')
    json_fact('records','results/source_replication_analysis.json','matched_input_records')
    for key,source,field in [('checksA10','results/source_result_check.json','scalar_checks'),('checksA11','results/source_policy_check.json','scalar_checks'),('overlaps','results/source_policy_check.json','original_A10_overlap_scalars')]:json_fact(key,source,field)
    columns=['Grid','RV material','RQ material',r'$\widetilde H_M$',r'$\widetilde H_L$',r'Mean gap (pp)',r'$\geq5$pp origins']
    rows=[]
    for freq,label in zip(GRIDS,LABELS):
        s={'symbol':'SPY','frequency_seconds':freq,'case':LEGACY}
        rv=fact(f'rvN{freq}','results/source_replication_incidence.csv',s,'RV_material_days',digits=0)
        rq=fact(f'rqN{freq}','results/source_replication_incidence.csv',s,'RQ_material_days',digits=0)
        den=fact(f'den{freq}','results/source_replication_incidence.csv',s,'RV_valid_pairs',digits=0)
        pair=selected('results/source_replication_incidence.csv',s).iloc[0]
        if pair.RV_valid_pairs!=pair.RQ_valid_pairs:raise ValueError('Use separate paper denominators on missingness')
        hm=fact(f'hM{freq}','results/source_replication_H.csv',{'frequency_seconds':freq,'case':BASE,'lag_max':10},'H_tilde')
        hl=fact(f'hL{freq}','results/source_replication_H.csv',{'frequency_seconds':freq,'case':LEGACY,'lag_max':10},'H_tilde')
        fact(f'hB{freq}','results/source_replication_H.csv',{'frequency_seconds':freq,'case':RESTORE,'lag_max':10},'H_tilde')
        gap=fact(f'gap{freq}','results/source_replication_risk.csv',{'frequency_seconds':freq,'case':LEGACY},'mean_absolute_weight_difference',scale=100,digits=3)
        count=fact(f'large{freq}','results/source_replication_risk.csv',{'frequency_seconds':freq,'case':LEGACY},'origins_above_5pp',digits=0)
        rows.append([label,rv+'/'+den,rq+'/'+den,hm,hl,gap,count])
    write_table('grid_table.tex',columns,rows,'lrrrrrr')
    for field in ['RV','RQ']:
        for bound in ['lower','upper']:
            fact(f'{field}{bound}','results/source_replication_intervals.csv',{'frequency_seconds':60,'measure':field,'mean_block':22},bound+'_95_percentile',scale=100,digits=2)
    for key,case,field in [('maxGap',LEGACY,'max_absolute_weight_difference'),('restoreGap',RESTORE,'mean_absolute_weight_difference')]:
        fact(key,'results/source_replication_risk.csv',{'frequency_seconds':60,'case':case},field,scale=100,digits=4)
    for freq in [60,300]:
        s={'frequency_seconds':freq,'decay':.94,'case':LEGACY,'annual_target':.1,'weight_cap':1.}
        for field,key in [('uncapped_mean_absolute_gap','uncapped'),('cap_attenuation','attenuation'),('both_saturated_fraction','bothCap')]:
            fact(key+str(freq),'results/source_policy_policies.csv',s,field,scale=100,digits=2 if field!='uncapped_mean_absolute_gap' else 4)
        fact('policyLarge'+str(freq),'results/source_policy_policies.csv',{'frequency_seconds':freq,'case':LEGACY},'origins_above_5pp',operation='count_ge',threshold=10,digits=0)
        for op in ['min','max']:
            fact('relative'+op+str(freq),'results/source_policy_states.csv',{'frequency_seconds':freq,'case':LEGACY},'origins_relative_difference_above_factor',operation=op,digits=0)
    cases=[LEGACY,'millisecond_time__legacy_flags','legacy_time__millisecond_flags',RESTORE]
    names=['Legacy time / legacy flags','Modern time / legacy flags','Legacy time / modern flags','Legacy + B information']
    rows=[]
    for i,(case,name) in enumerate(zip(cases,names)):
        s={'symbol':'SPY','frequency_seconds':60,'case':case}
        rows.append([name,fact(f'crossRV{i}','results/source_replication_incidence.csv',s,'RV_material_days',digits=0),fact(f'crossRQ{i}','results/source_replication_incidence.csv',s,'RQ_material_days',digits=0),fact(f'crossLog{i}','results/source_replication_incidence.csv',s,'mean_absolute_log_RV_ratio',digits=5)])
    write_table('crossed_table.tex',['Construction','RV material','RQ material','Mean abs. log RV ratio'],rows,'lrrr')
    rows=[]
    for i,decay in enumerate([.9,.94,.97]):
        for j,target in enumerate([.05,.1,.15]):
            for k,cap in enumerate([.5,1.,2.]):
                row=[f'{decay:.2f}',f'{100*target:.0f}',f'{100*cap:.0f}']
                for freq in [60,300]:
                    s={'frequency_seconds':freq,'decay':decay,'case':LEGACY,'annual_target':target,'weight_cap':cap}
                    row.extend([fact(f'policyGap{i}{j}{k}f{freq}','results/source_policy_policies.csv',s,'mean_absolute_gap',scale=100,digits=3),fact(f'policyN{i}{j}{k}f{freq}','results/source_policy_policies.csv',s,'origins_above_5pp',digits=0)])
                rows.append(row)
    write_table('policy_table.tex',[r'$\lambda$',r'Target \%',r'Cap \%','1m gap (pp)','1m large','5m gap (pp)','5m large'],rows,'rrrrrrr')
    rows=[]
    for band in [5,10,22]:
        for freq,label in zip(GRIDS,LABELS):
            row=[str(band),label]
            for k,case in enumerate([BASE,LEGACY,RESTORE]):row.append(fact(f'hBand{band}f{freq}c{k}','results/source_replication_H.csv',{'frequency_seconds':freq,'lag_max':band,'case':case},'H_tilde'))
            rows.append(row)
    write_table('H_table.tex',['Largest lag','Grid','Modern','Legacy','B restored'],rows,'rlrrr')
    for key,field in [('ouSpot','H_spot_mean'),('ouIV','H_IV_mean'),('ouRV','H_RV_mean'),('ouSE','H_RV_mcse')]:
        fact(key,'results/side_project/summary.csv',{'model':'OU','noise_sd':0.,'sampling_minutes':5,'lag_max':10},field,digits=6)
    for metric in ['top_one_potential_share','top_five_potential_share']:
        fact(metric,'results/source_policy_states.csv',{'frequency_seconds':60,'decay':.94,'case':LEGACY},metric,scale=100,digits=2)
    for symbol in ['EFA','IWM','QQQ','TLT']:
        s={'symbol':symbol,'frequency_seconds':60,'case':LEGACY}
        for field,key in [('RV_material_days','rv'),('RQ_material_days','rq'),('RV_valid_pairs','rvden'),('RQ_valid_pairs','rqden')]:
            fact('panel'+symbol+key,'results/source_replication_incidence.csv',s,field,digits=0)
    for key,field,digits in [('discoveryStandardized','origins_above_5pp_discovery_effect_standardized',0),('discoveryHmodern','H_modern_discovery_endpoints_omitted',4),('discoveryHlegacy','H_legacy_discovery_endpoints_omitted',4)]:
        json_fact(key,'results/source_result_check.json','post_result_discovery_sensitivity.60.'+field,digits)
    text='\\newcommand{\\Fact}[1]{\\csname fact@#1\\endcsname}\n'
    text+=''.join('\\expandafter\\def\\csname fact@'+f['key']+'\\endcsname{'+f['display']+'}\n' for f in facts)
    (PAPER/'generated/facts.tex').write_text(text,encoding='utf-8',newline='\n')
    (PAPER/'generated/claims.json').write_text(json.dumps(facts,indent=2)+'\n',encoding='utf-8',newline='\n')
    plt.rcParams.update({'font.size':9.5,'axes.titlesize':10,'axes.labelsize':9,
        'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white','pdf.fonttype':42})
    def save(fig,name):
        fig.savefig(PAPER/f'figures/{name}.pdf',bbox_inches='tight');fig.savefig(PAPER/f'figures/{name}.png',dpi=210,bbox_inches='tight');plt.close(fig)
    fig,ax=plt.subplots(figsize=(7.2,2.0));ax.set(xlim=(0,11),ylim=(0,2.15));ax.axis('off')
    boxes=[('Observed\nrecords','Matched price /\nsize / venue'),('Source\ninformation','Time and\ncondition fields'),('Measurements','RV, RQ and\nfinite-band slope'),('Risk state','Fixed causal\nEWMA'),('Decision\nconstraint','Common\nexposure cap')]
    for i,(heading,detail) in enumerate(boxes):
        x=.05+2.2*i;patch=FancyBboxPatch((x,.45),2.02,1.4,boxstyle='round,pad=.025',facecolor='#eef3f7',edgecolor='#476e8c');ax.add_patch(patch)
        ax.text(x+1.01,1.48,heading,ha='center',va='center',fontsize=9,fontweight='bold');ax.text(x+1.01,.88,detail,ha='center',va='center',fontsize=8)
        if i<4:ax.annotate('',(x+2.18,1.02),(x+2.03,1.02),arrowprops=dict(arrowstyle='->',color='#476e8c'))
    ax.text(5.5,.12,'Source agreement, state agreement and constrained-decision agreement are distinct checks.',ha='center',fontsize=8)
    save(fig,'workflow')
    fig,axes=plt.subplots(1,2,figsize=(7.2,3.5),layout='constrained')
    sg=synthetic[synthetic.noise_sd.eq(0)&synthetic.lag_max.eq(10)]
    models=['OU','Cauchy_H01','Cauchy_H03'];x=np.arange(3)
    for offset,field,label,color in [(-.24,'H_spot_mean','Spot samples','#446f96'),(0,'H_IV_mean','Grid-integrated variance','#c17b45'),(.24,'H_RV_mean','5-minute RV','#218675')]:
        g=sg[sg.sampling_minutes.eq(5)].set_index('model').reindex(models);axes[0].bar(x+offset,g[field],width=.24,label=label,color=color)
    axes[0].set(xticks=x,xticklabels=['OU','Cauchy .1','Cauchy .3'],ylabel='Mean finite-band H-tilde',title='(a) Measurement stages',ylim=(0,.75));axes[0].legend(frameon=False,fontsize=8)
    for model,label in zip(models,['OU','Cauchy H=.1','Cauchy H=.3']):
        g=sg[sg.model.eq(model)].sort_values('sampling_minutes');axes[1].errorbar(g.sampling_minutes,g.H_RV_mean,yerr=1.96*g.H_RV_mcse,marker='o',label=label)
    axes[1].set(xlabel='Sampling interval (minutes)',ylabel='Mean log-RV H-tilde',title='(b) Fixed lag band 1-10');axes[1].legend(frameon=False,fontsize=8)
    save(fig,'synthetic')
    fig,axes=plt.subplots(1,2,figsize=(7.2,3.5),layout='constrained');x=np.arange(6)
    for field,offset,color in [('RV',-.09,'#446f96'),('RQ',.09,'#c17b45')]:
        g=inc[inc.symbol.eq('SPY')&inc['case'].eq(LEGACY)].set_index('frequency_seconds').reindex(GRIDS)
        fraction=g[field+'_material_days']/g[field+'_valid_pairs'];b=ci[ci.measure.eq(field)&ci.mean_block.eq(22)].set_index('frequency_seconds').reindex(GRIDS)
        axes[0].vlines(x+offset,100*b.lower_95_percentile,100*b.upper_95_percentile,color=color);axes[0].scatter(x+offset,100*fraction,color=color,label=field)
    axes[0].set(xticks=x,xticklabels=LABELS,ylabel='Material differences (% valid days)',title='(a) Non-discovery incidence');axes[0].legend(frameon=False,fontsize=8)
    for case,label,color in [(BASE,'Modern','#446f96'),(LEGACY,'Legacy','#bb4f59'),(RESTORE,'B restored','#218675')]:
        g=hs[hs.lag_max.eq(10)&hs['case'].eq(case)].set_index('frequency_seconds').reindex(GRIDS);axes[1].plot(x,g.H_tilde,marker='o',label=label,color=color)
    axes[1].set(xticks=x,xticklabels=LABELS,ylabel='Descriptive H-tilde',title='(b) Calendar lags 1-10');axes[1].legend(frameon=False,fontsize=8)
    save(fig,'measurement')
    private=Path(r'D:\AICorner\WRDS_Private_Downloads\A10_source_replication\A10_private_case_ratios.csv')
    a11=json.loads((ROOT/'results/source_policy_robustness.json').read_text(encoding='utf-8'))
    if sha(private)!=a11['source_input_sha256']:raise ValueError('Checked private input changed')
    cols=['date','symbol','frequency_seconds','case','RV'];pd.read_csv(private,usecols=cols,nrows=5);daily=pd.read_csv(private,usecols=cols)
    fig,axes=plt.subplots(2,1,figsize=(7.2,4.8),layout='constrained',sharex=True)
    for ax,freq in zip(axes,[60,300]):
        g=daily[daily.symbol.eq('SPY')&daily.frequency_seconds.eq(freq)];dates=sorted(g.date.unique());paths={}
        for case,label,color in [(BASE,'Modern','#446f96'),(LEGACY,'Legacy','#bb4f59'),(RESTORE,'B restored','#218675')]:
            rv=g[g['case'].eq(case)].set_index('date').reindex(dates).RV.to_numpy();w=np.minimum(1,.1/np.sqrt(252*ewma(rv,.94)))[126:];paths[case]=w
            ax.plot(pd.to_datetime(dates[126:]),100*w,label=label,color=color,lw=1.25)
        check=risk[risk.frequency_seconds.eq(freq)&risk['case'].eq(LEGACY)].iloc[0]
        np.testing.assert_allclose(np.mean(np.abs(paths[LEGACY]-paths[BASE])),check.mean_absolute_weight_difference,rtol=1e-11,atol=1e-13)
        assert sum(np.abs(paths[LEGACY]-paths[BASE])>=.05)==check.origins_above_5pp
        ax.set(ylabel='Next-session weight input (%)',title=f'{freq//60}-minute RV; origin-date information');ax.legend(frameon=False,fontsize=8,ncol=3)
    axes[-1].xaxis.set_major_locator(mdates.MonthLocator(interval=2));axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    save(fig,'weight_paths')
    orig=policies[policies.decay.eq(.94)&policies['case'].eq(LEGACY)&policies.annual_target.eq(.1)&policies.weight_cap.eq(1)].set_index('frequency_seconds').reindex(GRIDS)
    fig,axes=plt.subplots(1,2,figsize=(7.2,3.5),layout='constrained');x=np.arange(6)
    axes[0].bar(x-.18,100*orig.mean_absolute_gap,width=.36,label='Capped',color='#446f96');axes[0].bar(x+.18,100*orig.uncapped_mean_absolute_gap,width=.36,label='Uncapped',color='#c17b45')
    axes[0].set(xticks=x,xticklabels=LABELS,yscale='log',ylabel='Mean absolute weight gap (pp)',title='(a) Original policy; log scale');axes[0].legend(frameon=False,fontsize=8)
    for decay in [.9,.94,.97]:
        g=states[states['case'].eq(LEGACY)&states.decay.eq(decay)].set_index('frequency_seconds').reindex(GRIDS)
        axes[1].plot(x,100*np.expm1(g.p95_absolute_log_uncapped_weight_ratio),marker='o',label=f'Decay {decay:.2f}')
    axes[1].axhline(10,color='grey',ls='--');axes[1].set(xticks=x,xticklabels=LABELS,ylabel='Relative factor discrepancy (%)',title='(b) Uncapped p95 difference');axes[1].legend(frameon=False,fontsize=8)
    save(fig,'cap_masking')
    fig,axes=plt.subplots(2,1,figsize=(7.2,4.8),layout='constrained');pairs=[(t,c) for t in [.05,.1,.15] for c in [.5,1.,2.]]
    vmax=100*policies[policies['case'].eq(LEGACY)&policies.frequency_seconds.isin([60,300])].mean_absolute_gap.max()
    for ax,freq in zip(axes,[60,300]):
        g=policies[policies['case'].eq(LEGACY)&policies.frequency_seconds.eq(freq)]
        matrix=np.array([[100*g[g.decay.eq(l)&g.annual_target.eq(t)&g.weight_cap.eq(c)].mean_absolute_gap.item() for t,c in pairs] for l in [.9,.94,.97]])
        im=ax.imshow(matrix,vmin=0,vmax=vmax,cmap='Blues',aspect='auto')
        for (i,j),v in np.ndenumerate(matrix):ax.text(j,i,f'{v:.2f}',ha='center',va='center',color='white' if v>vmax*.55 else '#183348',fontsize=9)
        ax.set(xticks=range(9),xticklabels=[f'{100*t:.0f}/{100*c:.0f}' for t,c in pairs],yticks=range(3),yticklabels=['.90','.94','.97'],xlabel='Target (%) / cap (%)',ylabel='EWMA decay',title=f'{freq//60}-minute RV')
    fig.colorbar(im,ax=axes,label='Mean absolute weight gap (pp)',shrink=.8)
    save(fig,'policies')
    files={p.relative_to(PAPER).as_posix():sha(p) for folder in ['generated','figures'] for p in (PAPER/folder).iterdir() if p.is_file()}
    run=record_run('undergraduate_paper_inputs',dict(status='prepared_pending_paper_check',source_runs=SOURCE_RUNS,
        source_inputs_sha256=inputs,generated_files_sha256=files,named_numerical_facts=len(facts),focused_figures=6,
        code_sha256=sha(__file__),new_market_data_acquired=False,sealed_data_opened=False,published_online=False))
    (ROOT/'results/undergraduate_paper_inputs.json').write_text(json.dumps(dict(run_id=run,named_numerical_facts=len(facts),focused_figures=6,source_inputs_sha256=inputs,generated_files_sha256=files),indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(run_id=run,facts=len(facts),figures=6)))


def write_table(name,headers,rows,alignment):
    text='\\begin{tabular}{'+alignment+'}\n\\toprule\n'+' & '.join(headers)+' \\\\\n\\midrule\n'
    text+=''.join(' & '.join(row)+' \\\\\n' for row in rows)+'\\bottomrule\n\\end{tabular}\n'
    (PAPER/'generated'/name).write_text(text,encoding='utf-8',newline='\n')


if __name__=='__main__':prepare()
