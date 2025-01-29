// Copyright (c) 2023-2024 The Regents of the University of Michigan.
// This file is from the StructuralGT project, released under the BSD 3-Clause
// License.

//
// This file is from the StructuralGT project, released under the BSD 3-Clause
// License.

//
// This file is from the StructuralGT project, released under the BSD 3-Clause
// License.

//
// This file is from the StructuralGT project, released under the BSD 3-Clause
// License.

//
// This file is from the StructuralGT project, released under the BSD 3-Clause
// License.

//
// This file is from the StructuralGT project, released under the BSD 3-Clause
// License.

//
// This file is from the StructuralGT project, released under the BSD 3-Clause
// License.

//
// This file is from the StructuralGT project, released under the BSD 3-Clause
// License.

//
// This file is from the StructuralGT project, released under the BSD 3-Clause
// License.

//
// This file is from the StructuralGT project, released under the BSD 3-Clause
// License.

//
// This file is from the StructuralGT project, released under the BSD 3-Clause
// License.

//
// This file is from the StructuralGT project, released under the BSD 3-Clause
// License.

#include <vector>

#ifndef RANDOMBETWEENNESSCAST_H
#define RANDOMBETWEENNESSCAST_H

namespace interface {
class RandomBetweennessCast {
public:
  void *G_ptr;
  double *weights_ptr;
  std::vector<int> sources;
  std::vector<int> targets;
  int sources_len;
  int targets_len;
  RandomBetweennessCast();
  ~RandomBetweennessCast();
  void random_betweenness_compute();
  int num_edges;
  std::vector<float> betweennesses;
};
} // namespace interface

#endif
