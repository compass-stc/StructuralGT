#include <stdlib.h>
#include <stdio.h>
#include <stdarg.h>

#define PY_SSIZE_T_CLEAN
#include <Python.h>
//#include "sgt_base.h"
#include "include/sgt_base.h"


static PyObject *ErrorObject;
static PyObject *
compute_anc(PyObject *self, PyObject *args)
{
    int num_cpus;
    int allow_mp;
    char *f_name;

    // Consider passing graph as String
    if (!PyArg_ParseTuple(args, "sii:compute_anc", &f_name, &num_cpus, &allow_mp)){
        return NULL;
    }

	/*if ( f_name == ''){
    	PyErr_SetString(ErrorObject, "Unable to retrieve graph.");
    	return NULL;
  	}*/

	if ( num_cpus <= 0 || allow_mp < 0){
    	PyErr_SetString(ErrorObject, "Invalid CPU parameters.");
    	return NULL;
  	}

    // Declare required variables
  	FILE *file;

  	igraph_t graph;
	igraph_integer_t num_nodes;
    igraph_integer_t count_nc = 0;
    igraph_integer_t sum_nc = 0;
    igraph_real_t anc = 0;

    // Open the file containing the serialized graph
    file = fopen(f_name, "r");
    // Read the graph from the file
    igraph_read_graph_edgelist(&graph, file, 0, IGRAPH_UNDIRECTED);
    fclose(file);
    // printf("Nodes: %d\nEdges: %d\n", (int)igraph_vcount(&graph), (int)igraph_ecount(&graph));

	num_nodes = igraph_vcount(&graph);
	if (allow_mp == 0){
        printf("Using single processing\n");
        igraph_integer_t lnc;
        for (igraph_integer_t i=0; i<num_nodes; i++) {
            for (igraph_integer_t j=i+1; j<num_nodes; j++){
                igraph_st_vertex_connectivity(&graph, &lnc, i, j, IGRAPH_VCONN_NEI_NEGATIVE);
                if (lnc == -1) { continue; }
                sum_nc += lnc;
                count_nc += 1;
            }
        }

    }
    else {
        printf("Using multiprocessing\n");
        // Initialize mutex
        pthread_mutex_t mutex;
        pthread_mutex_init(&mutex, NULL);

        // Create thread pool
        const int MAX_THREAD_COUNT = num_cpus;

        // Allocate memory for threads and args arrays
        pthread_t *threads = (pthread_t *)malloc(MAX_THREAD_COUNT * sizeof(pthread_t));
        ThreadArgsLNC *args = (ThreadArgsLNC *)malloc(MAX_THREAD_COUNT * sizeof(ThreadArgsLNC));

        if (threads == NULL || args == NULL) {
            PyErr_SetString(ErrorObject, "Memory allocation failed\n");
    	    return NULL;
        }

        // Initialize thread pool
        for (int i = 0; i < MAX_THREAD_COUNT; i++) {
            args[i].graph = &graph;
            args[i].mutex = &mutex;
            args[i].total_nc = &sum_nc;
            args[i].total_count = &count_nc;
        }

        // Create threads for computing LNC
        int idx = 0;
        int thread_count = 0;
        for (igraph_integer_t i = 0; i < num_nodes; i++) {
            for (igraph_integer_t j = i + 1; j < num_nodes; j++) {
                idx = (int)(thread_count % MAX_THREAD_COUNT);
                if (thread_count >= MAX_THREAD_COUNT) {
                    // Wait for a thread to finish before starting a new one
                    pthread_join(threads[idx], NULL);
                    thread_count++;
                }
                args[idx].i = (int)i;
                args[idx].j = (int)j;
                pthread_create(&threads[idx], NULL, compute_lnc, &args[idx]);
                thread_count++;
                // printf("thread %d running...\n", (idx));
            }
        }

        // Join threads
        for (int i = 0; i < MAX_THREAD_COUNT && i < thread_count; i++) {
            pthread_join(threads[i], NULL);
        }

        // Destroy mutex
        pthread_mutex_destroy(&mutex);
        // Free dynamically allocated memory
        free(threads);
        free(args);
    }

    // Compute ANC
    anc = (float) sum_nc / count_nc;

    // Destroy graph
    igraph_destroy(&graph);

    return PyFloat_FromDouble((double) anc);

}
static char compute_anc_doc[] =
"A C method that uses iGraph library to compute average node connectivity of a graph.\n"
"\n"
"Args:\n"
"   file (string): CSV file with edge list of graph A.\n"
"   cpus (int): number of available CPUs.\n"
"   mp (int): allow multi-processing (0: No, 1: Yes).\n"
"\n"
"Returns:\n"
"   ANC (float): Average Node Connectivity as a float value.\n";


static char sgt_doc[] =
"A C language module leveraging the iGraph library to compute Graph Theory (GT) metrics,"
"enhanced with multi-threading capabilities for accelerated computation.\n";

/* Method Table: ist of functions defined in the module */
static PyMethodDef sgt_methods[] = {
    {"compute_anc", compute_anc, METH_VARARGS, compute_anc_doc },
    //{"compute_lnc", compute_lnc, METH_VARARGS, "Compute local node connectivity." },
	{NULL, NULL, 0, NULL}        /* Sentinel */
};

/* Create module */
static struct PyModuleDef sgt_c_module = {
    PyModuleDef_HEAD_INIT,
    "sgt_c_module",   /* name of module */
    sgt_doc, /* module documentation, may be NULL */
    -1,       /* size of per-interpreter state of the module, or -1 if the module keeps state in global variables. */
    sgt_methods
};

/* Initialization function for the module */
PyMODINIT_FUNC
PyInit_sgt_c_module(void)
{
    PyObject *m;

    m = PyModule_Create(&sgt_c_module);
    if (m == NULL)
        return NULL;

    ErrorObject = PyErr_NewException("sgt_c_module.error", NULL, NULL);
    Py_XINCREF(ErrorObject);
    if (PyModule_AddObject(m, "error", ErrorObject) < 0) {
        Py_XDECREF(ErrorObject);
        Py_CLEAR(ErrorObject);
        Py_DECREF(m);
        return NULL;
    }

    return m;
}

