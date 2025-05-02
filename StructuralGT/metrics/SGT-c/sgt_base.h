#ifndef THREAD_ARGS_H
#define THREAD_ARGS_H

#include <igraph.h>
#include <pthread.h>

// Structure to hold thread arguments
typedef struct {
    igraph_t *graph;
    igraph_integer_t i;
    igraph_integer_t j;
    igraph_integer_t *total_nc;      // Pointer to store the result
    igraph_integer_t *total_count;
    pthread_mutex_t *mutex;          // Pointer to mutex
} ThreadArgsLNC;

#endif /* THREAD_ARGS_H */

void* compute_lnc(void *arg);
igraph_matrix_t* str_to_matrix(char* str_adj_mat, igraph_integer_t num_vertices);

