"""Build one offline HTML report with exact data, CAS checks and embedded SVG."""
import base64
import gzip
from fractions import Fraction as F
import hashlib
from html import escape
import io
import json
import os
from pathlib import Path

os.environ.setdefault('MPLCONFIGDIR', '/tmp/vacuum-report-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import sympy as sp
from vacuum_run_envelope import scalar_accuracy
import vacuum_execution_contract as execution_contract
import vacuum_target_envelope as target_envelope
import vacuum_selected_report as selected_report

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'research/vacuum-spectrum'
OUTPUT = D / 'VACUUM-REPORT.html'

CAS = '''import sympy as s
x, beta, kappa, epsilon = s.symbols('x beta kappa epsilon', positive=True)
a, b, p = [s.Function(n)(x) for n in ('a', 'b', 'p')]
# Real and imaginary components of f; p is the real positive vacuum.
expanded = sum(s.diff(p*z,x)**2 for z in (a,b)) + (a*a+b*b)*p*s.diff(p,x,2)
remainder = p*p*sum(s.diff(z,x)**2 for z in (a,b))
divergence = s.diff((a*a+b*b)*p*s.diff(p,x),x)
assert s.simplify(expanded-remainder-divergence) == 0
vacuum = s.exp(beta*s.cos(2*x)/2)
potential = kappa*(beta**2*s.sin(2*x)**2-2*beta*s.cos(2*x))
assert s.simplify(-kappa*s.diff(vacuum,x,2)+potential*vacuum) == 0
# A = d/dx + beta sin(2x), A* = -d/dx + beta sin(2x).
u = s.Function('u')(x)
Au = s.diff(u,x)+beta*s.sin(2*x)*u
assert s.simplify(kappa*(-s.diff(Au,x)+beta*s.sin(2*x)*Au)
                  -(-kappa*s.diff(u,x,2)+potential*u)) == 0
I, X = s.eye(2), s.Matrix([[0,1],[1,0]])
H = s.kronecker_product(I-X,I)+epsilon*s.kronecker_product(I,I-X)
z = s.symbols('z')
assert s.expand(H.charpoly(z).as_expr()-z*(z-2)*(z-2*epsilon)*(z-2-2*epsilon)) == 0
print('Four exact CAS identities passed; analytic domain/limit hypotheses are not CAS-proved.')
'''

RESIDUALS = '''def verify_residuals(report):
    from fractions import Fraction as F
    count = 0
    for theory in ('SU2', 'U1'):
        for cell in report['data'][theory+'_finest_certificates']:
            g = F(str(cell['g']))
            hopping = -1/(g*g)  # all archived development cells have eta=1
            result = cell['result']
            eigen = result['enclosures' if theory=='SU2' else 'even_enclosures']
            for k, (encoded, bound) in enumerate(zip(result['candidate_vectors_hex'], result['vector_bounds'])):
                q = [F(float.fromhex(x)) for x in encoded]
                assert q and any(q)
                if theory == 'SU2':
                    diagonal = [g*g*n*(n+2) for n in range(len(q))]
                else:
                    assert len(q)%2 == 1 and q == q[::-1]
                    K = len(q)//2
                    diagonal = [4*g*g*(n-K)**2 for n in range(len(q))]
                mu = (F(eigen[k]['lower'])+F(eigen[k]['upper']))/2
                separation = F(eigen[k+1]['lower'])-mu
                if k:
                    separation = min(separation, mu-F(eigen[k-1]['upper']))
                norm = sum(x*x for x in q)
                residual = [(diagonal[n]-mu)*q[n]
                            +(hopping*q[n-1] if n else 0)
                            +(hopping*q[n+1] if n+1<len(q) else 0)
                            for n in range(len(q))]
                residual.append(hopping*q[-1])
                if theory == 'U1':
                    residual.append(hopping*q[0])
                squared = sum(x*x for x in residual)/norm
                rho = F(bound['residual_norm_upper'])
                assert norm == F(bound['norm_squared']) and mu == F(bound['rayleigh_reference'])
                assert separation == F(bound['separation_lower']) and separation > 0
                assert rho >= 0 and rho*rho >= squared
                assert F(bound['distance_upper']) >= min(F(2),2*rho/separation)
                count += 1
    assert count == 80
    print('80 full infinite-Jacobi residual bounds verified with exact rational arithmetic.')
'''


def digest(data):
    return hashlib.sha256(data).hexdigest()


SCALARS = '''def verify_scalar_accuracy(report):
    from fractions import Fraction as F
    count = 0
    for theory in ('SU2', 'U1'):
        cells = report['data'][theory+'_scalar_accuracy']
        assert len(cells) == 10
        for cell, certificate in zip(cells, report['data'][theory+'_finest_certificates']):
            assert cell['g'] == certificate['g']
            exact = certificate['result']
            vacuum = exact['vacuum']
            moments = [*vacuum['raw_moments'][:2], vacuum['covariance'][0][0],
                       vacuum['covariance'][1][1], vacuum['covariance'][0][1]]
            gaps = list(exact['first_three_gap_intervals' if theory=='SU2' else 'first_three_even_gap_intervals'])
            if theory == 'U1':
                gaps.append(exact['parity']['full_gap_interval'])
            assert len(cell['values']) == len(cell['assessment']['methods']) == 2
            for method, values in cell['values'].items():
                bound = cell['assessment']['methods'][method]
                for key, intervals, relative in (('moments', moments, False), ('gaps', gaps, True)):
                    assert len(values[key]) == len(intervals)
                    errors = []
                    for value, endpoints in zip(values[key], intervals):
                        lo, hi = map(F, endpoints)
                        assert lo <= hi and (not relative or lo > 0)
                        error = max(abs(F(value)-lo), abs(F(value)-hi))
                        errors.append(error/lo if relative else error)
                    field = 'gap_relative_error_upper' if relative else 'moment_absolute_error_upper'
                    assert errors == list(map(F, bound[field]))
                    assert all(e <= F(1, 10**6) for e in errors)
                assert bound['qualifies'] is True
                count += 1
            assert cell['assessment']['qualifies'] is True
    assert count == 40
    return count
'''


def svg(fig):
    stream = io.StringIO()
    fig.savefig(stream, format='svg', metadata={'Date': None}, bbox_inches='tight')
    plt.close(fig)
    return stream.getvalue()[stream.getvalue().index('<svg'):]


def main():
    exec(compile(CAS, '<embedded-cas-checks>', 'exec'), {})
    names = ['design-readiness.json', 'result-contract.json', 'pilot-disposition.json',
             'vacuum-coercivity-check.json', 'execution-contract.json', 'target-result-envelope.json']
    selected = (D/'selected-summary.json').exists()
    live = not selected and (D/'selected-live-snapshot.json').exists()
    if live:names += ['selected-live-snapshot.json']
    if selected:
        names += ['selected-registration.json','selected-summary.json','selected-run/index.json','selected-run/verification.json']
    data = {n: json.loads((D/n).read_text()) for n in names}
    execution_contract.validate(data['execution-contract.json'])
    target_envelope.validate(data['target-result-envelope.json'])
    audit = data['design-readiness.json']
    rows = audit['cells']
    assert len(rows) == 20 and all(r['status'] == 'development_qualified' for r in rows)
    assert len(audit['targets']) == 42 and all(t['status'] == 'unrun' for t in audit['targets'])
    assert data['pilot-disposition.json']['original_pilot_replication'] == 'unverifiable_source_lost'
    documents = ['VACUUM-COERCIVITY.md', 'V3-FOCUS.md', 'REVIEW-HANDOFF.md',
                 'PILOT-DISPOSITION.md', 'RESULT-CONTRACT.md', 'DESIGN-READINESS.md',
                 'DESIGN-NULLS.md', 'TARGET-COST-PLAN.md']
    if selected or live:documents += ['SELECTED-REGISTRATION.md','selected-validation.txt','selected-run/console-observations.txt']
    # Exact archived finest-rung certificates are retained, not recomputed.
    for theory, name in [('SU2', 'certificates.json'), ('U1', 'u1-design-certificates.json')]:
        archive = json.loads((D/name).read_text())
        data[theory+'_finest_certificates'] = [
            {'g': c['g'], 'result': c['rungs'][-1]['result']} for c in archive['cells']]
    for theory, name in [('SU2', 'late-times.json'), ('U1', 'u1-design-semigroup.json')]:
        archive = json.loads((D/name).read_text())
        data[theory+'_time_window_evidence'] = [
            {'g': c['g'], 'times': c['times'],
             'finest_assessment': c['window_assessment']['rungs'][-1],
             'finest_correlation_error_bounds': c['angle_error_bounds'][-1]}
            for c in archive['cells']]
    for theory,name in [('SU2','refinement.json'),('U1','u1-design-development.json')]:
        archive=json.loads((D/name).read_text())
        evaluated=[]
        assert len(archive['cells']) == len(data[theory+'_finest_certificates']) == 10
        for cell,certificate in zip(archive['cells'],data[theory+'_finest_certificates']):
            assert cell['g']==certificate['g'] and cell['eta']==1
            final={k:v for k,v in cell['final'].items() if k!='angle_second'}
            assessment=scalar_accuracy({'scalar':{'result':{'final':final}},
                'certificates':{'result':certificate['result']}},theory)
            assert assessment['qualifies']
            values={k:{'moments':[str(F(v)) for v in r['moments']],
                       'gaps':[str(F(v)) for v in [*r['first_three_gaps'],
                               *([r['full_gap']] if theory=='U1' else [])]]} for k,r in final.items()}
            evaluated.append({'g':cell['g'],'values':values,'assessment':assessment})
        data[theory+'_scalar_accuracy']=evaluated
    sources = names + documents + ['certificates.json', 'u1-design-certificates.json',
        'refinement.json', 'late-times.json', 'u1-design-development.json', 'u1-design-semigroup.json',
        'design-bundle-v3/manifest.json']
    hashes = {n: digest((D/n).read_bytes()) for n in sources}
    payload = {'format': 'vacuum-report-v1', 'numerical_baseline_commit': '4b96f84614a5ceda04269af7a5a1d4e91a27ef95',
        'report_generator_sha256': digest(Path(__file__).read_bytes()),
        'scope': 'Exploratory single-angle development; no continuum gap proof; no target execution',
        'tool_versions': {'sympy': sp.__version__, 'matplotlib': matplotlib.__version__},
        'source_sha256': hashes, 'data': data, 'cas_program': CAS,
        'cas_sha256': digest(CAS.encode()),
        'report_review': {'status': 'no_outstanding_defects_in_reviewed_scope',
            'reviewer': 'separate_agent_report_review',
            'scope': ['mathematical_consistency', 'provenance', 'executable_checks', 'basic_accessibility'],
            'excluded': ['complete_numerical_instrument_certification', 'continuum_coercivity', 'browser_rendering'],
            'report_tests_passed': 5},
        'combined_error_review': {
            'status': 'no_blocking_defect_in_reviewed_composition',
            'reviewer': 'separate_agent_report_review',
            'scope': 'end-to-end sampled error, outward log slopes, mixture-plus-numerical bound, U1 even threshold',
            'remaining': 'future-run executor and registration checks; not a formal proof',
            'source_sha256': {p: digest((ROOT/p).read_bytes()) for p in (
                'scripts/vacuum_certificate_run.py', 'scripts/vacuum_time_windows.py',
                'scripts/vacuum_semigroup.py', 'scripts/vacuum_u1_design_semigroup_run.py')}},
        'analytic_certificate_review': {
            'status': 'no_correctness_defect_found_in_reviewed_analytic_chain',
            'reviewer': 'separate_agent_report_review',
            'scope': ['Sturm_Schur_endpoints', 'U1_parity_and_mapping',
                      'infinite_residual_and_eigenvector_distance', 'signed_overlaps',
                      'padded_moments', 'PSD_omitted_tail'],
            'qualification': 'analytic/code inspection under stated arithmetic contracts; not proof-assistant verification',
            'source_sha256': {p: digest((ROOT/p).read_bytes()) for p in (
                'scripts/vacuum_certified.py', 'scripts/vacuum_u1_certified.py',
                'scripts/vacuum_u1_design_certified.py', 'scripts/vacuum_intervals.py')}},
        'future_adapter': {
            'status': 'non_executing_adapter_implemented',
            'independent_review': 'identified_selection_failure_retention_and_schema_defects_fixed; no_outstanding_defect_in_adapter_scope',
            'repairs': ['eta_zero_selection_from_actual_certificates', 'partial_stage_retention',
                        'schema_validation_of_stage_results_and_reasons'],
            'remaining': ['registered_target_executor', 'authorization_and_registration_integration'],
            'source_sha256': {p: digest((ROOT/p).read_bytes()) for p in (
                'scripts/vacuum_future_adapter.py', 'scripts/test_vacuum_future_adapter.py',
                'research/vacuum-spectrum/future-stage-input.schema.json')}},
        'parameterized_certificate': {
            'status': 'implemented_and_calibration_tested',
            'independent_review': 'no_outstanding_defect_in_producer_and_verified_adapter_scope_after_endpoint_validation_repair',
            'calibration_scope': 'g=1 only; eta=0,1/2,1; SU2 and U1; cutoff=8; no target coordinates',
            'tests_passed': 6,
            'verified_adapter_entry': 'vacuum_parameterized_certificate.verified_channels',
            'source_sha256': {p: digest((ROOT/p).read_bytes()) for p in (
                'scripts/vacuum_parameterized_certificate.py',
                'scripts/test_vacuum_parameterized_certificate.py')}},
        'parameterized_temporal': {
            'status': 'implemented_and_calibration_tested',
            'independent_review': 'no_outstanding_defect_in_temporal_kernel_scope_after_partial_evidence_repair',
            'tests_passed': 7,
            'scope': 'direct propagation; exact sampled clocks; channel-specific thresholds; all requested grid/tolerance slots retained',
            'limitations': 'no target CLI, registration or full-run authorization envelope',
            'source_sha256': {p: digest((ROOT/p).read_bytes()) for p in (
                'scripts/vacuum_parameterized_temporal.py',
                'scripts/test_vacuum_parameterized_temporal.py')}},
        'parameterized_scalar': {
            'status': 'implemented_and_calibration_tested', 'tests_passed': 10,
            'independent_review': 'comparison_failure_and_spectral_sum_rule_repairs_reviewed; nonfinite_computed_defects_rejected',
            'scope': 'representation ladders; all rungs retained; no fallback after finest failure; agreement diagnostic only',
            'source_sha256': {p: digest((ROOT/p).read_bytes()) for p in (
                'scripts/vacuum_parameterized_scalar.py',
                'scripts/test_vacuum_parameterized_scalar.py')}},
        'run_envelope': {
            'status': 'development_and_calibration_integration_tested', 'tests_passed': 14,
            'independent_review': 'development_envelope_accounting_exact_scalar_accuracy_and_control_preflight_repairs_reviewed',
            'scope': 'all requested rungs accounted; immutable checkpoint snapshots; exact scalar accuracy; common sampled windows; final source audit',
            'limitations': 'development couplings only; no registered target executor; no continuum conclusion',
            'source_sha256': {p: digest((ROOT/p).read_bytes()) for p in (
                'scripts/vacuum_run_envelope.py', 'scripts/test_vacuum_run_envelope.py',
                'research/vacuum-spectrum/run-envelope.schema.json')}},
        'temporal_replay': {
            'status': 'implemented_and_calibration_tested', 'tests_passed': 5,
            'independent_review': 'no_blocking_defect_within_stored_arithmetic_and_accounting_scope',
            'scope': 'certificate identity and clock; every requested grid/tolerance; correlation errors; sampled windows; retained failed prefixes',
            'limitations': 'does not rerun or authenticate propagation; no standalone BDF error theorem',
            'source_sha256': {p:digest((ROOT/p).read_bytes()) for p in (
                'scripts/vacuum_temporal_replay.py','scripts/test_vacuum_temporal_replay.py')}},
        'scalar_replay': {
            'status': 'implemented_and_calibration_tested', 'tests_passed': 5,
            'independent_review': 'no_blocking_defect_within_stored_scalar_arithmetic_and_request_identity_scope',
            'scope': 'coordinates; methods and sizes; completed-record consistency; finest-rung identity; recomputed comparisons; failed evidence retained',
            'limitations': 'solver execution not authenticated; exact certificate accuracy remains separate',
            'source_sha256': {p:digest((ROOT/p).read_bytes()) for p in (
                'scripts/vacuum_scalar_replay.py','scripts/test_vacuum_scalar_replay.py')}},
        'whole_result_replay': {
            'status': 'implemented_and_calibration_tested', 'tests_passed': 7,
            'independent_review': 'malformed_input_and_required_control_inventory_repairs_reviewed; no_qualification_bypass_found',
            'scope': 'current-source development manifests; every successful certificate and retiming; scalar/temporal replay; exact accuracy; adaptation; cell and run outcomes; named controls',
            'limitations': 'source drift is invalid for current-source replay; recorded controls/failures do not authenticate execution; targets disabled',
            'source_sha256': {p:digest((ROOT/p).read_bytes()) for p in (
                'scripts/vacuum_run_replay.py','scripts/test_vacuum_run_replay.py',
                'research/vacuum-spectrum/control-preflight.schema.json')}},
        'execution_protocol_draft': {
            'registered': False, 'selected_target_ids': [], 'target_execution_authorized': False,
            'scope': 'finite SU2 and corrected U1 rotor characterization',
            'definition': data['execution-contract.json']['protocol'],
            'environment': data['execution-contract.json']['environment'],
            'validation_scope': 'nonexecuting draft and terminal-cell structure; not scientific result replay or authorization',
            'tests_passed': 4,
            'independent_review': 'no_defect_in_nonexecuting_draft_and_terminal_cell_structural_scope',
            'source_sha256': {p:digest((ROOT/p).read_bytes()) for p in (
                'scripts/vacuum_execution_contract.py', 'scripts/test_vacuum_execution_contract.py',
                'research/vacuum-spectrum/execution-contract.schema.json')},
            'next_required_input': 'user_target_selection',
            'after_selection': ['commit_selected_registration', 'enable_and_validate_exact_subset_execution_path'],
            'cost_limitations': 'historical eta=1 stage timings; integration checkpoint overhead and deformation runtimes unmeasured'},
        'target_envelope': {
            'status': 'ready_for_user_target_selection', 'tests_passed': 3,
            'independent_review': 'no_defect_within_preselection_envelope_and_denial_gate_scope',
            'planned_requests': {'scalar':378,'certificates':210,'temporal':336},
            'scope': 'all42unselected; nullresults; exact protocol requests; valid draft always denies execution',
            'source_sha256': {p:digest((ROOT/p).read_bytes()) for p in (
                'scripts/vacuum_target_envelope.py','scripts/test_vacuum_target_envelope.py',
                'research/vacuum-spectrum/target-result-envelope.schema.json')}},
        'blockers': {'independent_review': 'preselection_development_review_complete_with_stated_scope_limits',
                     'next_required_input': 'user_target_selection',
                     'user_review': 'user_will_review_completed_document; not_required_to_continue_repairs',
                     'owner_assigned_P_LC_ids': 'optional_in_quod; required_only_for_legacy_ledger_submission',
                     'registration': 'unregistered; required_before_future_target_execution'},
        'analytic_claims': [
            {'id': 'ground_transform', 'status': 'analytic_proof_with_CAS_local_identity',
             'hypotheses': ['compact connected configuration manifold', 'theta=0',
                 'smooth positive normalized invariant vacuum', 'H psi0=E0 psi0',
                 'divergence-free kinetic derivatives', 'physical form core and closure']},
            {'id': 'bounded_potential_comparison', 'status': 'analytic_minmax_proof_not_formalized',
             'formula': 'gap(T+V) >= gap(T) - (sup(V)-inf(V))',
             'hypotheses': ['self-adjoint nonnegative T with compact resolvent',
                            'simple free vacuum', 'bounded self-adjoint multiplication V']},
            {'id': 'uniform_YM_coercivity', 'status': 'unproved'}]}
    plt.rcParams.update({'svg.hashsalt': 'vacuum-single-report-v1', 'font.size': 10})
    selected_section = ''
    if selected:
        summary=data['selected-summary.json']
        selected_namespace={}
        exec(compile(selected_report.CHECKS,'<selected-checks>','exec'),selected_namespace)
        selected_namespace['verify_selected'](payload)
        payload['scope']='Registered 42-cell finite-rotor characterization plus archived development; no uniform Yang-Mills gap proof'
        payload['selected_run']={'registration_commit':summary['registration_commit'],'verification':summary['verification'],
            'source_sha256':{name:digest((ROOT/name).read_bytes()) for name in ('scripts/vacuum_selected_report.py','scripts/test_vacuum_selected_report.py')}}
        payload['historical_preselection_records']=['execution-contract.json','target-result-envelope.json','design-readiness.json']
        payload['blockers'].update(next_required_input='next_research_direction_after_fixed_run',registration='committed_and_executed_all42')
        fig,ax=plt.subplots(figsize=(10,3.2),constrained_layout=True)
        ordered=summary['cells']; gs=list(dict.fromkeys(r['g'] for r in ordered))
        groups=[(t,e) for t in ('SU2','U1') for e in ('0','0.5','1')]
        colors={'instrument_agreement':'#287d57','unresolved':'#d39b28','failure':'#b54747'}
        for row in ordered:
            x=gs.index(row['g']);y=groups.index((row['theory'],row['eta']))
            ax.scatter(x,y,s=440,marker='s',color=colors[row['status']])
        ax.set_xticks(range(7),gs);ax.set_yticks(range(6),[t+', η='+e for t,e in groups]);ax.set_xlabel('g');ax.invert_yaxis()
        target_figure=svg(fig).replace('<svg ','<svg role="img" aria-label="All 42 registered cell outcomes. Green: instrument agreement; amber: unresolved; red: failure. Exact outcomes and gaps appear in the following table." ',1)
        counts=summary['verification']['outcomes']
        selected_section='<h2>Registered 42-cell results</h2><p><b>'+escape(str(counts))+'</b>. All 42 selected cells were attempted, with '+str(summary['verification']['checkpoints'])+' preserved checkpoints. Registration commit <code>'+summary['registration_commit']+'</code> preceded target execution. The final pre-execution suite passed 211 tests in 78.436 seconds. Full raw-evidence and checkpoint replay passed after execution.</p>'
        lower=summary.get('finite_family_full_gap_lower')
        if lower is not None and F(lower)>0:
            floor=F(lower).numerator*10**9//F(lower).denominator
            displayed=f'{floor//10**9}.{floor%10**9:09d}'
            selected_section+='<p><b>Common bound on the selected finite family:</b> every full-gap lower endpoint is positive. Their minimum, c<sub>grid</sub>, is at least '+displayed+' (decimal rounded downward; exact rational minimum embedded). For rotor r, let dν<sub>r</sub>=|ψ₀,r|²dU<sub>r</sub> and Q<sub>r</sub>[f]=q<sub>Hᵣ</sub>[ψ₀,r f]−E₀,r‖ψ₀,r f‖². Then Q<sub>r</sub>[f] ≥ c<sub>grid</sub> Var<sub>νᵣ</sub>(f) for every physical form-domain f, under the stated ground-transform hypotheses. This minimum covers these 42 named Hamiltonians only. It supplies no lower bound uniform in an increasing lattice, physical volume, continuum limit, or an unselected coupling domain.</p>'
        selected_section+='<p>The raw cells and append-only checkpoint inventory are retained in <code>research/vacuum-spectrum/selected-run/</code>. Reproduce the complete solver-free replay with <code>OPENBLAS_NUM_THREADS=1 python3 scripts/vacuum_registered_run.py verify --registration-commit '+summary['registration_commit']+'</code>. The embedded checks below verify summary bindings and exact interval arithmetic; spectral-certificate and stored-correlation error/window replay uses the pinned repository sources and raw files.</p>'
        selected_section+='<figure>'+target_figure+'<figcaption>Fixed-run outcomes: green = instrument agreement; amber = unresolved; red = failure.</figcaption></figure>'
        selected_section+='<p>Gap values below are rounded interval midpoints; exact rational endpoints, thresholds, finest evidence and all matched deformation differences are embedded in the machine data. A certificate interval can remain informative when the overall instrument outcome is unresolved. Sample-pair indices refer to τ=(0, 1/8, 1/4, 1/2, 1, 2, 4, 8, 12, 16, 20, 24), scaled by that cell’s frozen certificate clock. Every adjacent pair was assessed; all qualifying common pairs are shown.</p>'+selected_report.table(summary)
        deformation_rows=[]
        for comparison in summary['deformation_comparisons']:
            values=[comparison['cell']]
            for field in ('full_gap','P_threshold','P2_threshold','mean_P','variance_P'):
                interval=comparison['difference_intervals'][field]
                values.append('unresolved' if interval is None else '['+format(float(F(interval[0])),'.7g')+', '+format(float(F(interval[1])),'.7g')+']')
            deformation_rows.append('<tr>'+''.join('<td>'+escape(v)+'</td>' for v in values)+'</tr>')
        selected_section+='<details><summary>Matched deformation differences: η minus 0 at the same theory and g</summary><p>Displayed endpoints are rounded; exact interval subtraction [a,b]−[c,d]=[a−d,b−c] and all five vacuum-component differences are embedded. These describe the specified finite Hamiltonians.</p><table><tr><th>Cell</th><th>Δ full gap</th><th>Δ P threshold</th><th>Δ P² threshold</th><th>Δ mean P</th><th>Δ variance P</th></tr>'+''.join(deformation_rows)+'</table></details>'
        selected_section+='<p>A BDF runtime warning was observed during SU(2), g=0.40, η=0.5. Its raw stage records completed and passed the registered replay. The warning observation is preserved in the supporting records; no rerun or budget change followed it.</p>'
        if counts.get('failure',0):
            decision='The next decision is how to address the retained instrument failures in a separate registration before extending the research model.'
        elif counts.get('unresolved',0):
            decision='The next decision is whether to design a separately registered instrument study for the explicitly unmet checks, or move to a specified lattice/volume family with a uniform-coercivity hypothesis.'
        else:
            decision='All registered checks were met, so this run supplies no unresolved-check reason to expand its schedule. The next research decision is the regulated lattice/volume family and the analytic hypothesis that could make its coercivity constant uniform. That choice must specify the physical quotient, norm, and limiting parameters before another target study.'
        selected_section+='<p><b>Limits and next decision:</b> no budget, ladder or schedule was extended. Instrument agreement characterizes the named finite rotor. Unresolved precision or window checks do not establish a zero gap. Full gaps and observable-accessible thresholds remain distinct; P² can select a higher level at η=0, and corrected-U(1) even probes cannot detect an odd-sector full gap. Matched deformation intervals measure only the specified Hamiltonian change, and a change of accessible leading level must not be read as full-gap collapse. '+decision+' A uniform theorem does not follow from this finite family. The original pilot remains permanently unverifiable.</p>'
    if live:
        snapshot=data['selected-live-snapshot.json']; counts=snapshot['counts']
        namespace={};exec(selected_report.LIVE_CHECKS,namespace);namespace['verify_live'](payload)
        payload['scope']='Ongoing registered finite-rotor execution; partial results; no complete-run verification or uniform Yang-Mills proof'
        payload['historical_preselection_records']=['execution-contract.json','target-result-envelope.json','design-readiness.json']
        payload['selected_live']={'counts':counts,'snapshot_utc':snapshot['snapshot_utc'],
            'source_sha256':{name:digest((ROOT/name).read_bytes()) for name in ('scripts/vacuum_selected_report.py','scripts/test_vacuum_selected_report.py')}}
        payload['blockers'].update(next_required_input='none; user_confirmed_continuation_of_frozen_run',registration='committed_execution_ongoing')
        selected_section='<h2>Registered execution: live partial handoff</h2><p><b>'+escape(str(counts))+'</b>, as of '+escape(snapshot['snapshot_utc'])+'. Registration <code>'+snapshot['index']['registration_commit']+'</code> was committed after 211 pre-execution tests passed and before the first target solver. Completed raw cells have been replayed, and all 21 SU(2) records were independently reviewed. This is not a complete-run verification.</p>'
        selected_section+='<p>The pre-execution tests exercised smaller free-case calibrations; they did not establish completion cost for the full free periodic schedule at the registered strict tolerance. The first U(1) cell is in its 600-node, tight-tolerance BDF call. Read-only samples indicate expensive computation before its first positive scheduled sample; some sampled locals are inconsistent because inspection was nonblocking. They do not prove a numerical failure or provide a reliable completion-time estimate. The frozen protocol has no runtime cutoff and no per-propagation checkpoint inside this stage. The user has explicitly instructed continuation; the original run remains active and unchanged. Unfinished work is not classified as a completed unresolved assessment.</p>'
        visible=[]
        for row in snapshot['rows']:
            values=[row['theory'],row['g'],row['eta'],row['status'],selected_report.display(row['full_gap_interval']) if row['raw'] else 'not available']
            for observable in ('P','P2'):
                channel=row['thresholds'].get(observable,{})
                values.append(selected_report.display(channel.get('gap_interval')) if row['raw'] else 'not available')
            visible.append('<tr>'+''.join('<td>'+escape(v)+'</td>' for v in values)+'</tr>')
        selected_section+='<table><tr><th>Theory</th><th>g</th><th>η</th><th>Snapshot status</th><th>Full gap midpoint</th><th>P threshold midpoint</th><th>P² threshold midpoint</th></tr>'+''.join(visible)+'</table>'
        selected_section+='<p>Exact rational intervals and completed finest certificates are embedded. A running or unrun row has no reported final numerical result; partial scalar and certificate evidence for the active cell remains in the retained checkpoints. For the free corrected-U(1) model, C<sub>PP</sub>(t)=½e<sup>−4g²t</sup> and C<sub>P²P²</sub>(t)=⅛e<sup>−16g²t</sup>, with zero cross-correlation. These analytic diagnostics do not substitute for the registered numerical requests or imply that long runtime is physical gap collapse.</p>'
        selected_section+='<p><b>Operational instruction:</b> the user confirmed continuation of the unchanged registered computation. No further confirmation is needed to keep running. Any revised solver or stopping rule requires a separate protocol; current budgets and schedules are not widened. The original pilot remains permanently unverifiable. Partial finite-rotor evidence supplies no uniform Yang–Mills gap proof.</p>'
    raw = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()
    encoded = base64.b64encode(gzip.compress(raw, mtime=0)).decode()
    plt.rcParams.update({'svg.hashsalt': 'vacuum-single-report-v1', 'font.size': 10})
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.6), constrained_layout=True)
    for ax, theory in zip(axes, ('SU2', 'U1')):
        cells = [r for r in rows if r['theory'] == theory]
        for field, label, marker in [('full_gap_interval','Full physical gap','o'),
                                     ('observable_gap_interval','Probe threshold','x')]:
            intervals = [(F(c[field][0]), F(c[field][1])) for c in cells]
            mid = [float((a+b)/2) for a,b in intervals]
            err = [float((b-a)/2) for a,b in intervals]
            ax.errorbar([c['g'] for c in cells], mid, yerr=err, marker=marker, label=label)
        ax.set(xscale='log', yscale='log', xlabel='g (development cells only)', ylabel='Energy in model units', title=theory+', eta = 1')
        ax.grid(alpha=.2)
        ax.legend()
    spectra = svg(fig).replace('<svg ', '<svg role="img" aria-label="Development spectra: SU2 full gap and probe threshold coincide; U1 even probe threshold exceeds the full gap. Numeric values follow in the table." ', 1)
    fig, ax = plt.subplots(figsize=(8, 3), constrained_layout=True)
    samples = data['vacuum-coercivity-check.json']['samples']
    ax.plot([r['m'] for r in samples], [float(F(r['gap_over_kappa_upper'])) for r in samples], 'o-')
    ax.set(xscale='log', yscale='log', xlabel='m, with beta = m^4', ylabel='Certified upper bound on gap / kappa',
           title='Fixed kinetic coefficient does not ensure a uniform gap')
    ax.grid(alpha=.2)
    counter = svg(fig).replace('<svg ', '<svg role="img" aria-label="Counterexample gap upper bounds decrease toward zero as m increases. Six numeric bounds follow in a table." ', 1)
    counter_table = ''.join('<tr><td>'+str(r['m'])+'</td><td>'+format(float(F(r['gap_over_kappa_upper'])), '.9g')+'</td></tr>' for r in samples)
    table = ''.join('<tr>'+''.join('<td>'+escape(str(v))+'</td>' for v in
        (r['theory'], r['g'], format(float(sum(map(F,r['full_gap_interval']))/2), '.9g'),
         format(float(sum(map(F,r['observable_gap_interval']))/2), '.9g'),
         len(r['qualifying_common_sample_pairs'])))+'</tr>' for r in rows)
    extraction = '''import base64, gzip, hashlib, json, re
from fractions import Fraction
from pathlib import Path
html = Path('VACUUM-REPORT.html').read_text()
tag = re.search(r'<script id="machine-data" type="application/octet-stream" data-sha256="([0-9a-f]+)">(.*?)</script>', html, re.S)
raw = gzip.decompress(base64.b64decode(tag.group(2)))
assert hashlib.sha256(raw).hexdigest() == tag.group(1)
report = json.loads(raw)
assert hashlib.sha256(report['cas_program'].encode()).hexdigest() == report['cas_sha256']
exec(compile(report['cas_program'], '<report-cas>', 'exec'), {})
audit = report['data']['design-readiness.json']
assert len(audit['cells']) == 20
target = report['data']['target-result-envelope.json']
assert target['selected_target_ids'] == [] and target['target_execution_authorized'] is False
assert target['targets_run'] == 0 and len(target['rows']) == 42
assert all(r['selected'] is False and r['status'] == 'unrun' and r['result'] is None for r in target['rows'])
assert target['contract_sha256'] == report['source_sha256']['execution-contract.json']
assert [r['id'] for r in target['rows']] == [r['id'] for r in audit['targets']]
assert len(audit['targets']) == 42 and all(t['status']=='unrun' for t in audit['targets'])
for cell in audit['cells']:
    for field in ('full_gap_interval','observable_gap_interval'):
        lo, hi = map(Fraction, cell[field])
        assert 0 < lo <= hi
assert report['data']['pilot-disposition.json']['historical_replication_verified'] is False
for theory in ('SU2','U1'):
    for cell in report['data'][theory+'_time_window_evidence']:
        for pair in cell['finest_assessment']['pairs']:
            for observable in pair['observables']:
                if observable['qualifies']:
                    mixture = Fraction(observable['relative_mixture_bias_upper'])
                    numerical = Fraction(observable['relative_numerical_slope_error_upper'])
                    total = Fraction(observable['relative_combined_error_upper'])
                    assert mixture >= 0 and numerical >= 0 and total == mixture+numerical
                    assert total <= Fraction(1,1000000) and observable['nonzero_first_overlap']
print('Embedded data digest, exact interval ordering, target boundary and CAS checks passed.')
# For the full numerical certificate replay use the pinned repository sources.
'''
    extraction += '\n' + RESIDUALS + '\nverify_residuals(report)\n'
    extraction += '\n' + SCALARS + '\nverify_scalar_accuracy(report)\n'
    if selected:extraction += '\n'+selected_report.CHECKS+'\nverify_selected(report)\n'
    if live:extraction += '\n'+selected_report.LIVE_CHECKS+'\nverify_live(report)\n'
    appendix = ''.join('<details><summary>'+escape(n)+'</summary><pre>'+escape((D/n).read_text())+'</pre></details>' for n in documents)
    html = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Vacuum spectrum — evidence and proof obligations</title>
<style>body{{font:17px/1.55 system-ui,sans-serif;max-width:1120px;margin:auto;padding:32px;color:#182b39;background:#fafbfd}}h1,h2,h3{{line-height:1.2}}h2{{margin-top:2em;border-top:1px solid #ccd5dd;padding-top:1em}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:#edf2f6;padding:18px;font-size:13px}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{padding:7px;border-bottom:1px solid #ccd5dd;text-align:left}}svg{{max-width:100%;height:auto}}.cards{{display:flex;gap:12px;flex-wrap:wrap}}.card{{padding:16px;background:#e7eff5;border-radius:8px;flex:1;min-width:200px}}.equation{{font-size:19px;background:#edf3ef;padding:18px}}summary{{cursor:pointer;font-weight:600;padding:12px}}.open{{background:#fff0d4}}@media print{{body{{background:white;padding:0}}details{{break-inside:avoid}}}}</style>
<h1>Vacuum spectrum: evidence, exact math, and remaining decisions</h1>
<p>Consolidated 2026-09-09. Exploratory finite-rotor study; v3 source revision incorporated.
The vacuum reduction is exact. A cutoff- and volume-uniform Yang–Mills gap is unproved.</p>
<div class="cards"><div class="card"><b>20 development cells</b><br>Archived bounds, overlaps and sampled windows qualify.</div>
<div class="card"><b>202 regression tests passed</b><br>Recorded pre-selection run: 76.243 s; source hashes embedded below.</div>
<div class="card open"><b>42 targets unrun</b><br>No registration or target execution authorization.</div></div>
{selected_section}
<h2>1. Historical pre-selection handoff</h2>
<p><b>The development prerequisites are complete through the target-selection boundary.</b>
The next required input is which target cells to characterize. The complete candidate set
is both SU(2) and U(1), with g ∈ {{0.125, 0.25, 0.40, 0.60, 0.85, 1.25, 2.50}} and
η ∈ {{0, 0.5, 1}}: 42 cells. A subset or the full set can be specified. None is selected.
After that decision, commit the selected registration and enable and validate its exact
execution path before running anything. Independent readiness review found no further
numerical sweep necessary merely to make this selection.</p>
<p><b>Independent review:</b> a separate agent reviewed mathematical consistency, provenance,
executable checks and basic accessibility. Its two findings were corrected; no outstanding
defects remain within that scope. A subsequent independent analytic/code review found no
correctness defect in the spectral endpoint, residual, overlap, covariance, omitted-tail and
sampled-error chain. All five report-specific tests pass, including the exact embedded verifier,
80 rational residual checks, and rejection of CAS sign-error and residual-underestimate mutants.
This is not proof-assistant verification or certification of future execution,
continuum coercivity or browser rendering. The user will review this
completed document; clear defects can be repaired without waiting for further input.
<b>P/LC identifiers:</b> P denotes a prediction/experiment registration and LC a literature check
in the original proslambenomenos ledgers. Assignment is needed only if registering through that
owner workflow; it does not block this report, mathematical development or review in quod.
Labels are optional in quod: commit hashes, artifact checksums and manifests provide the
present traceability. A committed future specification, not a label format, is the substantive
prerequisite for target execution. The numerical baseline is
4b96f84614a5ceda04269af7a5a1d4e91a27ef95; the earlier handoff was published at 690ce6b.
This newer report identifies its generator by SHA-256 in the embedded metadata.
The reviewed repairs are complete; a selected registration remains necessary before execution. The original pilot is permanently
unverifiable because its script and results are lost; recovery is no longer requested.</p>
<h2>2. Physical models and exact reduction</h2>
<table><tr><th>Model</th><th>Physical space and operator</th><th>Free gap</th></tr>
<tr><td>SU(2)</td><td>Haar class functions; H = 4g² C₂ − 2ηP/g²; P = cos x</td><td>3g²</td></tr>
<tr><td>U(1)</td><td>Periodic Haar functions; H = −4g² ∂²θ − 2η cos θ/g²</td><td>4g², both parities</td></tr></table>
<p>g &gt; 0, η ≥ 0. Work at theta angle zero. For the general compact-link form,
H = −κΣXⱼ² + V, κ &gt; 0. Xⱼ are divergence-free invariant derivatives.
The Gauss constraint restricts Ψ to invariant functions. Let ψ₀ be the smooth,
strictly positive normalized vacuum and P₀ its projection. Set Ψ = ψ₀f and dν = ψ₀²dU.</p>
<div class="equation">Hψ₀ = E₀ψ₀<br>q[ψ₀f] = ⟨ψ₀f,(H−E₀)ψ₀f⟩ = κ∫Σ|Xⱼf|²dν<br>‖(I−P₀)Ψ‖² = Var<sub>ν</sub>(f)</div>
<p>Expanding the energy leaves a total derivative plus the displayed Dirichlet form.
Haar integration by parts removes that derivative; the vacuum equation removes the residual
potential term. Closure extends the identity from the smooth physical core. The potential
still determines ν. This is not cancellation of uncontrolled continuum infinities.</p>
<h2>3. Proof dependency map</h2>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 210" role="img" aria-label="Vacuum identity needs an independent positive estimate and a limit construction to prove a uniform gap">
<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10Z" fill="#435d70"/></marker></defs>
<g fill="#e7eff5" stroke="#435d70"><rect x="5" y="40" width="225" height="120" rx="8"/><rect x="265" y="40" width="220" height="120" rx="8"/><rect x="520" y="40" width="220" height="120" rx="8" fill="#fff0d4"/><rect x="775" y="40" width="220" height="120" rx="8" fill="#fff0d4"/></g>
<g font-family="sans-serif" font-size="16" text-anchor="middle"><text x="117" y="80">Constraints + vacuum</text><text x="117" y="110">Exact Dirichlet identity</text><text x="117" y="140">Established conditionally</text><text x="375" y="80">Independent estimate</text><text x="375" y="110">Rotor comparison proved</text><text x="375" y="140">Positive-margin region</text><text x="630" y="80">Uniform physical constant</text><text x="630" y="110">All cutoffs and volumes</text><text x="630" y="140">Not established for YM</text><text x="885" y="80">Construct limiting theory</text><text x="885" y="110">Pass full-domain bound</text><text x="885" y="140">Not established</text></g>
<g stroke="#435d70" stroke-width="2" marker-end="url(#arrow)"><path d="M230 100H260"/><path d="M485 100H515"/><path d="M740 100H770"/></g></svg>
<p>The required inequality is qᵣ[Ψ] ≥ δ*sᵣ‖(I−P₀,ᵣ)Ψ‖² for every physical form-domain Ψ,
with δ* &gt; 0 independent of r. The reference energy sᵣ must be fixed independently of the gap.
If physical conversion multiplies energies by cᵣ, cᵣsᵣ must approach a finite nonzero scale.</p>
<h3>Independent sufficient bound in the controlled models</h3>
<p>For a self-adjoint nonnegative T with compact resolvent, simple free vacuum and gap γ,
and bounded potential v₋I ≤ V ≤ v₊I, full-domain min–max yields λ₁(T+V) ≥ γ+v₋.
Using the free vacuum as a trial state yields λ₀(T+V) ≤ v₊. Subtraction proves:</p>
<div class="equation">Δ(T+V) ≥ γ − (v₊−v₋)<br>SU(2): Δ ≥ 3g² − 4η/g²; positive if 3g⁴ &gt; 4η<br>U(1): Δ ≥ 4g² − 4η/g²; positive if g⁴ &gt; η</div>
<p>This uses the whole physical domain, not a finite-basis Rayleigh minimum. It is analytic
and has not been Lean-formalized. It provides no positive weak-coupling certificate at fixed
η &gt; 0, and total potential oscillation can grow with volume.</p>
<p>A separate vacuum-measure comparison gives Δᵣ ≥ κᵣaᵣ/(bᵣCᵣ) when
aᵣ ≤ dνᵣ/dμᵣ ≤ bᵣ and Var<sub>μᵣ</sub>(f) ≤ Cᵣ∫|∇f|²dμᵣ.
Uniformity requires inf κᵣaᵣ/(sᵣbᵣCᵣ) &gt; 0. None of the current moments defines
these independent comparison constants.</p>
<h3>From certified spectrum to overlap and tail bounds</h3>
<p>For a normalized finite-support candidate v, compute its infinite-operator residual,
including the hopping into omitted sites. If ρ ≥ ‖(H−μ)v‖ and s &gt; 0 separates μ
from every other eigenvalue in the relevant physical sector, spectral expansion gives
sin θ ≤ ρ/s. After phase alignment, ‖u−v‖ ≤ √2 sin θ ≤ 2ρ/s; the universal cap is 2.</p>
<div class="equation">δₖ = min(2, 2ρₖ/sₖ)<br>
|⟨uₖ,Ou₀⟩−⟨vₖ,Ov₀⟩| ≤ δₖ+δ₀ for ‖O‖ ≤ 1<br>
|⟨u₀,Oᵐu₀⟩−⟨v₀,Oᵐv₀⟩| ≤ 2δ₀ for ‖Oᵐ‖ ≤ 1</div>
<p>Signed amplitude intervals give squared-weight intervals; an interval containing zero
cannot certify a nonzero overlap. Full multiplication before projection preserves moment
identities. For omitted diagonal weight Rₐ, positivity gives
Rₐ ≤ Var(Oₐ).upper − Σ retained weights.lower. With the next omitted gap bounded below by d,
the omitted diagonal correlation is at most Rₐe⁻ᵈᵗ and its cross entry has absolute value
at most √(R₀R₁)e⁻ᵈᵗ by Cauchy–Schwarz. The spectral and phase hypotheses are essential.</p>
<h2>4. Archived numerical evidence</h2><figure>{spectra}<figcaption>Archived development spectra and probe-accessible thresholds; numerical alternatives appear below.</figcaption></figure>
<p>Only the 20 pre-existing η=1 development cells are plotted. Lines guide the eye;
they do not interpolate certified bounds. Error bars use exact archived interval widths
and are generally smaller than the markers. U(1) even probes can miss the odd full-gap state.</p>
<table><tr><th>Theory</th><th>g</th><th>Full gap midpoint</th><th>Probe threshold midpoint</th><th>Qualifying common sample pairs</th></tr>{table}</table>
<p>Displayed midpoints are rounded. Exact rational endpoints, overlap certificates, covariance,
omitted-tail bounds and result-contract channel records are embedded below. A qualifying sampled
pair is not a registered target window. Numerical regressions replay existing certificates;
the full solver and analytic premises remain independently reviewable.</p>
<h3>How the combined error bound is established</h3>
<p>Let the exact connected diagonal correlation satisfy C(tᵢ) ∈ [Lᵢ,Uᵢ],
with Lᵢ &gt; 0. For any computed value cᵢ, its end-to-end error is at most
εᵢ = max(|cᵢ−Lᵢ|, |cᵢ−Uᵢ|). This bound includes all discrepancies from the
certified model at that sampled time; it does not require a separate rigorous BDF error estimate.
Changes between grids and solver tolerances are diagnostics, not the justification for εᵢ.</p>
<div class="equation">For h = tⱼ−tᵢ &gt; 0:<br>
m = log[C(tᵢ)/C(tⱼ)]/h ∈ M = [log(Lᵢ/Uⱼ)/h, log(Uᵢ/Lⱼ)/h]<br>
Computed slope m̂ ∈ O, using outward logarithm rounding<br>
ν = max over x ∈ endpoints(M), y ∈ endpoints(O) of |x−y| / d₋<br>
μ = max(0, sup M − d₋) / d₋<br>Relative total error ≤ μ + ν</div>
<p>Here [d₋,d₊] encloses the first accessible excitation Δ, with d₋ &gt; 0.
The positive spectral measure is supported at energies ≥ Δ, so C(tⱼ) ≤
exp(−Δh)C(tᵢ) and m ≥ Δ. Therefore 0 ≤ m−Δ ≤ sup M−d₋.
The triangle inequality gives |m̂−Δ|/Δ ≤ (|m̂−m|+|m−Δ|)/d₋ ≤ ν+μ.
Qualification additionally requires a certified nonzero first accessible overlap and
μ+ν ≤ 10⁻⁶. Nonpositive correlations remain unresolved. This is conservative:
interval uncertainty enters more than once, but is never subtracted away.</p>
<p>The embedded time-window evidence now retains all finest-grid sampled pairs, their
exact rational mixture/numerical/combined bounds, and the end-to-end correlation error bounds
for both theories. This proof of composition is conditional on the spectral and correlation
enclosures being valid for the declared operator and clock; it does not independently
re-prove their Sturm, residual or omitted-tail construction.</p>
<p><b>Independent composition review:</b> the separate agent found no blocking defect in
this error composition, outward slope arithmetic, or use of the U(1) even threshold.
The reviewed source hashes are embedded. It confirmed that a standalone BDF error bound
is not required for this sampled end-to-end comparison. The subsequent upstream
Sturm/Schur, eigenvector, overlap and tail analytic/code review also found no correctness
defect. These findings do not certify unsampled times or future target runs, and rely on
the documented self-adjointness, spectral and arithmetic contracts.</p>
<h3>Future execution: integration repairs and remaining work</h3>
<p>Review of the older development-only result adapter found two gaps for future deformations:
it did not attach the known free P² selection rule, and it assumed a successful final
certificate rung. Those findings do not invalidate its η=1 archives. A separate non-executing
adapter now intersects analytically forbidden weights with zero only at η=0, rejects
contradictory certificates, and retains failed/unresolved stages and partial rung evidence.
Real core-generated free certificates at calibration g=1 resolve P at level one and P²
at level two for both theories. Interacting uncertain overlaps remain unresolved.</p>
<p>JSON Schema validates stage presence, terminal statuses, object results on completion,
and nonblank failure/unresolved reasons. Six adapter tests cover the producer path,
contradictory weights, partial failures and malformed evidence. An available adapter record
means outputs and thresholds are structurally available; its precision status remains
“not assessed.” The adapter has no solver or target-run entry point. The integrated
development replay and unselected target envelope below supply the current orchestration
and request checks. Actual target execution follows a separate selected registration.</p>
<p>The separate reviewer verified the free-selection and failure-retention repairs and the
schema's rejection of malformed stage containers, result types and reasons. No outstanding
defect remains from that adapter review. Certificate contents still require independent
verification against their declared model coordinates before adaptation.</p>
<p><b>Parameterized certificate producer:</b> the reviewed exact SU(2) and corrected U(1)
engines now accept explicit η and bind theory, g, η, cutoff and exact sample times into each
record. Verification replays every derived field without invoking the eigensolver. The
verified channel entry point rejects a failed replay before using the record's coordinates.
Six tests at development calibration g=1 cover η=0, 1/2, 1; exact equality with the preserved
η=1 producers; the free P² selection path; and rejection of changed coordinates, clocks,
budget flags, parity and malformed endpoint records. This producer is a kernel, not a
registered execution envelope or authorization mechanism. Independent review verified the
malformed-record repair and coordinate-bound adapter, with no outstanding defect in that scope.</p>
<p><b>Parameterized temporal kernel:</b> a verified certificate now drives independent angle
ground preparation, direct sparse BDF propagation and per-observable sampled assessment at
each requested grid/tolerance. The exact certificate clock must equal the binary64 solver
clock; otherwise it is rejected before numerical work. Each tolerance retains its own
computed correlations, end-to-end error bound and adjacent-pair assessments. Free P² uses
its second accessible level, and U(1) retains the even/full distinction.</p>
<p>Seven temporal tests use development coordinates only. They check free and deformed
models, clock/coordinate rejection, continued work after an injected solver failure,
retention of computed correlations if assessment fails, and valid coarse-certificate
uncertainty remaining unresolved. Propagation and assessment have separate status fields.
Completed processing is not a precision verdict. The kernel does not authorize or execute
target manifests; the development envelope below adds full-run accounting, while target registration remains open.
Independent review confirmed the partial-evidence repair and unresolved-status handling,
with no outstanding defect within the temporal-kernel scope.</p>
<p><b>Parameterized scalar stage:</b> explicit g and η now drive both representation ladders:
SU(2) character/fourth-order angle and corrected U(1) Fourier/periodic angle. All requested
cutoffs and grids are retained. A failed finest rung cannot be replaced silently by a
coarser result. Final raw representations survive a comparison failure, and nonfinite
solver/comparison outputs are rejected before serialization. Ten scalar tests
cover both free models, a deformation and injected failures. Cross-representation agreement
remains diagnostic; the exact model certificate is still required for precision claims.
Independent review confirmed the comparison-failure and nonfinite-output repairs, with no
outstanding defect in the scalar comparison/failure-handling scope.</p>
<p>The scalar stage now checks diagonal and signed cross-weight sums, retained omitted
covariance, full-basis padding tails, covariance/moment consistency and spectral positivity.
Contradictions fail the stage with the original record retained. Its 10⁻⁹ consistency
tolerance is a diagnostic, not a rigorous error bound. All archived finest scalar records
pass these checks. Separately, all 40 required finest representations across the 20
development cells meet the exact scalar-accuracy budgets; their binary64 values and
rational error bounds are embedded and replayed by the standalone verifier below.</p>
<p><b>Integrated development envelope:</b> a schema-validated manifest pins the transitive
local source files and runtime schemas before any solver starts. It permits existing development
couplings only. Development runs require the recovered full ladders, fixed sample schedule
and both tolerance pairs; smaller calibration requests are explicitly distinguished.
Every requested scalar rung, certificate cutoff and propagation grid/tolerance has a terminal
record. Failures retain available evidence and allow later cells to proceed; a failed
checkpoint stops numerical work. Final source and request-accounting audits can invalidate
an otherwise qualifying result.</p>
<p>Qualification requires both scalar representations to meet exact certificate-based
error bounds (10⁻⁶ absolute for moments and relative for positive gaps), certificate budgets,
and a common qualifying adjacent sample pair for both observables at the finest grid and
last tolerance. Agreement alone cannot qualify biased scalar values. The sampling clock is
binary64-rounded τ divided by the minimum accessible-gap midpoint at the finest certificate;
it is a declared numerical sampling rule, not a physical continuum scale. Fourteen
integration tests cover the two models, positive free-model qualification, biased-value rejection,
failure retention, checkpoint failure, source drift and target rejection. This envelope
does not implement registered target execution. Independent review found no blocking
issue in the development envelope after repairs, including exact scalar accuracy and the
fixed schedule. All 42 targets remain unrun.</p>
<p>Before processing any requested cell, the envelope now replays the specified analytic
nulls and both representation calibrations. Full verdicts are retained and their source
files and referenced design are pinned. A failed check, unrejected mutant or control
exception prevents requested-cell computation and yields instrument failure with complete
request accounting. Fourteen envelope tests include false control verdicts, exceptions and
rejection of corrupted temporal evidence without losing the propagation record.
Independent review confirmed both the sum-rule and control-preflight repairs.</p>
<p><b>Offline temporal replay:</b> development qualification now uses recomputed common
sample pairs. The verifier binds the stored result to its verified certificate and exact
clock, checks every grid/tolerance slot, recomputes full correlation-error matrices and
channel-specific windows, and compares all retained assessment fields. Partial failed
assessments retain their completed arithmetic prefix; failed stages cannot qualify.
Five replay tests cover both models, changed evidence, failed propagation/assessment and
coarse unresolved certificates. Independent review found no blocking defect in this scope.
Replay checks stored arithmetic, not propagation authenticity or a standalone BDF bound.
The whole-result gate below composes this check with the remaining evidence.</p>
<p><b>Offline scalar replay:</b> development qualification also uses the recomputed
representation agreement. Every requested method and size must match, completed solver
records must satisfy their validators and spectral sum rules, final records must equal
the requested finest rungs, and stored differences and agreement must match recomputation.
Failed rungs and comparisons preserve their available records without a success verdict.
Five replay tests cover both models, altered identities and comparisons, finest failure,
and retained malformed solver evidence. Independent review found no blocking issue in this
scope. Replay does not authenticate solver execution or replace exact certificate accuracy.</p>
<p><b>Whole development-result replay:</b> the final gate checks current source pins and
complete request accounting, enforces the exact named control inventory through a schema,
replays each successful certificate and its retiming, and recomputes scalar accuracy,
adaptation, common temporal pairs, cell outcomes and the run outcome. A stored replay
verdict must also match recomputation. Failed replay yields instrument failure with raw
evidence and previous statuses retained. Seven whole-result tests cover both qualifying
models, coarse unresolved evidence, failed controls and certificates, corrupted outputs,
and malformed data. Independent review confirmed the repairs and found no qualification
bypass. This verifies stored arithmetic under current source pins; it does not authenticate
the reported solver execution, control execution or operational failures.</p>
<p><b>Execution protocol draft, still unregistered:</b> preserve the full recovered ladders,
the schedule and error budgets above, all adjacent-pair assessments and every common
qualifying pair. Do not extend a target's schedule or widen its budgets after inspecting
its output. A deformation comparison at matched theory and g subtracts certified component
intervals: [a,b] − [c,d] = [a−d,b−c]. Report each component, its uncertainty and the named
Hamiltonian change; an interval excluding zero establishes only finite-model separation.
Unresolved overlap coverage stays explicit. The machine-readable draft has no selected
targets and no execution authorization. The checked draft pins source/schema hashes,
CPython and nine computational dependency versions. Its schema freezes the protocol and
preserves all 42 target identities. A separate terminal-cell structural definition permits
partial failed evidence and rejects agreement with a failed required stage; structural
acceptance cannot establish scientific validity or grant authority. Four contract tests
check mutation rejection and preservation of partial evidence without solving target cells.
Independent review found no defect within the nonexecuting draft and structural scope.
The user's target decision is now required. Dependency versions identify the Python environment;
they do not guarantee identical native binaries or hardware behavior.
Historical cost scenarios exclude integration checkpoint overhead and do not measure
the free/deformed runtime behavior.</p>
<p><b>Target-result envelope and stopping boundary:</b> the bound, machine-readable skeleton
retains all 42 identities, empty selection and null results. Every row lists its exact
representation, certificate and grid/tolerance requests. Across the full candidate set
these total 378 scalar requests, 210 certificate cutoffs and 336 propagations; these are
plans, not completed work. Three tests reject inventory, request, precision, result and
authorization mutations. A valid draft always denies execution. Independent review found
no defect in this pre-selection scope. The historical full-set cost scenarios are about
20.85 minutes at mean measured stage cost and 38.29 minutes using per-stage observed maxima;
the explicit fourfold stress scenario is 153.16 minutes. These exclude new integration and
checkpoint overhead and are not runtime guarantees. Registration and an execution path for
the chosen subset follow the user's selection.</p>
<h2>5. Counterexample and null obligations</h2>
<p>On a fixed periodic circle, set ψβ ∝ exp[(β/2)cos(2θ)] and
Vβ = κ[β²sin²(2θ) − 2βcos(2θ)]. Then Hβψβ = 0 and Hβ = κA* A,
A = ∂θ + βsin(2θ). The positive vacuum is unique for each β.
The mean-zero physical trial function f = cos θ gives Δβ/κ ≤ Eν(sin²θ)/(1−Eν(sin²θ)).</p>
<div class="equation">β = m⁴, m ≥ 2:<br>Eν(sin²θ) ≤ Bₘ = m⁻² + 6m exp(−m²)<br>0 &lt; Δβ/κ ≤ Bₘ/(1−Bₘ) → 0</div><figure>{counter}<figcaption>Certified upper bounds for the fixed-kinetic counterexample.</figcaption></figure>
<table><tr><th>m</th><th>Upper bound on gap/κ (rounded display)</th></tr>{counter_table}</table>
<p>The fixed kinetic coefficient and vacuum equation therefore do not imply one uniform
constant. This potential is a counterexample to that inference, not to pure Yang–Mills.
Other required controls include energy offsets, accumulating eigenvalues 1/n, circle gaps
4π²κ/L², restricted trial spaces, hidden spectral states, gapless connected correlations,
nonzero-mean raw correlations and exact symmetry selection rules.</p>
<h2>6. Machine-readable content and executable checks</h2>
<p>This file is self-contained: no network scripts, fonts, plotting services or external images.
The embedded JSON includes all 20 audit records, all 42 unrun target records, full result-contract
data, finest-rung certificates, source SHA-256 hashes and explicit theorem statuses.
The digest detects internal drift; it does not independently authenticate a scientific claim.</p>
<p>Copy and run the following code next to this HTML using Python with SymPy {sp.__version__}.
It checks four symbolic identities, all 80 finest-rung infinite-operator residual bounds
in exact rational arithmetic, and exact data consistency. It does not prove the
integration-by-parts hypotheses, min–max theorem, upstream spectral endpoints or continuum limit.</p>
<pre>{escape(extraction)}</pre><details><summary>Exact CAS program</summary><pre>{escape(CAS)}</pre></details>
<details><summary>Machine-data inventory and source hashes</summary><pre>{escape(json.dumps({k:v for k,v in payload.items() if k not in ('data','cas_program')},indent=2))}</pre></details>
<script id="machine-data" type="application/octet-stream" data-sha256="{digest(raw)}">{encoded}</script>
<h2>7. Complete supporting arguments and review specification</h2>
<p>The complete source documents are embedded verbatim below as historical supporting records.
Their earlier treatment of P/LC identifiers as a general development blocker is superseded by
section 1 of this report. References to other repository
files remain provenance pointers; their contents are not silently claimed to be included.
To reproduce the full numerical audit in the pinned checkout, run
<code>OPENBLAS_NUM_THREADS=1 python3 -m unittest discover -s scripts -p 'test_vacuum*.py' -v</code>.</p>{appendix}
<footer><p>Build: scripts/vacuum_single_report.py. CAS {sp.__version__}; plotting Matplotlib {matplotlib.__version__}.
Report generation executes no target solver and allocates no registration identifiers.</p></footer></html>'''
    if selected or live:
        html=html.replace('Consolidated 2026-09-09. Exploratory finite-rotor study;', 'Updated 2026-09-10. Registered finite-rotor characterization;')
        html=html.replace('<b>202 regression tests passed</b><br>Recorded pre-selection run: 76.243 s; source hashes embedded below.', '<b>211 pre-execution tests passed</b><br>Frozen-path validation: 78.436 s; committed before target computation.')
        card='<b>42 selected cells executed</b><br>Committed registration; fixed-budget results and verification below.' if selected else '<b>'+str(counts['completed'])+' completed; '+str(counts['incomplete'])+' incomplete</b><br>'+str(counts['unattempted'])+' unattempted; registered execution remains active.'
        html=html.replace('<b>42 targets unrun</b><br>No registration or target execution authorization.',card)
        start=html.index('<h2>1. Historical pre-selection handoff</h2>')
        stop=html.index('<p><b>Independent review:</b>',start)
        html=html[:start]+'<h2>1. Scope and review</h2><p>The user selected all 42 cells after the development handoff at commit 24d42a9. Selected registration 4cbbe83, its reviewed execution path, and the results above supersede the historical unselected drafts. Those drafts remain embedded as provenance. P/LC labels are optional within quod; they add no mathematical assurance beyond the explicitly stated checks.</p>'+html[stop:]
        html=html.replace('All 42 targets remain unrun.', 'At that historical checkpoint all 42 targets remained unrun; the registered run above supersedes that status.')
        html=html.replace("The user's target decision is now required.", "That historical target decision was subsequently supplied: all 42 cells.")
        html=html.replace("Registration and an execution path for\nthe chosen subset follow the user's selection.", 'The separate selected registration and exact execution path now supersede this historical stopping boundary.')
        html=html.replace('all 42 unrun target records', 'the historical unrun target records and all 42 selected result summaries')
    OUTPUT.write_text(html)
    print(f'Wrote {OUTPUT} ({OUTPUT.stat().st_size:,} bytes)')
    return extraction


if __name__ == '__main__':
    main()
