from libcpp.vector cimport vector

cdef extern from "NonLinearRandomBetweennessCast.cpp":
    pass

# Declare the class with cdef
cdef extern from "NonLinearRandomBetweennessCast.h" namespace "interface":
    cdef cppclass NonLinearRandomBetweennessCast:
        void* G_ptr
        double* weights_ptr
        vector[int] sources
        vector[int] targets
        vector[float] incoming
        int sources_len
        int targets_len
        vector[float] betweennesses
        int num_edges
        NonLinearRandomBetweennessCast() except +
        void nonlinear_random_betweenness_compute() except +
        
