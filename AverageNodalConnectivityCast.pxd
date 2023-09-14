from libcpp.vector cimport vector

cdef extern from "AverageNodalConnectivityCast.cpp":
    pass

# Declare the class with cdef
cdef extern from "AverageNodalConnectivityCast.h" namespace "interface":
    cdef cppclass AverageNodalConnectivityCast:
        void* G_ptr
        float anc
        AverageNodalConnectivityCast() except +
        void average_nodal_connectivity_compute() except +
        
