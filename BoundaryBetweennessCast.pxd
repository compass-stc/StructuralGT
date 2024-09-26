from libcpp.vector cimport vector

cdef extern from "BoundaryBetweennessCast.cpp":
    pass

# Declare the class with cdef
cdef extern from "BoundaryBetweennessCast.h" namespace "interface":
    cdef cppclass BoundaryBetweennessCast:
        void* G_ptr
        long long* sources_ptr
        long long* targets_ptr
        #vector[long long] sources
        #vector[long long] targets
        double* weights_ptr
        int sources_len
        int targets_len
        vector[float] betweennesses
        int num_edges
        BoundaryBetweennessCast() except +
        void boundary_betweenness_compute() except +
        
