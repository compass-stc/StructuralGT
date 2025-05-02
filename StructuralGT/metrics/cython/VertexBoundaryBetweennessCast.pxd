# Copyright (c) 2023-2024 The Regents of the University of Michigan.
# This file is from the StructuralGT project, released under the BSD 3-Clause
# License.

from libcpp.vector cimport vector


cdef extern from "VertexBoundaryBetweennessCast.cpp":
    pass

# Declare the class with cdef
cdef extern from "VertexBoundaryBetweennessCast.h" namespace "interface":
    cdef cppclass VertexBoundaryBetweennessCast:
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
        int num_vertices
        VertexBoundaryBetweennessCast() except +
        void vertex_boundary_betweenness_compute() except +
