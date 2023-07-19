#include <igraph.h>
#include <stdio.h>
#include <stdlib.h>
#include "Util.h"
#include <Eigen/Dense>
#include "NonLinearRandomBetweennessCast.h"

#include <iostream>
namespace interface {

// Default constructor
NonLinearRandomBetweennessCast::NonLinearRandomBetweennessCast () {}

NonLinearRandomBetweennessCast::~NonLinearRandomBetweennessCast () {}


void NonLinearRandomBetweennessCast::nonlinear_random_betweenness_compute () {
    igraph_t* g = (igraph_t*)this->G_ptr;
    int num_verts = igraph_vcount(g);
    num_edges = igraph_ecount(g);

    igraph_vector_t weights_vec;
    igraph_real_t* weights_arr = (double *)weights_ptr; 
    igraph_vector_init_array(&weights_vec, weights_arr, num_edges);

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
        igraph_sparsemat_iterator_next(&mit);
    }
    
    /*Invert Laplacian*/
    Eigen::MatrixXf pinv(num_verts, num_verts);
    pinv = eigL.completeOrthogonalDecomposition().pseudoInverse();

    //std::cout << pinv << "\n";
    
    /*Generate voltage vector*/
    /*(Faster than matrix vector multiplication because we know the
     * location of non-zero elements a priori)
     * Note that, for nonlinear random betweenness, the target vertex has
     * changed to the ghost vertex*/
    std::vector<float> V(num_verts, 0);
    float sum = 0;
    for (int i=0; i<num_verts; i++) {
        for (int s=0; s<sources_len; s++) {
            V[i] += pinv(i, sources[s])*incoming[s];
            sum += incoming[s];
        }
            V[i] -= pinv(i, num_verts-1)*sum;
    }
    /*Here, from/to refer to the edge endpoints; not the source/targets used
     * to calculate the betweenness subset.
     */
    betweennesses.resize(num_edges);
    igraph_integer_t from, to;
    bool skip = false;
    for (int i=0; i<num_edges; i++) {
        igraph_edge(g, i, &from, &to);
        /*Skip edges connecting sources*/
        for (int s1=0; s1<sources_len; s1++) {
            for (int s2=0; s2<sources_len; s2++) {
                //printf("%i,%i,%i,%i\n",s1,s2,int(from),int(to));
                if (((int(from)==sources[s1] and int(to)==sources[s2]) 
                 or (int(from)==sources[s2] and int(to)==sources[s1]))
                        and !skip) {
                    skip=true;
                    break;
                }
            }
        } 
        /*Skip edges connecting targets*/
        for (int t1=0; t1<targets_len; t1++) {
            for (int t2=0; t2<targets_len; t2++) {
                //printf("%i,%i,%i,%i\n",s1,s2,int(from),int(to));
                if (((int(from) == targets[t1] && int(to) == targets[t2]) ||
                    (int(from) == targets[t2] && int(to) == targets[t1])) &&
                    !skip) {
                    skip = true;
                    break;
                }
            }
        } 
        /*Reset the skip flag*/
        if (skip) { 
            skip = false;
            continue; 
        }
        /*So if edge neither connects two sources nor two targets, do this...*/
        betweennesses[i] = abs(V[int(from)] - V[int(to)])*igraph_sparsemat_get(
                    &A, from, to);
    }
    igraph_destroy(g);
}



}
