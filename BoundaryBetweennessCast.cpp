#include <igraph.h>
#include <stdio.h>
#include <stdlib.h>
#include "BoundaryBetweennessCast.h"
#include "Util.h"

#include <chrono>

#if IGRAPH_INTEGER_SIZE==64
typedef int64_t IG_LONG;
#elif IGRAPH_INTEGER_SIZE==32
typedef int32_t IG_LONG;
#endif

namespace interface {

// Default constructor
BoundaryBetweennessCast::BoundaryBetweennessCast () {}

BoundaryBetweennessCast::~BoundaryBetweennessCast () {}

void BoundaryBetweennessCast::boundary_betweenness_compute () {
    //printf("Begin\n");
    igraph_t* g = (igraph_t*)this->G_ptr;
    
    num_edges = igraph_ecount(g);
    
    igraph_vector_int_t sources_vec, targets_vec;
    igraph_vector_t res, weights_vec;
    igraph_vector_init(&res, num_edges);
    igraph_vs_t ig_sources, ig_targets;

    igraph_integer_t* sources_arr = (IG_LONG*)sources_ptr;
    igraph_integer_t* targets_arr = (IG_LONG*)targets_ptr;
    igraph_vector_int_init_array(&sources_vec, sources_arr, sources_len);
    igraph_vector_int_init_array(&targets_vec, targets_arr, targets_len);
    igraph_vs_vector(&ig_sources, &sources_vec);
    igraph_vs_vector(&ig_targets, &targets_vec);

    igraph_real_t* weights_arr = (double *)weights_ptr;
    igraph_vector_init_array(&weights_vec, weights_arr, num_edges);
    
    //printf("Running\n");
    std::chrono::steady_clock::time_point begin = std::chrono::steady_clock::now();
    igraph_edge_betweenness_subset(g,
        &res, /*igraph_vector_t *res*/
        igraph_ess_all(IGRAPH_EDGEORDER_ID), /*igraph_es_t eids*/
        false, /*igraph_bool_t directed*/
        ig_sources, /*igraph_vs_t sources*/
        ig_targets, /*igraph_vs_t targets*/
        &weights_vec); /*igraph_vector_t *weights*/
    std::chrono::steady_clock::time_point end = std::chrono::steady_clock::now();
//    printf("Complete in %lld\n", std::chrono::duration_cast<std::chrono::microseconds>(end - begin).count());

    betweennesses <<= res;

    igraph_vector_int_destroy(&sources_vec);
    igraph_vector_int_destroy(&targets_vec);
    igraph_vs_destroy(&ig_sources);
    igraph_vs_destroy(&ig_targets);
    igraph_destroy(g);
}



}
