from libcpp.vector cimport vector

cdef extern from "RandomBetweennessCast.cpp":
    pass

# Declare the class with cdef
cdef extern from "RandomBetweennessCast.h" namespace "interface":
    cdef cppclass RandomBetweennessCast:
        void* G_ptr
        double* weights_ptr
        vector[int] sources
        vector[int] targets
        int sources_len
        int targets_len
        vector[float] betweennesses
        int num_edges
        RandomBetweennessCast() except +
        void random_betweenness_compute() except +
        