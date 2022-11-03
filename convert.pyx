# distutils: language = c++

import numpy as np


def to_dense(float[:,:] sparse):

    #TODO change to pointer reference
    _len = sparse.shape[0]

    num = np.count_nonzero(sparse) #automatically returns int
    rows = np.zeros(num, dtype=np.uintc)
    columns = np.zeros(num, dtype=np.uintc)
    values = np.zeros(num, dtype=np.single)

    cdef unsigned int[:] rows_view = rows
    cdef unsigned int[:] columns_view = columns
    cdef float[:] values_view = values

    cdef Py_ssize_t i = 0
    for row in range(_len):
        for col in range(_len):
            element = sparse[row,col]
            if element != 0:
                rows[i] = row
                columns[i] = col
                values[i] = element
                i = i + 1

    return rows,columns,values


def to_sparse(unsigned int[:] rows, unsigned int[:] columns, float[:] values):

    _size = max(rows)+1
    _len = len(rows)
    adjacency = np.zeros((_size,_size), dtype=np.single)

    for i in range(_len):
        adjacency[rows[i],columns[i]] = values[i]

    return adjacency
