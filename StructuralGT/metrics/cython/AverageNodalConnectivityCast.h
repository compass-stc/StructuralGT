// Copyright (c) 2023-2024 The Regents of the University of Michigan.
// This file is from the StructuralGT project, released under the BSD 3-Clause
// License.

#include <vector>

#ifndef AVERAGENODALCONNECTIVITYCAST_H
#define AVERAGENODALCONNECTIVITYCAST_H
namespace interface {
class AverageNodalConnectivityCast {
public:
  void *G_ptr;
  AverageNodalConnectivityCast();
  ~AverageNodalConnectivityCast();
  void average_nodal_connectivity_compute();
  float anc;
};
} // namespace interface

#endif
