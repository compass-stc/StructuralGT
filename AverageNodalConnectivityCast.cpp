#include <igraph.h>
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
    printf("Completed\n"); 
    int num_verts = igraph_vcount(g);
    igraph_integer_t nc;
    float total_connectivity = 0;
    for (igraph_integer_t i=0; i<num_verts; i++) {
        for (igraph_integer_t j=i+1; j<num_verts; j++) {
            igraph_st_vertex_connectivity(g, &nc, i, j, (igraph_vconn_nei_t)IGRAPH_VCONN_NEI_NEGATIVE);
            total_connectivity += nc;
        }
    } 
    printf("Completed\n");
    
    anc = 2 * total_connectivity / float(num_verts) / (float(num_verts)-1);
       
    igraph_destroy(g);
}



}