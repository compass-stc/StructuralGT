#include <igraph.h>
#include <stdio.h>
#include <stdlib.h>
#include "Util.h"
#include <Eigen/Dense>
#include "RandomBetweennessCast.h"

#include <iostream>
namespace interface {

// Default constructor
RandomBetweennessCast::RandomBetweennessCast () {}

RandomBetweennessCast::~RandomBetweennessCast () {}


void RandomBetweennessCast::random_betweenness_compute () {
    igraph_t* g = (igraph_t*)this->G_ptr;
    
    num_edges = igraph_ecount(g);
    int num_verts = igraph_vcount(g);

    igraph_vector_t weights_vec;
    igraph_real_t* weights_arr = (double *)weights_ptr; 
    igraph_vector_init_array(&weights_vec, weights_arr, num_edges);

    //std::cout << num_verts << "\n";
    /*Prepare Laplacian as Eigen Array*/
    igraph_sparsemat_t A, compA;
    igraph_sparsemat_t L, compL;
    igraph_sparsemat_init(&L, num_verts, num_verts, num_verts*2*6);
    igraph_sparsemat_init(&A, num_verts, num_verts, num_verts*2*6);
    igraph_get_laplacian_sparse(g, &L, IGRAPH_ALL,
            IGRAPH_LAPLACIAN_UNNORMALIZED, &weights_vec);
    igraph_get_adjacency_sparse(g, &A, IGRAPH_GET_ADJACENCY_BOTH,
            &weights_vec, IGRAPH_NO_LOOPS);
    igraph_sparsemat_compress(&L, &compL);
    igraph_sparsemat_compress(&A, &compA);
    //igraph_sparsemat_print(&L, stdout);
    igraph_sparsemat_iterator_t mit;
    Eigen::MatrixXf eigL = Eigen::MatrixXf::Zero(num_verts, num_verts);

    int row, col;
    float val;
    igraph_sparsemat_iterator_init(&mit, &compL);
    for (int i=0; i<(num_edges*2+num_verts); i++) {
        
        row = igraph_sparsemat_iterator_row(&mit);
        col = igraph_sparsemat_iterator_col(&mit);
        val = igraph_sparsemat_iterator_get(&mit);

        eigL(row, col) = val;
//        if (igraph_sparsemat_iterator_end(&mit)) { break; }
//        printf("Setting %i,%i equal to %f\n", row,col,val);
        igraph_sparsemat_iterator_next(&mit);
    }
    
    //igraph_integer_t* sources_arr = (long long *)sources_ptr;
    //igraph_integer_t* targets_arr = (long long *)targets_ptr;

    /*Invert Laplacian*/
    //eigL.completeOrthogonalDecomposition().pseudoInverse();
    Eigen::MatrixXf pinv(num_verts, num_verts);
    pinv = eigL.completeOrthogonalDecomposition().pseudoInverse();

    //std::cout << pinv << "\n";

    /*Here, from/to refer to the edge endpoints; not the source/targets used
     * to calculate the betweenness subset.
     */
    betweennesses.resize(num_edges);
    igraph_integer_t from, to;
    for (int i=0; i<num_edges; i++) {
        for (int s=0; s<sources_len; s++) {
            for (int t=0; t<targets_len; t++) {
                igraph_edge(g, i, &from, &to);
                if (from>=to) { continue; }
                betweennesses[i] += abs(pinv(int(from),sources[s])-pinv(int(from),targets[t])
                    -pinv(int(to),sources[s])+pinv(int(to),targets[t]))*igraph_sparsemat_get(
                    &A, from, to);
            }
        }
    }

    /*
    for (int i=0; i<num_edges; i++) {
        std::cout << betweennesses[i] << "\n";
    }
    */

    /*
    igraph_vector_int_t sources_vec, targets_vec;
    igraph_vector_t res, weights_vec;
    igraph_vector_init(&res, num_edges);
    igraph_vs_t sources, targets;

    igraph_integer_t* sources_arr = (long long *)sources_ptr;
    igraph_integer_t* targets_arr = (long long *)targets_ptr;
    igraph_vector_int_init_array(&sources_vec, sources_arr, sources_len);
    igraph_vector_int_init_array(&targets_vec, targets_arr, targets_len);
    igraph_vs_vector(&sources, &sources_vec);
    igraph_vs_vector(&targets, &targets_vec);

    igraph_real_t* weights_arr = (double *)weights_ptr;
    igraph_vector_init_array(&weights_vec, weights_arr, num_edges);
    
    */
       
    igraph_destroy(g);
}



}
