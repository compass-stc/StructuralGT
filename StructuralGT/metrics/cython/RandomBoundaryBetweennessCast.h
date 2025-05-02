// Copyright (c) 2023-2024 The Regents of the University of Michigan.
// This file is from the StructuralGT project, released under the BSD 3-Clause
// License.

#include <vector>

#ifndef RANDOMBOUNDARYBETWEENNESSCAST_H
#define RANDOMBOUNDARYBETWEENNESSCAST_H

namespace interface {
class RandomBoundaryBetweennessCast {
public:
  void *G_ptr;
  double *weights_ptr;
  std::vector<int> sources;
  std::vector<int> targets;
  std::vector<float> incoming;
  int sources_len;
  int targets_len;
  RandomBoundaryBetweennessCast();
  ~RandomBoundaryBetweennessCast();
  void random_boundary_betweenness_compute();
  int num_edges;
  std::vector<float> linear_betweennesses;
  std::vector<float> nonlinear_betweennesses;
};
} // namespace interface

#endif
