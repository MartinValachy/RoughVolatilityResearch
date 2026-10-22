"""Check the paper's invented teaching examples with exact rational arithmetic."""
from fractions import Fraction as F
import json,math
from phase1_support import ROOT,record_run,sha

def check():
    checks=0
    def equal(actual,expected):
        nonlocal checks
        assert actual==expected,(actual,expected)
        checks+=1
    returns=[F(1,100),-F(1,100),F(2,100)]
    rv=sum(r*r for r in returns);rq=sum(r**4 for r in returns)
    equal(rv,F(6,10000))
    equal(rq,F(18,100000000))
    equal(f'{math.sqrt(float(rv)):.4f}','0.0245')
    equal(f'{100*math.sqrt(float(rv)):.2f}','2.45')
    state=F(94,100)*F(1,10000)+F(6,100)*F(4,10000)
    equal(state,F(118,1000000))
    equal(F(252)*state,F(29736,1000000))
    vol=math.sqrt(float(F(252)*state));weight=.1/vol
    equal(f'{vol:.4f}','0.1724')
    equal(f'{100*vol:.2f}','17.24')
    equal(f'{weight:.3f}','0.580')
    equal(f'{100*weight:.1f}','58.0')
    equal(F(55)-F(50),F(5))
    equal((F(55,100)/F(50,100)-1)*100,F(10))
    equal((F(150,100)-F(120,100))*100,F(30))
    equal(min(F(1),F(150,100))-min(F(1),F(120,100)),F(0))
    equal(math.log(2)/(2*math.log(2)),.5)
    equal(398-126,272)
    equal(3*3*3,27)
    def material(a,b):
        ratio=F(a,b)
        return ratio>F(11,10) or ratio<F(10,11)
    for a,b,expected in [(100,105,False),(100,111,True),(100,110,False)]:
        equal(material(a,b),expected);equal(material(b,a),expected)
    study=ROOT/'paper/study.tex';guide=ROOT/'paper/reader_guide.tex'
    source=study.read_text(encoding='utf8')
    for literal in ['0.0006','0.00000018','0.000118','17.24','58.0','3\\times3\\times3=27']:
        assert literal in source,literal
    result=dict(status='passed_checks',selected_arithmetic_checks=checks,
        examples='Invented RV/RQ,EWMA,target weight,percentage points,cap,two-lag slope,warmup and strict reciprocal thresholds',
        empirical_observations_used=False,study_sha256=sha(study),reader_guide_sha256=sha(guide),
        code_sha256=sha(__file__),boundary='Selected teaching arithmetic and printed literals, not an empirical result or general error-free guarantee')
    run=record_run('student_paper_example_check',result)
    (ROOT/'results/student_paper_example_check.json').write_text(json.dumps(dict(result,run_id=run),indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps(dict(run_id=run,checks=checks,status='passed_checks')))

if __name__=='__main__':check()

