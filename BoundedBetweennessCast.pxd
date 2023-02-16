from libcpp.vector cimport vector

cdef extern from "BoundedBetweennessCast.cpp":
    pass

# Declare the class with cdef
cdef extern from "BoundedBetweennessCast.h" namespace "interface":
    cdef cppclass BoundedBetweennessCast:
        void* G_ptr
        long long* sources_ptr
        long long* targets_ptr
        double* weights_ptr
        int sources_len
        int targets_len
        vector[float] betweennesses
        int num_edges
        BoundedBetweennessCast() except +
        void bounded_betweenness_compute() except +
        
