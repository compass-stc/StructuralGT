# distutils: language = c++

from BoundedBetweennessCast cimport BoundedBetweennessCast
from cpython.long cimport PyLong_AsVoidPtr
import numpy as np

from libcpp.vector cimport vector

# Create a Cython extension type which holds a C++ instance
# as an attribute and create a bunch of forwarding methods
# Python extension type.
cdef class PyCast:
    cdef BoundedBetweennessCast c_cast  # Hold a C++ instance which we're wrapping
    
    def __init__(self, long long ptr):
        self.c_cast = BoundedBetweennessCast()
        self.c_cast.G_ptr = PyLong_AsVoidPtr(ptr)

    def bounded_betweenness_compute(self, long long[:] sources,
                                    long long[:] targets, int num_edges,
                                    double[:] weights):
        
        self.c_cast.sources_len = <long>len(sources)
        self.c_cast.targets_len = <long>len(targets)

        """
        cdef vector[long long] sources_vec
        cdef vector[long long] targets_vec

        for i in range(len(sources)):
            sources_vec.push_back(sources[i])
        for i in range(len(targets)):
            targets_vec.push_back(targets[i])
        self.c_cast.sources = sources_vec
        self.c_cast.targets = targets_vec
        """

        if weights is None:
            weights = np.ones(num_edges+1, dtype=np.double)

        cdef double[:] weights_memview = weights
        self.c_cast.weights_ptr = &weights_memview[0]

        
        cdef long long[:] sources_memview = sources
        cdef long long[:] targets_memview = targets
        #cdef double[:] weights_memview = weights
               
        self.c_cast.sources_ptr = &sources_memview[0]
        self.c_cast.targets_ptr = &targets_memview[0]
        self.c_cast.weights_ptr = &weights_memview[0]

        self.c_cast.bounded_betweenness_compute()

    @property
    def bounded_betweenness(self):
        _bounded_betweennesses = {}
        for i in range(self.c_cast.num_edges):
            _bounded_betweennesses[i] = self.c_cast.betweennesses[i]

        return _bounded_betweennesses

