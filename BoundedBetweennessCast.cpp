#include <igraph.h>
#include <stdio.h>
#include <stdlib.h>
#include "BoundedBetweennessCast.h"
#include "Util.h"

#if IGRAPH_INTEGER_SIZE==64
typedef long IG_LONG;
#elif IGRAPH_INTEGER_SIZE==32
typedef long IG_LONG;
#endif

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
    igraph_vs_t ig_sources, ig_targets;

    printf("Size is %i\n", IGRAPH_INTEGER_SIZE);


    /*
    igraph_integer_t* sources_std_vec;
    igraph_integer_t* targets_std_vec;
    //long long* sources_std_vec;
    //long long* targets_std_vec;
    std::vector<long> sources_copy; 
    std::vector<long> targets_copy; 
    if (sizeof(IGRAPH_PRIu)==3) {
        sources_copy.resize(sources_len);
        targets_copy.resize(targets_len);
        sources_std_vec = (IG_LONG *)sources_copy.data();
        targets_std_vec = (IG_LONG *)targets_copy.data();
    } else if (sizeof(IGRAPH_PRIu)==8) {
        sources_std_vec = (IG_LONG *)sources_ptr;
        targets_std_vec = (IG_LONG *)targets_ptr;
    }
    igraph_integer_t* sources_arr = &sources_std_vec[0];
    igraph_integer_t* targets_arr = &targets_std_vec[0];
    */


    igraph_integer_t* sources_arr = (IG_LONG*)sources_ptr;
    igraph_integer_t* targets_arr = (IG_LONG*)targets_ptr;
    igraph_vector_int_init_array(&sources_vec, sources_arr, sources_len);
    igraph_vector_int_init_array(&targets_vec, targets_arr, targets_len);
    igraph_vs_vector(&ig_sources, &sources_vec);
    igraph_vs_vector(&ig_targets, &targets_vec);

    igraph_real_t* weights_arr = (double *)weights_ptr;
    igraph_vector_init_array(&weights_vec, weights_arr, num_edges);
    

    igraph_edge_betweenness_subset(g,
        &res, /*igraph_vector_t *res*/
        igraph_ess_all(IGRAPH_EDGEORDER_ID), /*igraph_es_t eids*/
        false, /*igraph_bool_t directed*/
        ig_sources, /*igraph_vs_t sources*/
        ig_targets, /*igraph_vs_t targets*/
        &weights_vec); /*igraph_vector_t *weights*/

    betweennesses <<= res;

    igraph_vector_int_destroy(&sources_vec);
    igraph_vector_int_destroy(&targets_vec);
    igraph_vs_destroy(&ig_sources);
    igraph_vs_destroy(&ig_targets);
    igraph_destroy(g);
}



}
