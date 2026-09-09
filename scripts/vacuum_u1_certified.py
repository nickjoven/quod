"""Exact U(1) sector bounds using rational squared hoppings and bilateral residuals."""
from fractions import Fraction as F
from math import lcm

import vacuum_certified as common
import vacuum_intervals as interval


def sturm_count(diagonal, squared_hoppings, x, correction=F(0)):
    d=[F(v) for v in diagonal]
    s=[F(v) for v in squared_hoppings]
    x=F(x)
    if not d or len(s)!=len(d)-1 or any(v<0 for v in s):
        raise ValueError('matching diagonal and nonnegative squared hoppings required')
    d[-1]-=F(correction)
    if not any(s):
        return sum(v<x for v in d)
    if 0 in s:
        split=s.index(0)+1
        return sturm_count(d[:split],s[:split-1],x)+sturm_count(d[split:],s[split:],x)
    scale=lcm(x.denominator,*(v.denominator for v in d),*(v.denominator for v in s))
    ds=[int((v-x)*scale) for v in d]
    ss=[0]+[int(v*scale**2) for v in s]
    previous,current,last,count=0,1,1,0
    for v,b2 in zip(ds,ss):
        previous,current=current,v*current-b2*previous
        if current:
            sign=1 if current>0 else -1
            count+=sign!=last
            last=sign
    return count


def parameters(g,eta,cutoff,parity):
    g,eta=common.rational(g),common.rational(eta)
    if g<=0 or isinstance(cutoff,bool) or not isinstance(cutoff,int) or cutoff<4 or parity not in ('even','odd'):
        raise ValueError('positive g, cutoff >=4, and even/odd parity required')
    b=-eta/g**2
    d=[g**2*n*n for n in range(0 if parity=='even' else 1,cutoff+1)]
    squares=[b*b]*(len(d)-1)
    if parity=='even':
        squares[0]*=2
    return d,squares,b,g**2*(cutoff+1)**2-2*abs(b)


def enclosures(g,eta,cutoff,parity,count=5,bits=44):
    d,s,b,tail=parameters(g,eta,cutoff,parity)
    if not 1<=count<=len(d) or bits<1:
        raise ValueError('invalid eigenvalue count or precision')
    width=F(1,1<<bits)
    floor=-2*abs(b)
    records=[]
    for k in range(count):
        low,high=min(d)-2*abs(b)-1,max(d)+2*abs(b)+1
        while high-low>width:
            mid=(low+high)/2
            if sturm_count(d,s,mid)<=k:
                low=mid
            else:
                high=mid
        finite_low,upper=low,high
        lower=floor
        if upper<tail:
            low,high=floor-1,upper
            def below(x):
                return sturm_count(d,s,x,b*b/(tail-x))
            step=F(1)
            while below(low)>k:
                low-=step
                step*=2
            while high-low>width:
                mid=(low+high)/2
                if below(mid)<=k:
                    low=mid
                else:
                    high=mid
            lower=max(floor,low)
        records.append({'index':k,'lower':lower,'upper':upper,'finite_lower':finite_low,'tail_floor':tail})
    return records


def verify(g,eta,cutoff,parity,records):
    d,s,b,tail=parameters(g,eta,cutoff,parity)
    if not records or len(records)>len(d):
        return False
    for k,r in enumerate(records):
        low,high,finite=F(r['lower']),F(r['upper']),F(r['finite_lower'])
        if r['index']!=k or F(r['tail_floor'])!=tail or low>high or finite>high:
            return False
        if sturm_count(d,s,high)<=k or sturm_count(d,s,finite)>k:
            return False
        if low>-2*abs(b) and (low>=tail or sturm_count(d,s,low,b*b/(tail-low))>k):
            return False
    return True


def vector_bound(g,eta,vector,index,eigen):
    q=[F(float(v)) for v in vector]
    if len(q)%2!=1 or q!=q[::-1] or not 0<=index<len(eigen)-1:
        raise ValueError('exactly reflection-even bilateral vector and neighboring eigenvalue required')
    cutoff=len(q)//2
    g,eta=common.rational(g),common.rational(eta)
    b=-eta/g**2
    norm=common.dot(q,q)
    if norm==0:
        raise ValueError('zero candidate vector')
    mu=(eigen[index]['lower']+eigen[index]['upper'])/2
    separation=eigen[index+1]['lower']-mu
    if index:
        separation=min(separation,mu-eigen[index-1]['upper'])
    residual=[(g*g*(i-cutoff)**2-mu)*q[i]+(b*q[i-1] if i else 0)
              +(b*q[i+1] if i+1<len(q) else 0) for i in range(len(q))]
    residual.extend((b*q[0],b*q[-1]))
    rho=common.sqrt_interval(common.dot(residual,residual)/norm)[1]
    return {'norm_squared':norm,'rayleigh_reference':mu,'residual_norm_upper':rho,
            'separation_lower':separation,'distance_upper':min(F(2),2*rho/separation) if separation>0 else None,
            'status':'bounded' if separation>0 else 'unresolved'}


def multiply_p(q):
    out=[F(0)]*(len(q)+2)
    for i,v in enumerate(q):
        out[i]+=v/2
        out[i+2]+=v/2
    return out


def observables(vectors,bounds):
    if any(b['distance_upper'] is None for b in bounds):
        return None,None
    q=[[F(float(v)) for v in row] for row in vectors]
    p=multiply_p(q[0]);p2=multiply_p(p)
    overlaps=[]
    for k in range(1,len(q)):
        low,high=common.sqrt_interval(bounds[0]['norm_squared']*bounds[k]['norm_squared'])
        if low<=0:
            raise ValueError('normalization includes zero')
        error=bounds[0]['distance_upper']+bounds[k]['distance_upper']
        row=[]
        for applied in (p[1:-1],p2[2:-2]):
            numerator=common.dot(q[k],applied)
            endpoints=(numerator/low,numerator/high)
            a=max(F(-1),min(endpoints)-error),min(F(1),max(endpoints)+error)
            w=interval.square(a)
            row.append({'amplitude_lower':a[0],'amplitude_upper':a[1],
                        'weight_lower':w[0],'weight_upper':w[1],'nonzero_certified':w[0]>0})
        overlaps.append(row)
    applied=q[0];moments=[]
    for power in range(1,5):
        applied=multiply_p(applied)
        value=common.dot(q[0],applied[power:-power])/bounds[0]['norm_squared']
        error=2*bounds[0]['distance_upper']
        moments.append((max(F(0) if power%2==0 else F(-1),value-error),min(F(1),value+error)))
    p,p2,p3,p4=moments
    v1=interval.subtract(p2,interval.square(p));v2=interval.subtract(p4,interval.square(p2))
    cross=interval.subtract(p3,interval.multiply(p,p2))
    vacuum={'raw_moments':moments,'covariance':[[(max(F(0),v1[0]),v1[1]),cross],
                                                [cross,(max(F(0),v2[0]),v2[1])]]}
    return overlaps,vacuum


def gap_fields(even,odd):
    ground_proved=even[0]['upper']<odd[0]['lower']
    full=(min(even[1]['lower'],odd[0]['lower'])-even[0]['upper'],
          min(even[1]['upper'],odd[0]['upper'])-even[0]['lower']) if ground_proved else None
    return {'even_ground_below_odd_certified':ground_proved,'full_gap_interval':full,
            'first_even_gap_interval':(even[1]['lower']-even[0]['upper'],even[1]['upper']-even[0]['lower']),
            'full_gap_odd_certified':ground_proved and odd[0]['upper']<even[1]['lower'],
            'odd_observable_weights':'zero by exact reflection symmetry'}
