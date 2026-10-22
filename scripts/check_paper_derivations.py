"""Numerical cross-checks of paper identities; no empirical inputs or model fitting."""
import itertools
import json
import math

from phase1_support import ROOT, record_run, sha


def check():
    checks = 0

    def close(actual, expected, rel=2e-10, absolute=2e-13):
        nonlocal checks
        assert math.isclose(actual, expected, rel_tol=rel, abs_tol=absolute), (actual, expected)
        checks += 1

    # Three-point Gaussian quadrature integrates each variable's moments through
    # degree five exactly. This checks return-polynomial expansion independently
    # of the displayed Gaussian fourth-moment formulas, without Monte Carlo luck.
    nodes = [(-math.sqrt(3), 1/6), (0.0, 2/3), (math.sqrt(3), 1/6)]
    for a in [0.00003, 0.0007, 0.12]:
        for omega2 in [0.0, 0.000001, 0.02]:
            second = fourth = 0.0
            for (z, pz), (left, pl), (right, pr) in itertools.product(nodes, repeat=3):
                ret = math.sqrt(a)*z + math.sqrt(omega2)*(right-left)
                probability = pz*pl*pr
                second += probability*ret**2
                fourth += probability*ret**4
            close(second, a+2*omega2)
            close(fourth, 3*(a+2*omega2)**2)
            if omega2 == 0:
                close(fourth-second**2, 2*a*a)
    a_values = [0.00003, 0.00007, 0.0002, 0.0001]
    m = len(a_values)
    for omega2 in [0, 0.000001, 0.02]:
        close(m*sum((a+2*omega2)**2 for a in a_values),
              m*sum(a*a for a in a_values)+4*m*omega2*sum(a_values)+4*m*m*omega2**2)

    # Exact Dirichlet second-moment expression via Gamma functions versus its
    # simplified q-hat expectation. Independent M=2 circle integration as well.
    for m in [1, 2, 3, 10, 42, 78]:
        one = math.exp(math.lgamma(m/2)-math.lgamma(m/2+2)
                       +math.lgamma(2.5)-math.lgamma(.5))
        close((2/3)*m*one, 2/(m+2))
    n = 2048
    circle = sum((2/3)*(math.cos(2*math.pi*i/n)**4+math.sin(2*math.pi*i/n)**4)
                 for i in range(n))/n
    close(circle, .5)

    # Analytic local slopes versus centered numerical derivatives of log V.
    for kappa in [.02, .3, 1.7]:
        for tau in [.05, .8, 3, 20]:
            for q in [0, .01, .4]:
                v = .25
                def variogram(t):
                    return -2*v*math.expm1(-kappa*t)+2*q
                h = tau*1e-5
                numerical = tau*(math.log(variogram(tau+h))-math.log(variogram(tau-h)))/(4*h)
                analytic = tau*v*kappa*math.exp(-kappa*tau)/variogram(tau)
                close(numerical, analytic, rel=2e-7, absolute=2e-10)
                if q == 0:
                    close(analytic, kappa*tau/(2*math.expm1(kappa*tau)))
        close((kappa*1e-7)/(2*math.expm1(kappa*1e-7)), .5, rel=2e-7)
    for H in [.1, .3, .5]:
        xs = [math.log(i) for i in range(1, 11)]
        ys = [math.log(2.7)+2*H*x for x in xs]
        meanx, meany = sum(xs)/len(xs), sum(ys)/len(ys)
        slope = sum((x-meanx)*(y-meany) for x, y in zip(xs, ys))/sum((x-meanx)**2 for x in xs)
        close(slope/2, H)

    # Expansion against recursion, initialized homogeneity and a planted
    # erroneous initialization coefficient. Values are synthetic daily inputs.
    rv = [.0002 + .00001*((i*7)%11) for i in range(36)]
    for decay in [.9, .94, .97]:
        state = rv[0]
        for t in range(len(rv)):
            if t:
                state = decay*state+(1-decay)*rv[t]
            direct = decay**t*rv[0]+sum((1-decay)*decay**(t-i)*rv[i] for i in range(1, t+1))
            close(state, direct)
            close(decay**t+sum((1-decay)*decay**(t-i) for i in range(1, t+1)), 1)
        bad = (1-decay)*decay**(len(rv)-1)*rv[0]+sum((1-decay)*decay**(len(rv)-1-i)*rv[i] for i in range(1, len(rv)))
        assert not math.isclose(bad, state, rel_tol=1e-6)
        checks += 1
        for multiplier in [.1, 3, 10000]:
            scaled = multiplier*rv[0]
            for value in rv[1:]:
                scaled = decay*scaled+(1-decay)*multiplier*value
            close(scaled, multiplier*state)
            close(math.sqrt(state/scaled), multiplier**(-.5))

    for target, annual, cap in itertools.product([.05, .1, .15], [252], [.5, 1, 2]):
        cutoff = target**2/(annual*cap**2)
        close(target/math.sqrt(annual*cutoff), cap)
        for a, b in itertools.product([.001, .1, .8, 1, 1.5, 10], repeat=2):
            assert abs(min(cap, a)-min(cap, b)) <= abs(a-b)+1e-15
            checks += 1
    summary = dict(status='passed_checks', identities_checked=checks,
                   methods=['exact Gaussian polynomial quadrature', 'Gamma-function moments and circle integration',
                            'finite differences of log variograms', 'recursion versus direct convolution',
                            'scale and cap boundary cases'],
                   planted_wrong_initialization_rejected=True, empirical_data_read=False,
                   code_sha256=sha(__file__), theory_source_sha256=sha(ROOT/'paper/theory.tex'),
                   interpretation='Selected mathematical identities passed these checks; not a proof of empirical model assumptions.')
    run = record_run('paper_derivation_check', summary)
    (ROOT/'results/paper_derivation_check.json').write_text(json.dumps(dict(summary, run_id=run), indent=2)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(run_id=run, checks=checks, status='passed_checks')))


if __name__ == '__main__':
    check()
