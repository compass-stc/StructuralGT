from libcpp.vector cimport vector

cdef extern from "RandomBoundaryBetweennessCast.cpp":
    pass

# Declare the class with cdef
cdef extern from "RandomBoundaryBetweennessCast.h" namespace "interface":
    cdef cppclass RandomBoundaryBetweennessCast:
        void* G_ptr
        double* weights_ptr
        vector[int] sources
        vector[int] targets
        vector[float] incoming
        int sources_len
        int targets_len
        vector[float] linear_betweennesses
        vector[float] nonlinear_betweennesses
        int num_edges
        RandomBoundaryBetweennessCast() except +
        void random_boundary_betweenness_compute() except +
        
