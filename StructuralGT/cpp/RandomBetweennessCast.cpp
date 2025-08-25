// Copyright (c) 2023-2024 The Regents of the University of Michigan.
// This file is from the StructuralGT project, released under the BSD 3-Clause
// License.

#include "RandomBetweennessCast.h"
#include "Util.h"
#include <Eigen/Dense>
#include <igraph.h>
#include <stdio.h>
#include <stdlib.h>

#include <iostream>
namespace interface {

// Default constructor
RandomBetweennessCast::RandomBetweennessCast() {}

RandomBetweennessCast::~RandomBetweennessCast() {}

void RandomBetweennessCast::random_betweenness_compute() {
  igraph_t *g = (igraph_t *)this->G_ptr;

  num_edges = igraph_ecount(g);
  int num_verts = igraph_vcount(g);

  igraph_vector_t weights_vec;
  igraph_real_t *weights_arr = (double *)weights_ptr;
  igraph_vector_init_array(&weights_vec, weights_arr, num_edges);

  /*Prepare Laplacian as Eigen Array*/
  igraph_sparsemat_t A, compA;
  igraph_sparsemat_t L, compL;
  igraph_sparsemat_init(&L, num_verts, num_verts, num_verts * 2 * 6);
  igraph_sparsemat_init(&A, num_verts, num_verts, num_verts * 2 * 6);
  igraph_get_laplacian_sparse(g, &L, IGRAPH_ALL, IGRAPH_LAPLACIAN_UNNORMALIZED,
                              &weights_vec);
  igraph_get_adjacency_sparse(g, &A, IGRAPH_GET_ADJACENCY_BOTH, &weights_vec,
                              IGRAPH_NO_LOOPS);
  igraph_sparsemat_compress(&L, &compL);
  igraph_sparsemat_compress(&A, &compA);
  igraph_sparsemat_iterator_t mit;
  Eigen::MatrixXf L_reduced =
      Eigen::MatrixXf::Zero(num_verts - 1, num_verts - 1);

  int row, col;
  float val;
  igraph_sparsemat_iterator_init(&mit, &compL);
  for (int i = 0; i < (num_edges * 2 + num_verts); i++) {
    row = igraph_sparsemat_iterator_row(&mit);
    col = igraph_sparsemat_iterator_col(&mit);
    if ((row == 0) || (col == 0)) {
      igraph_sparsemat_iterator_next(&mit);
      continue;
    }

    val = igraph_sparsemat_iterator_get(&mit);

    L_reduced(row - 1, col - 1) = val;
    igraph_sparsemat_iterator_next(&mit);
  }

  /*Invert Laplacian*/
  Eigen::MatrixXf L_red_inv(num_verts - 1, num_verts - 1);
  L_red_inv = L_reduced.inverse();

  /*Get matrix C*/
  Eigen::MatrixXf C(num_verts, num_verts);
  // Set the first column and row to zeros
  C.col(0).setZero();
  C.row(0).setZero();
  C.block(1, 1, num_verts - 1, num_verts - 1) = L_red_inv;

  /*Get incidence matrix, B*/
  igraph_integer_t from, to;
  Eigen::MatrixXf B = Eigen::MatrixXf::Zero(num_edges, num_verts);
  for (int i = 0; i < num_edges; i++) {
    igraph_edge(g, i, &from, &to);
    B(i, from) = float(VECTOR(weights_vec)[i]);
    B(i, to) = float(-VECTOR(weights_vec)[i]);
  }

  /*Get flow matrix, F*/
  Eigen::MatrixXf F(num_edges, num_verts);
  F = B * C;

  Eigen::VectorXf b = Eigen::VectorXf::Zero(num_verts);
  Eigen::VectorXf RW = Eigen::VectorXf::Zero(num_edges);
  for (int u = 0; u < num_verts; u++) {
    for (int v = u + 1; v < num_verts; v++) {
      b[u] = 1;
      b[v] = -1;
      RW += (F * b).cwiseAbs();
      b[u] = 0;
      b[v] = 0;
    }
  }
  betweennesses <<= RW;
  igraph_destroy(g);
}
} // namespace interface
