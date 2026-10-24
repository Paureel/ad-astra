"""Rigorous compact-exterior radius scaling of the clipped-log theorem.

Logarithms use exact atanh series with a geometric remainder. Exponentials
use argument reduction, positive Taylor bounds and outward fixed-point
rational squaring. Decimal is used only to display rational endpoints.
No Phase1 or earlier Phase2 evidence is modified.
"""
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal as D, localcontext, ROUND_FLOOR, ROUND_CEILING
import hashlib
import json

HERE = Path(__file__).parent
ROOT = HERE.parents[2]
GRID = 10**100
SERIES_TERMS = 80


def down(q):
    return F(q.numerator*GRID//q.denominator,GRID)


def up(q):
    return F(-((-q.numerator*GRID)//q.denominator),GRID)


def atanh_log_interval(z):
    """Enclose log((1+z)/(1-z)) for exact0<=z<=1/3."""
    assert 0 <= z <= F(1,3)
    zz = z*z
    power = z
    total = F(0)
    for j in range(SERIES_TERMS):
        total += 2*power/F(2*j+1)
        power *= zz
    remainder = 2*power/(F(2*SERIES_TERMS+1)*(1-zz))
    return down(total),up(total+remainder)


def log_interval(x):
    assert x >= 1
    shifts = 0
    while x >= 2:
        x /= 2
        shifts += 1
    lo,hi = atanh_log_interval((x-1)/(x+1))
    l2,h2 = atanh_log_interval(F(1,3))
    return lo+shifts*l2,hi+shifts*h2


def exp_interval(x):
    assert x >= 0
    y = x
    shifts = 0
    while y > F(1,8):
        y /= 2
        shifts += 1
    yl,yh = down(y),up(y)
    tl,th = F(1),F(1)
    sl,sh = F(1),F(1)
    for j in range(1,SERIES_TERMS+1):
        tl = down(tl*yl/j)
        th = up(th*yh/j)
        sl += tl
        sh += th
    nxt = up(th*yh/(SERIES_TERMS+1))
    ratio = yh/(SERIES_TERMS+2)
    assert ratio < 1
    sh += up(nxt/(1-ratio))
    for _ in range(shifts):
        sl = down(sl*sl)
        sh = up(sh*sh)
    assert 0 < sl <= sh
    return sl,sh


def decimal(q, upper=False):
    with localcontext() as ctx:
        ctx.prec = 60
        ctx.rounding = ROUND_CEILING if upper else ROUND_FLOOR
        return str(D(q.numerator)/D(q.denominator))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    benchmark_path = ROOT/'benchmarks/rodal-2c-v1.json'
    contract_path = ROOT/'research/expanded_family/localized-exterior-contract.json'
    reference_path = ROOT/'research/deep_strict/validated_math/frozen-interval-level-11.json'
    theorem_path = HERE/'clipped-log-proof.md'
    prior_receipt_path = HERE/'clipped-log-bound.json'
    assert sha(benchmark_path) == 'dec6cdcc48e234a581dc1068f3c3bee62c73c41f14ac10c37908f5d85d6cd3e4'
    assert sha(contract_path) == '179c10116855ff2ac2b40eb6bdc03b2d7504466a9241bd941b8793375c12521e'
    assert sha(reference_path) == '6cdb2350ea9273ccbfa693ce2d3dfac59beb5b4aae7fcee38d58f70e6e4529b9'
    assert sha(prior_receipt_path) == '6653e36ae52619adf8ae27dfef857a46fcfeb80cc98b79551e157e6924878d1c'
    benchmark = json.loads(benchmark_path.read_text())
    reference = json.loads(reference_path.read_text())
    c = F(benchmark['constants']['c_m_s'])
    G = F(benchmark['constants']['G_m3_kg_s2'])
    beta = F(benchmark['parameters']['speed_c'])
    a = F(benchmark['cabin']['proper_radius_m'])
    eps = F(benchmark['cabin']['maximum_shift_norm'])
    B = beta-eps
    assert (a,beta,B) == (10,2,F(1999999,1000000))
    K = c**4*B*B*a/(3*G)
    baseline_upper = F(reference['baseline_energy_J_interval'][1])
    assert exp_interval(F(0)) == (1,1)
    log10 = log_interval(F(10))
    assert exp_interval(log10[0])[0] < 10 < exp_interval(log10[1])[1]
    rows = []
    for radius in (40,80,100,300,500,1000,1000000):
        R = F(radius)
        loglo,loghi = log_interval(R/a)
        lower = K*R/((R-a)*loghi)
        factor_upper = baseline_upper/lower
        assert lower > 0
        rows.append({
            'compact_exterior_radius_m_exact':str(R),
            'log_R_over_a_interval_exact':[str(loglo),str(loghi)],
            'log_R_over_a_interval_outward':[decimal(loglo),decimal(loghi,True)],
            'universal_energy_lower_bound_J_exact':str(lower),
            'universal_energy_lower_bound_J_outward':decimal(lower),
            'maximum_baseline_improvement_factor_upper':decimal(factor_upper,True)
        })
    thresholds = []
    # These proposed brackets are checked by the rational log enclosure;
    # no floating-point estimate is trusted as a proof of the root.
    brackets = {
        10:(F(4824155916638365989,10**16),F(4824155916638365990,10**16)),
        100:(F(305672731287163763),F(305672731287163764))
    }
    for factor in (10,100,1000):
        exponent = K*factor/baseline_upper
        el,eh = exp_interval(exponent)
        simple_lo,simple_hi = a*el,a*eh
        result = {
            'target_improvement_factor':factor,
            'target_energy_upper_J_exact':str(baseline_upper/factor),
            'exponent_K_times_factor_over_reference_upper_exact':str(exponent),
            'exponent_interval_outward':[decimal(exponent),decimal(exponent,True)],
            'explicit_necessary_radius_threshold_formula':'a*exp(K*factor/reference_upper)',
            'explicit_threshold_interval_m_exact':[str(simple_lo),str(simple_hi)],
            'explicit_threshold_interval_m_outward':[decimal(simple_lo),decimal(simple_hi,True)],
            'necessary_exterior_radius_m_greater_than_exact':str(simple_lo),
            'necessary_exterior_radius_m_lower_outward':decimal(simple_lo)
        }
        if factor in brackets:
            rl,rh = brackets[factor]
            ll,lh = log_interval(rl/a)
            hl,hh = log_interval(rh/a)
            phi_lower_upper = (1-a/rl)*lh
            phi_upper_lower = (1-a/rh)*hl
            assert phi_lower_upper < exponent < phi_upper_lower
            assert simple_hi < rl
            result.update({
                'strong_implicit_threshold_equation':'(1-a/R)*log(R/a)=K*factor/reference_upper',
                'strong_implicit_root_interval_m_exact':[str(rl),str(rh)],
                'strong_implicit_root_interval_m_outward':[decimal(rl),decimal(rh,True)],
                'verified_root_bracket':True,
                'necessary_exterior_radius_m_greater_than_exact':str(rl),
                'necessary_exterior_radius_m_lower_outward':decimal(rl)
            })
        thresholds.append(result)
    assert F(thresholds[0]['necessary_exterior_radius_m_greater_than_exact']) > 482
    assert F(thresholds[1]['necessary_exterior_radius_m_greater_than_exact']) > F(30567)*10**13
    assert F(thresholds[2]['necessary_exterior_radius_m_greater_than_exact']) > F(71214)*10**161
    out = {
        'status':'independently_reproduced',
        'formal_certification':False,
        'evidence_kind':'exact_rational_transcendental_enclosures_for_compact_radius_lower_bounds',
        'script_sha256':sha(Path(__file__)),
        'clipped_log_proof_sha256':sha(theorem_path),
        'clipped_log_receipt_sha256':sha(prior_receipt_path),
        'original_benchmark_sha256':sha(benchmark_path),
        'localized_contract_sha256':sha(contract_path),
        'reference_receipt_sha256':sha(reference_path),
        'scope':'Compactly supported shift perturbation within a ball of the displayed radius, beta2 and the same10m reference core. No symmetry or additional source cap is assumed. Radii other than100m are mathematical comparison scenarios, not changes to the active candidate contract.',
        'K_J_exact':str(K),
        'K_J_outward_interval':[decimal(K),decimal(K,True)],
        'K_over_reference_upper_exact':str(K/baseline_upper),
        'baseline_upper_J_exact':str(baseline_upper),
        'dipole_amplitude_lower_exact':str(B),
        'logarithm_method':'Exact atanh series after power-of-two reduction to[1,2); geometric remainder bound.80terms.',
        'exponential_method':'Positive Taylor bounds after reduction to[0,1/8], geometric remainder and outward rational squaring.80terms; fixed denominator10^100.',
        'radius_table':rows,
        'improvement_thresholds':thresholds,
        'core_assumption_audit':'Exact inner trace is -B*a*mu plus the exterior additive constant. B=beta*(1-g0(a)); the divergence theorem gives beta*g0(a)=average_cabin W_x, so |W|<=epsilon implies B>=beta-epsilon. The constant and higher harmonics cannot reduce either trace norm. Exact uniform exterior makes grad psi=0 at its boundary.',
        'limitations':'Necessary conditions only. No candidate achieves these thresholds by this proof. The weaker explicit radius threshold is not the same as the stronger implicit root. The general radius theorem does not apply to noncompact tails or changed core, speed, observer, metric or integration domain.'
    }
    path = HERE/'radius-scaling.json'
    path.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'receipt_sha256':sha(path),
        'K_J':decimal(K),
        'radius_table':[{k:v for k,v in r.items() if k in (
            'compact_exterior_radius_m_exact','universal_energy_lower_bound_J_outward',
            'maximum_baseline_improvement_factor_upper')} for r in rows],
        'thresholds':[{k:v for k,v in r.items() if k in (
            'target_improvement_factor','necessary_exterior_radius_m_lower_outward',
            'strong_implicit_root_interval_m_outward')} for r in thresholds]},indent=2))


if __name__ == '__main__':
    main()
