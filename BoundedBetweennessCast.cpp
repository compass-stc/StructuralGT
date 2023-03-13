#include <igraph.h>
#include <stdio.h>
#include <stdlib.h>
#include "BoundedBetweennessCast.h"
#include "Util.h"

namespace interface {

// Default constructor
BoundedBetweennessCast::BoundedBetweennessCast () {}

BoundedBetweennessCast::~BoundedBetweennessCast () {}

//Casts an igraph vector to a std::vector. The assignemnet operator may not 
//be overloaded for a class that had been defined elsewhere. Hence I am using 
//<<= instead.
/*
std::vector<float>& operator<<=(std::vector<float>& V, igraph_vector_t& I) {
    for (int i=0; i<igraph_vector_size(&I); i++) {
        V.push_back(VECTOR(I)[i]);
    }
    return V;
}
*/

void BoundedBetweennessCast::bounded_betweenness_compute () {
    igraph_t* g = (igraph_t*)this->G_ptr;
    
    num_edges = igraph_ecount(g);
    
    igraph_vector_int_t sources_vec, targets_vec;
    igraph_vector_t res, weights_vec;
    igraph_vector_init(&res, num_edges);
    igraph_vs_t sources, targets;

    printf("Size is %lu\n", sizeof(IGRAPH_PRIu));
    igraph_integer_t* sources_arr = (long long*)sources_ptr;
    igraph_integer_t* targets_arr = (long long *)targets_ptr;
    igraph_vector_int_init_array(&sources_vec, sources_arr, sources_len);
    igraph_vector_int_init_array(&targets_vec, targets_arr, targets_len);
    igraph_vs_vector(&sources, &sources_vec);
    igraph_vs_vector(&targets, &targets_vec);

    igraph_real_t* weights_arr = (double *)weights_ptr;
    igraph_vector_init_array(&weights_vec, weights_arr, num_edges);
    

    igraph_edge_betweenness_subset(g,
        &res, /*igraph_vector_t *res*/
        igraph_ess_all(IGRAPH_EDGEORDER_ID), /*igraph_es_t eids*/
        false, /*igraph_bool_t directed*/
        sources, /*igraph_vs_t sources*/
        targets, /*igraph_vs_t targets*/
        &weights_vec); /*igraph_vector_t *weights*/

    betweennesses <<= res;

    igraph_vector_int_destroy(&sources_vec);
    igraph_vector_int_destroy(&targets_vec);
    igraph_vs_destroy(&sources);
    igraph_vs_destroy(&targets);
    igraph_destroy(g);
}



}
