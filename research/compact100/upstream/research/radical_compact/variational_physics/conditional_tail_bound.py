"""Check the outer boundary term and a reference-envelope corollary.

The compact-exterior theorem is not applied to a noncompact tail.  A
separate identity keeps the outer tangential-gradient term explicitly.
Exact polynomial fixtures have nonzero outer traces.  The corollary uses
the actual angular norm envelope of the original standardized reference.
"""
from pathlib import Path
from fractions import Fraction as F
from math import factorial
import importlib.util
import hashlib
import json

HERE = Path(__file__).parent
ROOT = HERE.parents[2]


def load(name,path):
    spec = importlib.util.spec_from_file_location(name,path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


POLY_PATH = HERE/'clipped_log_bound.py'
LOG_PATH = HERE/'radius_scaling.py'
assert sha(POLY_PATH) == 'c7da9fde762a702f718e03900956ef6c2d494f9df486a834e8b8115d0f8ea018'
assert sha(LOG_PATH) == '09157ac1134a818ff1f439e14bf3a1db35fad797bc1b7d48563183a6e6a4ab31'
p = load('tail_polynomials',POLY_PATH)
trans = load('tail_transcendentals',LOG_PATH)


def boundary_identity_checks():
    one = {(0,0,0):F(1)}
    r2 = {(2,0,0):F(1),(0,2,0):F(1),(0,0,2):F(1)}
    base = one
    for _ in range(6):
        base = p.mul(base,p.add(one,p.scale(r2,F(-1,4))))
    factors = [one,{(1,0,0):F(-1)},
               {(0,2,0):F(1),(1,0,1):F(3,7)},
               {(1,0,0):F(-1),(0,1,0):F(2,7),(1,0,1):F(-3,11),(0,0,3):F(5,13)}]
    rows = []
    for i,factor in enumerate(factors):
        Q,g2,e2 = p.invariants(p.mul(base,factor))
        signed = sum((v*p.sphere_moment_over_pi(k)*F(2)**(sum(k)+3)/F(sum(k)+3)
                      for k,v in Q.items()),F(0))
        assert signed == 0
        for a,R in ((F(1,4),F(1)),(F(1,2),F(3,2)),(F(3,4),F(7,4))):
            # The log(R/a) coefficient cancels using integral over the
            # entire support ball2, including the region outsideR.
            lhs = -sum((v*p.sphere_moment_over_pi(k)*(R**(sum(k)+3)-a**(sum(k)+3))/F((sum(k)+3)**2)
                        for k,v in Q.items()),F(0))
            radial = sum((v*p.sphere_moment_over_pi(k)*(R**(sum(k)-1)-a**(sum(k)-1))/F(sum(k)-1)
                          for k,v in e2.items()),F(0))
            angular_a = a*a*p.sphere_value(g2,a)-p.sphere_value(e2,a)
            angular_R = R*R*p.sphere_value(g2,R)-p.sphere_value(e2,R)
            rhs = -2*radial-angular_a/a+angular_R/R
            assert lhs == rhs
            assert radial >= 0 and angular_a >= 0 and angular_R >= 0
            if i:
                assert angular_R > 0
                assert lhs != -2*radial-angular_a/a
            rows.append({'case':i,'a_exact':str(a),'R_exact':str(R),
                         'nonzero_outer_tangential_term':angular_R>0,
                         'outer_term_over_pi_exact':str(angular_R/R),
                         'weighted_integral_over_pi_exact':str(lhs),'identity_pass':True})
    return rows


def main():
    checks = boundary_identity_checks()
    benchmark_path = ROOT/'benchmarks/rodal-2c-v1.json'
    contract_path = ROOT/'research/expanded_family/localized-exterior-contract.json'
    reference_path = ROOT/'research/deep_strict/validated_math/frozen-interval-level-11.json'
    assert sha(benchmark_path) == 'dec6cdcc48e234a581dc1068f3c3bee62c73c41f14ac10c37908f5d85d6cd3e4'
    assert sha(contract_path) == '179c10116855ff2ac2b40eb6bdc03b2d7504466a9241bd941b8793375c12521e'
    assert sha(reference_path) == '6cdb2350ea9273ccbfa693ce2d3dfac59beb5b4aae7fcee38d58f70e6e4529b9'
    benchmark = json.loads(benchmark_path.read_text())
    reference = json.loads(reference_path.read_text())
    c = F(benchmark['constants']['c_m_s'])
    G = F(benchmark['constants']['G_m3_kg_s2'])
    beta = F(benchmark['parameters']['speed_c'])
    assert F(benchmark['parameters']['profile_radius_m']) == 20
    assert F(benchmark['parameters']['sigma_per_m']) == 1
    a = F(benchmark['cabin']['proper_radius_m'])
    eps = F(benchmark['cabin']['maximum_shift_norm'])
    B = beta-eps
    R = F(150)
    # q=exp(-40)<10^-17 from a finite positive Taylor sum.
    assert sum((F(40)**j/F(factorial(j)) for j in range(101)),F(0)) > 10**17
    q = F(1,10**17)
    k_lower = (1-q)/(1+q)
    C_upper = F(20)/k_lower
    # exp(-2*(150-20))=exp(-260)<exp(-240)<q^6.
    assert 2*(R-20) >= 6*40
    epsilon_upper = 2*q**6
    # Candidate tangential norm <= candidate full norm <= reference full
    # norm.  The angular averages of1-mu^2 andmu^2 are2/3 and1/3.
    S_upper = beta*beta*(F(2,3)*C_upper*C_upper+F(1,3)*R*R*epsilon_upper**2)
    S_rounded_upper = F(1067)
    assert S_upper < S_rounded_upper
    loglo,loghi = trans.log_interval(R/a)
    numerator = c**4/G*(B*B*a/3-S_rounded_upper/(2*R))
    assert numerator > 0
    lower = numerator/loghi
    baseline_upper = F(reference['baseline_energy_J_interval'][1])
    assert lower > baseline_upper/10
    out = {
        'status':'independently_reproduced','formal_certification':False,
        'evidence_kind':'conditional_tail_identity_and_exact_reference_envelope_corollary',
        'script_sha256':sha(Path(__file__)),
        'polynomial_helper_sha256':sha(POLY_PATH),
        'transcendental_helper_sha256':sha(LOG_PATH),
        'original_benchmark_sha256':sha(benchmark_path),
        'localized_contract_sha256':sha(contract_path),
        'reference_receipt_sha256':sha(reference_path),
        'conditional_assumptions':[
            'The same global gradient-potential metric, observer, core and beta.',
            'Finite integral|Q| and vanishing infinity flux of grad(psi)*Delta(psi)-Hess(psi)*grad(psi), hence integralQ=0.',
            'A measured or proved outer spherical tangential-gradient L2 norm or an upper bound on it.'
        ],
        'outer_measure_definition':'S_R=(1/(4pi))*integral_S2 |grad_S psi(R,Omega)|^2 dOmega = R^2*mean_S2 |v_T(R,Omega)|^2',
        'simple_conditional_bound':'Eabs >= c^4/(G*log(R/a))*max(0,B^2*a/3-S_R/(2R))',
        'S_only_radial_improvement':'Add max(0,B*a-sqrt(3*S_R/2))^2/[3*(R-a)] inside the positive part.',
        'signed_dipole_radial_improvement':'With actual coreB and b_R=(3/(4pi))*integral psi(R,Omega)*mu dOmega, add (B*a+b_R)^2/[3*(R-a)]. Substituting only a lower bound onB is not always valid in this signed expression; minimize over a knownB interval instead.',
        'nonzero_outer_term_exact_checks':checks,
        'reference_envelope_corollary':{
            'scope':'For all r>=40m, the candidate shift-deviation and Hessian norms are no greater than the original reference norms at the same point. This is the existing reference-comparable-tail scenario, distinct from compact100m candidates.',
            'sphere_radius_m_exact':str(R),
            'core_dipole_lower_exact':str(B),
            'reference_C_upper_exact':str(C_upper),
            'reference_epsilon_upper_exact':str(epsilon_upper),
            'S_R_upper_exact':str(S_upper),
            'S_R_simplified_upper_m2_exact':str(S_rounded_upper),
            'log_R_over_a_interval_exact':[str(loglo),str(loghi)],
            'energy_lower_J_exact':str(lower),
            'energy_lower_J_outward':trans.decimal(lower),
            'maximum_reference_improvement_factor_upper':trans.decimal(baseline_upper/lower,True),
            'tenfold_reference_improvement_excluded':True,
            'decay_justification':'The full reference envelope gives v=O(r^-1) and Hess(psi)=O(r^-2), so Q=O(r^-4) is integrable and the infinity divergence flux is O(r^-1), tending tozero.'
        },
        'limitations':'The outer boundary term is retained. This is not the compact radius theorem applied to a noncompact field. Neither formula is asserted for arbitrary unspecified realistic tails. The stronger signed-dipole formula must respect its actualB dependence. No material-realization or formal-certification claim.'
    }
    path = HERE/'conditional-tail-bound.json'
    path.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'receipt_sha256':sha(path),'exact_boundary_checks':len(checks),
                      'reference_envelope_corollary':out['reference_envelope_corollary']},indent=2))


if __name__ == '__main__':
    main()
