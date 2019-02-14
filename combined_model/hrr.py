import numpy
import shelve
import os
import glob
import gc
import itertools

"Modified version of Dr. Joshua Phillips' code"
# %load hrr.py
#!/usr/bin/env python

def hrr(length,normalized=False):
    "Creates Holographic Reduced Representations"

    if normalized:
        x = numpy.random.uniform(-numpy.pi,numpy.pi,int((length-1)/2))
        if length % 2:
            x = numpy.real(numpy.fft.ifft(numpy.concatenate([numpy.ones(1),numpy.exp(1j*x),numpy.exp(-1j*x[::-1])])))
        else:
            x = numpy.real(numpy.fft.ifft(numpy.concatenate([numpy.ones(1),numpy.exp(1j*x),numpy.ones(1),numpy.exp(-1j*x[::-1])])))
    else:
        x = numpy.random.normal(0.0,1.0/numpy.sqrt(length),length)
        
    return x

def hrri(length):
    "Returns the identity vector for N-length HRRs."
    return numpy.concatenate([numpy.ones(1),numpy.zeros(length-1)])

def hrrs(length,n=1,normalized=False):
    "Creates a matrix of n HRRs, one per row."
    return numpy.row_stack([hrr(length,normalized) for x in range(n)])

def inv(x):
    "Computes the -exact- inverse of an HRR."
    x = numpy.fft.fft(x)
    return numpy.real(numpy.fft.ifft((1.0/numpy.abs(x))*numpy.exp(-1j*numpy.angle(x))))

def pinv(x):
    "Computes the pseudo-inverse of an HRR."
    return numpy.real(numpy.fft.ifft(numpy.conj(numpy.fft.fft(x))))

def convolve(x,y):
    "Computes the circular convolution of two HRRs."
    return numpy.real(numpy.fft.ifft(numpy.fft.fft(x)*numpy.fft.fft(y)))

def mconvolve(x):
    "Computes the circular convolution of a matrix of HRRs."
    return numpy.real(numpy.fft.ifft(numpy.apply_along_axis(numpy.prod,0,numpy.apply_along_axis(numpy.fft.fft,1,x))))
    
def oconvolve(x,y):
    "Computes the convolution of all pairs of HRRs in the x and y matrices."
    return numpy.row_stack([ [convolve(x[i,:],y[j,:]) for i in range(x.shape[0]) ] for j in range(y.shape[0]) ])

def correlate(x,y,invf=pinv):
    "Computes the correlation of the two provided HRRs."
    return convolve(x,invf(y))

def compose(x,y):
    "Composes two HRRs using addition in angle space. (in-progress)"
    x = numpy.fft.fft(x)
    y = numpy.fft.fft(y)
    return numpy.real(numpy.fft.ifft((x+y)/2.0))

def mcompose(x):
    "Composes a matrix of HRRs, one per row, using addition in angle space. (in-progress)"
    x = numpy.apply_along_axis(numpy.fft.fft,1,x)
    return numpy.real(numpy.fft.ifft(numpy.apply_along_axis(numpy.mean,0,x)))

def decompose(x,y):
    "Decomposes two HRRs using addition in angle space. (in-progress)"
    return compose(x,-y)

def pow(x,k):
    "Compute the convolutive power of an HRR."
    ## Original method only allowed for unitary vectors to
    ## have convolutive powers since magnitudes could not
    ## be kept in check for non-unitary vectors...
    ## return numpy.real(numpy.fft.ifft(numpy.power(numpy.fft.fft(x),k)))
    ## New version, allows for non-unitary vectors to
    ## have convolutive powers, but there is still an
    ## inversion problem since x and sqrt(x^2) are not
    ## the same vector...
    x = numpy.fft.fft(x)
    return numpy.real(numpy.fft.ifft(numpy.abs(x)*numpy.exp(1j*numpy.angle(numpy.power(x,k)))))

class LTM:
    "Long-term Memory"
    store = None
    ## Note - this is linux-specific
    tmpdir = "/dev/shm/"
    ## Might want to choose something else in the future...
    
    ## Default HRR size
    N = 1024
    normalized = False
    
    def __init__(self,name,N=1024,normalized=False):
        self.store = shelve.open(self.tmpdir + "hrr_ltm_" + name)
        self.N = N
        self.name = name
        self.normalized = normalized
        self.store[""] = hrri(self.N)
        
    def __del__(self):
        if (self.store is not None):
            self.store.close()
            
    def clean(self, total=False):
        if total:
            for f in glob.glob(self.tmpdir + "hrr_ltm_" + "*"):
                os.remove(f)
        else:
            os.remove(self.tmpdir + "hrr_ltm_" + self.name)
                
    def lookup(self,q):
        "Lookup a single symbol, encode it if necessary"
        if q in self.store:
            return self.store[q]
        else:
            self.store[q] = hrr(self.N,self.normalized)
            return self.store[q]
    
    def encode(self,q):
        "Encode an HRR"
        if not isinstance(q,str):
            return None
        name = q
        q = q.split('+')
        rep = numpy.zeros(self.N)
        for substr in q:
            subrep = hrri(self.N)
            substr = sorted(substr.split('*'))
            for subsubstr in substr:
                subrep = convolve(subrep,self.lookup(subsubstr))
            rep += subrep
        rep /= numpy.sqrt(len(q))
        self.store[name] = rep
        return rep
    
    def print(self):
        print(self)
        for key in self.store.keys():
            print(key,self.store[key])
                