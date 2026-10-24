"""Full-class compact energy bound from a clipped logarithmic weight.

All displayed claims use exact Fraction arithmetic.  A finite positive
Taylor sum proves the needed upper bound on log10.  Independent Cartesian
polynomial integration checks the weighted identity including the inner
interface term.  Existing Phase1 files are only read.
"""
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal as D, localcontext, ROUND_FLOOR, ROUND_CEILING
from math import factorial
import hashlib
import json

HERE = Path(__file__).parent
ROOT = HERE.parents[2]


def add(*polys):
    out = {}
    for p in polys:
        for k, v in p.items():
            out[k] = out.get(k, F(0)) + v
    return {k:v for k,v in out.items() if v}


def scale(p, c):
    return {k:v*c for k,v in p.items() if v*c}


def mul(p, q):
    out = {}
    for a,x in p.items():
        for b,y in q.items():
            k = tuple(a[i]+b[i] for i in range(3))
            out[k] = out.get(k, F(0))+x*y
    return {k:v for k,v in out.items() if v}


def derivative(p, i):
    out = {}
    for k,v in p.items():
        if k[i]:
            j = list(k)
            j[i] -= 1
            out[tuple(j)] = v*k[i]
    return out


def df(n):
    x = 1
    while n > 0:
        x *= n
        n -= 2
    return x


def sphere_moment_over_pi(k):
    if any(i % 2 for i in k):
        return F(0)
    return F(4*df(k[0]-1)*df(k[1]-1)*df(k[2]-1), df(sum(k)+1))


def sphere_value(p, r):
    return sum((v*sphere_moment_over_pi(k)*r**sum(k) for k,v in p.items()), F(0))


def invariants(p):
    grad = [derivative(p,i) for i in range(3)]
    hess = [[derivative(grad[i],j) for j in range(3)] for i in range(3)]
    trace = add(*(hess[i][i] for i in range(3)))
    Q = add(mul(trace,trace),scale(add(*(mul(v,v) for row in hess for v in row)),-1))
    norm_grad2 = add(*(mul(v,v) for v in grad))
    euler = {k:sum(k)*v for k,v in p.items() if sum(k)}
    return Q,norm_grad2,mul(euler,euler)


def exact_identity_checks():
    one = {(0,0,0):F(1)}
    radius2 = {(2,0,0):F(1),(0,2,0):F(1),(0,0,2):F(1)}
    compact = one
    for _ in range(6):
        compact = mul(compact,add(one,scale(radius2,-1)))
    factors = [one,{(1,0,0):F(1)},
               {(0,2,0):F(1),(1,0,1):F(3,7)},
               {(1,0,0):F(1),(0,1,0):F(2,7),(1,0,1):F(-3,11),(0,0,3):F(5,13)}]
    cases = []
    for i,factor in enumerate(factors):
        Q,g2,e2 = invariants(mul(compact,factor))
        # Integral_Q/pi also equals the coefficient of log(1/a) in
        # the exact annular integral of log(r/a)*Q.  It must vanish.
        signed = sum((v*sphere_moment_over_pi(k)/F(sum(k)+3) for k,v in Q.items()), F(0))
        assert signed == 0
        for a in (F(1,3),F(1,2),F(3,4)):
            lhs = -sum((v*sphere_moment_over_pi(k)*(1-a**(sum(k)+3))/F((sum(k)+3)**2)
                        for k,v in Q.items()), F(0))
            radial = sum((v*sphere_moment_over_pi(k)*(1-a**(sum(k)-1))/F(sum(k)-1)
                          for k,v in e2.items()), F(0))
            angular_trace = a*a*sphere_value(g2,a)-sphere_value(e2,a)
            rhs = -2*radial-angular_trace/a
            assert radial >= 0 and angular_trace >= 0
            assert lhs == rhs
            cases.append({'polynomial_case':i,'inner_radius_exact':str(a),
                          'weighted_integral_over_pi_exact':str(lhs),
                          'inner_angular_term_over_pi_exact':str(angular_trace/a),
                          'identity_pass':True})
    return cases


def decimal(q, upper=False):
    with localcontext() as ctx:
        ctx.prec = 60
        ctx.rounding = ROUND_CEILING if upper else ROUND_FLOOR
        return str(D(q.numerator)/D(q.denominator))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    checks = exact_identity_checks()
    benchmark_path = ROOT/'benchmarks/rodal-2c-v1.json'
    contract_path = ROOT/'research/expanded_family/localized-exterior-contract.json'
    reference_path = ROOT/'research/deep_strict/validated_math/frozen-interval-level-11.json'
    compact_path = ROOT/'research/expanded_family/angular_search/localized/compact-r100-l13-verified.json'
    assert sha(benchmark_path) == 'dec6cdcc48e234a581dc1068f3c3bee62c73c41f14ac10c37908f5d85d6cd3e4'
    assert sha(contract_path) == '179c10116855ff2ac2b40eb6bdc03b2d7504466a9241bd941b8793375c12521e'
    assert sha(reference_path) == '6cdb2350ea9273ccbfa693ce2d3dfac59beb5b4aae7fcee38d58f70e6e4529b9'
    assert sha(compact_path) == '7c408f6fe0667284573cd1eb18bfbbb61fb0c9bda5f55b6b69e48ca55231db36'
    benchmark = json.loads(benchmark_path.read_text())
    reference = json.loads(reference_path.read_text())
    compact = json.loads(compact_path.read_text())
    c = F(benchmark['constants']['c_m_s'])
    G = F(benchmark['constants']['G_m3_kg_s2'])
    beta = F(benchmark['parameters']['speed_c'])
    a = F(benchmark['cabin']['proper_radius_m'])
    eps = F(benchmark['cabin']['maximum_shift_norm'])
    R = F(100)
    assert (a,beta,R) == (10,2,100)
    B = beta-eps
    log_upper = F(2302585092994046,10**15)
    taylor = sum((log_upper**j/F(factorial(j)) for j in range(51)),F(0))
    assert taylor > R/a
    # exp(log_upper)>10 implies log(10)<log_upper.  It is in the
    # denominator, so this exact rational substitution lowers the bound.
    lower = c**4*B*B*a*R/(3*G*(R-a)*log_upper)
    baseline_upper = F(reference['baseline_energy_J_interval'][1])
    compact_upper = F(compact['total_energy_upper_J_exact'])
    old_lower = 2*c**4*B*B*a**3*R/(G*(R**3-a**3))
    assert lower > baseline_upper/10
    assert baseline_upper/lower < F(5459424,10**6)
    assert lower > 8*old_lower
    out = {
        'status':'independently_reproduced',
        'formal_certification':False,
        'evidence_kind':'analytic_full_class_compact_lower_bound_with_exact_arithmetic',
        'script_sha256':sha(Path(__file__)),
        'task_claim_sha256':sha(HERE/'task-claim.json'),
        'original_benchmark_sha256':sha(benchmark_path),
        'localized_contract_sha256':sha(contract_path),
        'reference_receipt_sha256':sha(reference_path),
        'phase1_best_compact_receipt_sha256':sha(compact_path),
        'scope':{
            'metric':'ds^2=-du^2+|dq+grad(Phi)du|^2, u=ct',
            'observer':'n=(1,-grad(Phi))',
            'speed_c_exact':str(beta),'cabin_radius_m_exact':str(a),
            'flat_exterior_radius_m_exact':str(R),
            'cabin_shift_cap_exact':str(eps),
            'dipole_amplitude_lower_exact':str(B),
            'regularity':'C5 potential, more than sufficient for the identities',
            'symmetry_assumption':None,
            'global_caps_used':False,
            'energy':'Whole-space integral of absolute Eulerian density, in joules'},
        'analytic_lower_bound_formula':'c^4*B^2*a*R/[3*G*(R-a)*log(R/a)]',
        'log_R_over_a_rational_upper':str(log_upper),
        'log_bound_proof':'The exact positive exponential Taylor sum through degree50 at the claimed upper endpoint exceeds10.',
        'log_bound_Taylor_check_pass':True,
        'exact_cartesian_weighted_identity_checks':checks,
        'lower_bound_J_exact':str(lower),
        'lower_bound_J_outward':decimal(lower),
        'baseline_upper_J_exact':str(baseline_upper),
        'baseline_improvement_factor_upper_outward':decimal(baseline_upper/lower,True),
        'phase1_best_compact_upper_J_exact':str(compact_upper),
        'phase1_best_compact_to_lower_bound_ratio_upper':decimal(compact_upper/lower,True),
        'old_quadratic_weight_lower_bound_J_exact':str(old_lower),
        'new_to_old_lower_bound_ratio_lower':decimal(lower/old_lower),
        'tenfold_baseline_improvement_ruled_out':True,
        'independent_algebra_review':'Root and analytic_bounds independently confirmed interface signs, dipole normalization and centering factor.',
        'limitations':'This excludes tenfold improvement only for the stated compact100m class. It does not prove the current candidate optimal, require energy conditions, construct matter, establish engineering safety, or open the formal certification gate.'
    }
    path = HERE/'clipped-log-bound.json'
    path.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k in (
        'status','formal_certification','lower_bound_J_outward',
        'baseline_improvement_factor_upper_outward','phase1_best_compact_to_lower_bound_ratio_upper',
        'new_to_old_lower_bound_ratio_lower','tenfold_baseline_improvement_ruled_out')},indent=2))
    print('receipt_sha256',sha(path))


if __name__ == '__main__':
    main()
