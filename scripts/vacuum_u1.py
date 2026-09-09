"""U(1) development convention: H=-g^2 d_theta^2-2 eta cos(theta)/g^2.

Fourier and periodic fourth-order angle representations keep both parities.
The convention is explicit but not yet verified against the missing pilot.
"""
import numpy as np
from scipy.linalg import eigh_tridiagonal
from scipy.sparse import coo_matrix, diags
from scipy.sparse.linalg import eigsh

from vacuum_development import observable_data


def validate_inputs(g, eta, size):
    if not np.isfinite(g) or g <= 0 or not np.isfinite(eta):
        raise ValueError('positive finite g and finite eta required')
    if isinstance(size, bool) or not isinstance(size, (int, np.integer)) or size < 4:
        raise ValueError('integer size >=4 required')


def parity_fields(record, even, odd):
    record.update(even_energies=even.tolist(), odd_energies=odd.tolist(),
                  full_gap=float(min(even[1], odd[0])-even[0]),
                  first_even_gap=float(even[1]-even[0]),
                  first_odd_gap=float(odd[0]-even[0]),
                  odd_observable_weights='exactly zero by reflection parity for P and P^2',
                  numerical_lowest_excited_parity='odd' if odd[0] < even[1] else 'even_or_degenerate',
                  threshold_status='unresolved: even overlaps and numerical error budget required')
    return record


def fourier(g, eta, cutoff):
    validate_inputs(g, eta, cutoff)
    b = -eta/g**2
    even_d = g**2*np.arange(cutoff+1, dtype=float)**2
    even_off = np.full(cutoff, b)
    even_off[0] *= np.sqrt(2)
    even, ve = eigh_tridiagonal(even_d, even_off)
    odd, _ = eigh_tridiagonal(g**2*np.arange(1,cutoff+1,dtype=float)**2, np.full(cutoff-1,b),
                             select='i',select_range=(0,3))
    # Embed the cosine coefficients in the bilateral Fourier basis n=-K,...,K.
    vectors = np.empty((2*cutoff+1, cutoff+1))
    vectors[cutoff] = ve[0]
    vectors[cutoff+1:] = ve[1:]/np.sqrt(2)
    vectors[:cutoff] = vectors[cutoff+1:][::-1]
    if vectors[cutoff,0] < 0:
        vectors[:,0] *= -1
    ground = vectors[:,0]

    def multiply_p(v):
        out = np.zeros(len(v)+2)
        out[:-2] += v/2
        out[2:] += v/2
        return out

    p = multiply_p(ground)
    p2 = multiply_p(p)
    padded = np.column_stack((np.pad(p,(1,1)),p2))
    applied = padded[2:-2]
    record = observable_data(even, vectors, applied, padded.T@padded)
    n = np.arange(-cutoff,cutoff+1)
    hv = g**2*n[:,None]**2*vectors[:,:4]
    hv[1:] += b*vectors[:-1,:4]
    hv[:-1] += b*vectors[1:,:4]
    tail = np.vstack((padded[:2],padded[-2:]))
    record.update(method='u1_fourier_even_odd', cutoff=cutoff,
                  solver_residual_first_four=np.linalg.norm(hv-vectors[:,:4]*even[:4],axis=0).tolist(),
                  outside_basis_residual_first_four=(np.sqrt(2)*abs(b*vectors[-1,:4])).tolist(),
                  observable_projection_tail_gram=(tail.T@tail).tolist(),
                  even_parity_defect=float(np.max(abs(vectors-vectors[::-1]))))
    return parity_fields(record,even,odd)


def differences(a,b):
    return {'moment_absolute': abs(np.asarray(a['moments'])-b['moments']).tolist(),
            'even_gap_relative': (abs(np.asarray(a['first_three_gaps'])-b['first_three_gaps'])/np.asarray(b['first_three_gaps'])).tolist(),
            'full_gap_relative': abs(a['full_gap']-b['full_gap'])/b['full_gap']}


def within_goal(diff):
    values = np.asarray([*diff['moment_absolute'],*diff['even_gap_relative'],diff['full_gap_relative']])
    return bool(values.shape == (9,) and np.isfinite(values).all() and (values>=0).all() and (values<=1e-6).all())


def calibration():
    n,g = 64,.5
    free = angle(g,0,n)
    four = fourier(g,0,20)
    h = 2*np.pi/n
    lam = 4*np.sin(np.arange(5)*h/2)**2/h**2
    discrete = g**2*(lam+h*h*lam*lam/12)
    matrix,obs = periodic_matrix(g,0,n)
    ground = np.full(n,1/np.sqrt(n))
    broken = matrix.tolil()
    for i,j in ((0,n-1),(0,n-2),(1,n-1)):
        broken[i,j]=broken[j,i]=0
    weak = fourier(.1,1,4)
    q = np.asarray(weak['ground'])
    projected_p = (np.diag(np.full(len(q)-1,.5),1)+np.diag(np.full(len(q)-1,.5),-1))
    wrong_square = float(q@projected_p@projected_p@q)
    x = np.arange(n)*h
    wrong_haar = float(np.sin(x)**2@obs[:,1]/np.sum(np.sin(x)**2))
    checks = {
        'free_fourier_moments': bool(np.max(abs(np.array(four['moments'])-[0,.5,.5,.125,0]))<1e-12),
        'free_periodic_dispersion_even': bool(np.max(abs(np.array(free['even_energies'])-discrete[:4]))<1e-9),
        'free_periodic_dispersion_odd': bool(np.max(abs(np.array(free['odd_energies'])-discrete[1:5]))<1e-9),
        'free_periodic_haar': bool(np.max(abs(np.array(free['moments'])-[0,.5,.5,.125,0]))<1e-9),
        'periodic_constant_ground': bool(np.linalg.norm(matrix@ground)<1e-9),
        'odd_selection_rule': bool(np.max(abs(np.asarray(free['odd_overlap_numerical'])))<1e-12),
        'projection_tail_accounting': bool(np.max(abs(np.array(weak['unrepresented_covariance'])-weak['observable_projection_tail_gram']))<1e-12),
    }
    mutants = {'wrong_haar': abs(wrong_haar-.5)>1e-2,
               'missing_periodic_wrap': bool(np.linalg.norm(broken@ground)>1e-2),
               'project_square_before_multiplication': abs(wrong_square-weak['moments'][1])>1e-4,
               'odd_full_gap_used_for_even_probe': abs(weak['full_gap']-weak['first_even_gap'])>1e-2}
    return {'checks':checks,'mutants_rejected':mutants,'pass':all(checks.values()) and all(mutants.values()),
            'scope':'free analytic and inadequate-cutoff controls; no target cells'}


def periodic_matrix(g, eta, nodes):
    validate_inputs(g, eta, nodes)
    if nodes < 12 or nodes % 2:
        raise ValueError('even periodic grid with at least 12 nodes required')
    h = 2*np.pi/nodes
    indices = np.arange(nodes)
    rows = np.repeat(indices,3)
    columns = np.column_stack((indices,(indices-1)%nodes,(indices+1)%nodes)).ravel()
    values = np.tile([2.,-1.,-1.],nodes)/h**2
    laplace = coo_matrix((values,(rows,columns)),shape=(nodes,nodes)).tocsc()
    matrix = g**2*(laplace+h**2/12*(laplace@laplace))
    x = indices*h
    matrix -= diags(2*eta/g**2*np.cos(x))
    return matrix.tocsc(), np.column_stack((np.cos(x),np.cos(x)**2))


def parity_embeddings(nodes):
    """Orthonormal reflection-even/odd embeddings, including both fixed points."""
    half = nodes//2
    interior = np.arange(1,half)
    rows = np.concatenate(([0,half],interior,nodes-interior))
    cols = np.concatenate(([0,half],interior,interior))
    values = np.concatenate(([1.,1.],np.full(2*(half-1),1/np.sqrt(2))))
    even = coo_matrix((values,(rows,cols)),shape=(nodes,half+1)).tocsc()
    rows = np.concatenate((interior,nodes-interior))
    cols = np.tile(np.arange(half-1),2)
    values = np.concatenate((np.full(half-1,1/np.sqrt(2)),np.full(half-1,-1/np.sqrt(2))))
    odd = coo_matrix((values,(rows,cols)),shape=(nodes,half-1)).tocsc()
    return even,odd


def angle(g, eta, nodes):
    matrix, observables = periodic_matrix(g,eta,nodes)
    qe,qo = parity_embeddings(nodes)
    # sigma lies below the continuum and finite kinetic+potential lower bound.
    sigma = -2*abs(eta)/g**2-1

    def low(embedding):
        reduced = (embedding.T@matrix@embedding).tocsc()
        values,vectors = eigsh(reduced,k=4,sigma=sigma,which='LM',tol=1e-12,
                              v0=np.linspace(1.,2.,reduced.shape[0]),maxiter=20*reduced.shape[0])
        order = np.argsort(values)
        return values[order], np.asarray(embedding@vectors[:,order])

    even,vectors = low(qe)
    odd,odd_vectors = low(qo)
    if vectors[np.argmax(abs(vectors[:,0])),0] < 0:
        vectors[:,0] *= -1
    applied = vectors[:,:1]*observables
    record = observable_data(even,vectors,applied,applied.T@applied)
    reflection = (-np.arange(nodes))%nodes
    record.update(method='u1_periodic_fourth_order',nodes=nodes,spacing=float(2*np.pi/nodes),
                  solver_residual_first_four=np.linalg.norm(matrix@vectors-vectors*even,axis=0).tolist(),
                  odd_solver_residual_first_four=np.linalg.norm(matrix@odd_vectors-odd_vectors*odd,axis=0).tolist(),
                  even_parity_defect=float(np.max(abs(vectors-vectors[reflection]))),
                  odd_parity_defect=float(np.max(abs(odd_vectors+odd_vectors[reflection]))),
                  odd_overlap_numerical=(odd_vectors.T@applied).tolist(),
                  quadrature_error_bound=None,mesh_error_bound=None)
    return parity_fields(record,even,odd)
