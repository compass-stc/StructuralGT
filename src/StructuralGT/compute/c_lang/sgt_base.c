//#define _POSIX_C_SOURCE 200809L  // Linux
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
//#include "sgt_base.h"
#include "include/sgt_base.h"

// Function to compute Local Node Connectivity
void* compute_lnc(void *arg) {
    ThreadArgsLNC *args = (ThreadArgsLNC*)arg;
    igraph_integer_t lnc;

    igraph_st_vertex_connectivity(args->graph, &lnc, args->i, args->j, IGRAPH_VCONN_NEI_NEGATIVE);

    // Update shared data under mutex lock
    pthread_mutex_lock(args->mutex);
    if (lnc != -1){
        *(args->total_nc) += lnc;
        *(args->total_count) += 1;
        //printf("got %d\n", lnc);
        //printf("NC:%d Count:%d \n", *(args->total_nc), *(args->total_count));
    }
    pthread_mutex_unlock(args->mutex);
    
    pthread_exit(NULL);
}

// Function to convert string representation of adjacency matrix to 2D matrix
igraph_matrix_t* str_to_matrix(char* str_adj_mat, igraph_integer_t num_vertices) {
    // Allocate memory for the matrix
    igraph_matrix_t* mat = (igraph_matrix_t*)malloc(sizeof(igraph_matrix_t));
    if (!mat) {
        fprintf(stderr, "Failed to allocate memory for matrix structure\n");
        exit(EXIT_FAILURE);
    }
    igraph_matrix_init(mat, num_vertices, num_vertices);

    // Parse string and populate matrix
    char* token;
    char* nextToken;
    const char delimiters[] = ",";

    // Get the first token
    // strtok_r - MacOs
    //token = strtok_r(str_adj_mat, delimiters, &nextToken);
    token = strtok_s(str_adj_mat, delimiters, &nextToken);

    // Iterate through the remaining tokens
    for (igraph_integer_t i = 0; i < num_vertices; i++) {
        for (igraph_integer_t j = 0; j < num_vertices; j++) {
            MATRIX(*mat, i, j) = atoi(token);
            // Get the next token
            // strtok_r - MacOs
            //token = strtok_r(NULL, delimiters, &nextToken);
            token = strtok_s(NULL, delimiters, &nextToken);
        }
    }

    return mat;
}

