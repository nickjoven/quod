"""Exact parity certificates for H=-4g^2 d_theta^2-2 eta cos(theta)/g^2.

Map declared decimal coordinates to exact Fractions BEFORE scaling. The
shared Schur/Sturm/residual engine then sees precisely the recovered operator.
"""
import vacuum_u1_certified as legacy
from vacuum_certified import rational


def mapped(g, eta):
    return 2*rational(g),4*rational(eta)


def parameters(g, eta, cutoff, parity):
    return legacy.parameters(*mapped(g,eta),cutoff,parity)


def enclosures(g, eta, cutoff, parity, count=5, bits=44):
    return legacy.enclosures(*mapped(g,eta),cutoff,parity,count=count,bits=bits)


def verify(g, eta, cutoff, parity, records):
    return legacy.verify(*mapped(g,eta),cutoff,parity,records)


def vector_bound(g, eta, vector, index, eigen):
    return legacy.vector_bound(*mapped(g,eta),vector,index,eigen)


observables=legacy.observables
gap_fields=legacy.gap_fields
