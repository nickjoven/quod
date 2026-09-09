"""Recovered U(1) design: H=-4g^2 d_theta^2-2 eta cos(theta)/g^2.

Reuse the independently assembled historical representations through the exact
parameter identity H_design(g,eta)=H_legacy(2g,4eta). This is an internal
parameter mapping, not a change to the external development manifest.
"""
import numpy as np
import vacuum_u1 as legacy

FOURIER_CUTOFFS = (40,80,160,320,640)
CONVENTION = 'H=-4g^2 d_theta^2-2 eta cos(theta)/g^2; Haar dtheta/(2pi); recovered design'


def parameters(g, eta, size):
    legacy.validate_inputs(g,eta,size)
    mapped=(2*g,4*eta)
    if not np.isfinite(mapped).all():
        raise ValueError('mapped parameters overflow')
    return mapped


def fourier(g, eta, cutoff):
    result=legacy.fourier(*parameters(g,eta,cutoff),cutoff)
    result['convention']=CONVENTION
    return result


def angle(g, eta, nodes):
    result=legacy.angle(*parameters(g,eta,nodes),nodes)
    result['convention']=CONVENTION
    return result


def periodic_matrix(g, eta, nodes):
    return legacy.periodic_matrix(*parameters(g,eta,nodes),nodes)


differences=legacy.differences
within_goal=legacy.within_goal


def calibration():
    g,n=.5,64
    four=fourier(g,0,40)
    periodic=angle(g,0,n)
    h=2*np.pi/n
    lam=4*np.sin(np.arange(5)*h/2)**2/h**2
    expected=4*g*g*(lam+h*h*lam*lam/12)
    checks={
        'free_fourier_even_gaps':bool(np.allclose(four['first_three_gaps'],4*g*g*np.arange(1,4)**2,rtol=0,atol=1e-12)),
        'free_full_gap':abs(four['full_gap']-4*g*g)<1e-12,
        'free_periodic_even':bool(np.allclose(periodic['even_energies'],expected[:4],rtol=0,atol=1e-9)),
        'free_periodic_odd':bool(np.allclose(periodic['odd_energies'],expected[1:5],rtol=0,atol=1e-9)),
        'haar_moments':bool(np.allclose(four['moments'],[0,.5,.5,.125,0],rtol=0,atol=1e-12)),
    }
    # Changing only the kinetic coefficient must preserve the potential matrix.
    free,_=periodic_matrix(g,0,n)
    interacting,obs=periodic_matrix(g,1,n)
    checks['potential_coefficient']=bool(np.allclose((interacting-free).diagonal(),-2/g**2*obs[:,0],rtol=0,atol=1e-12))
    inherited=legacy.calibration()
    mutants={**inherited['mutants_rejected'],
             'legacy_kinetic_coefficient':abs(legacy.fourier(g,0,40)['full_gap']-4*g*g)>1e-2}
    return {'pass':all(checks.values()) and inherited['pass'] and all(mutants.values()),
            'checks':checks,'shared_representation_calibration':inherited,'mutants_rejected':mutants,
            'scope':'recovered free model and shared representation controls; targets unrun'}
