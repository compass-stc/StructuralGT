from NonLinearRandomBetweennessCast cimport NonLinearRandomBetweennessCast
from cpython.long cimport PyLong_AsVoidPtr
import numpy as np

from libcpp.vector cimport vector

# Create a Cython extension type which holds a C++ instance
# as an attribute and create a bunch of forwarding methods
# Python extension type.
# Where an array need only be iterated over sequentially, a pointer to its
# first element should be assigned as an attribute to the c_cast object. Only
# when its elements need to be accessed in a discontinous manner should the
# attribute be set as a std::vector
cdef class PyCast:
    cdef NonLinearRandomBetweennessCast c_cast  # Hold a C++ instance which we're wrapping
    
    def __init__(self, long long ptr):
        self.c_cast = NonLinearRandomBetweennessCast()
        self.c_cast.G_ptr = PyLong_AsVoidPtr(ptr)

    def nonlinear_random_betweenness_compute(self, long[:] sources,
                                             long[:] targets, long[:] incoming,
                                             int num_edges, double[:] weights):

        self.c_cast.sources_len = <long>len(sources)
        self.c_cast.targets_len = <long>len(targets)
        
        cdef vector[int] sources_vec
        cdef vector[int] targets_vec
        cdef vector[float] incoming_vec

        for i in range(len(sources)):
            sources_vec.push_back(sources[i])
            incoming_vec.push_back(incoming[i])
        for i in range(len(targets)):
            targets_vec.push_back(targets[i])
        self.c_cast.sources = sources_vec
        self.c_cast.targets = targets_vec
        self.c_cast.incoming = incoming_vec

        if weights is None:
            weights = np.ones(num_edges+len(targets), dtype=np.double)
        else:
            mean=np.mean(weights)
            weights = np.append(weights, np.full(len(targets), mean,
                                                 dtype=np.double))

        cdef double[:] weights_memview = weights
        self.c_cast.weights_ptr = &weights_memview[0]
        self.c_cast.nonlinear_random_betweenness_compute()

        
    @property
    def nonlinear_random_betweenness(self):
        _random_betweennesses = np.zeros((self.c_cast.num_edges-self.c_cast.targets_len),
                                         dtype=np.double)
        #Return all elements of the betweenness vector, except the final
        #elements connecting the targets and to the ghost
        for i in range(self.c_cast.num_edges-self.c_cast.targets_len):
            _random_betweennesses[i] = self.c_cast.betweennesses[i]

        return _random_betweennesses

