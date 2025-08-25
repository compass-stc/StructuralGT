from StructuralGT.cpp.AverageNodalConnectivityCast cimport AverageNodalConnectivityCast
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
    cdef AverageNodalConnectivityCast c_cast  # Hold a C++ instance which we're wrapping

    def __init__(self, long long ptr):
        self.c_cast = AverageNodalConnectivityCast()
        self.c_cast.G_ptr = PyLong_AsVoidPtr(ptr)

    def average_nodal_connectivity_compute(self):
        self.c_cast.average_nodal_connectivity_compute()

    @property
    def average_nodal_connectivity(self):
        return self.c_cast.anc
