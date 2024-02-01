#include <igraph/igraph.h>
#include <stdio.h>
#include <stdlib.h>
#include "Util.h"
#include "AverageNodalConnectivityCast.h"

#include <iostream>
namespace interface {

// Default constructor
AverageNodalConnectivityCast::AverageNodalConnectivityCast () {}

AverageNodalConnectivityCast::~AverageNodalConnectivityCast () {}


void AverageNodalConnectivityCast::average_nodal_connectivity_compute () {
    igraph_t* g = (igraph_t*)this->G_ptr;
    int num_verts = igraph_vcount(g);
    int den = 0;
    igraph_integer_t nc;
    float total_connectivity = 0;
    for (igraph_integer_t i=0; i<num_verts; i++) {
        for (igraph_integer_t j=i+1; j<num_verts; j++) {
            igraph_st_vertex_connectivity(g, &nc, i, j, (igraph_vconn_nei_t)IGRAPH_VCONN_NEI_NEGATIVE);
            if (nc == -1) { continue; }
            total_connectivity += nc;
            den++;
        }
    } 
    anc = total_connectivity / float(den);
    igraph_destroy(g);
}



}
