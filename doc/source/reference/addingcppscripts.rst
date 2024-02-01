==================
Adding C++ Scripts
==================

**StructuralGT** aims to offer optimized graph theoretic analysis code combined with the python ecosystem. For the most part, graph theoretic algorithms are made available, on the python side, via access to the :class:`igraph.Graph` attribute of the :class:`Network` class. Calling methods of the :attr:`Graph` attribute calls an optimized C routine, implemented in `igraph <https://igraph.org/>`__. This section is for users who want to implement their own graph theoretic calculations in C and combine them with analysis in python. A few of these routines have already been implemented in **StrucutralGT**, and can be used as templates. They are made possible because the igraph library allows the user to access the pointer to the underlying C :code:`igraph_t` object. To leverage this in your own code, the following are generally required:

Python Wrapper Method
=====================

This is the called by the user and should be a method of a :class:`Compute` subclass. These methods should create a deep copy of the graph, to pass to the C++ script. The graph is passed to the C++ script via its pointer, which can be accessed from igraph's :meth:`_raw_pointer` method.

Cython Module
=============

All graph pointers are passed to a C++ script via a cython module, which takes the same name as the python wrapper method which generated it, except with a preceding underscore and leading :code:`cast` label, e.g. :code:`_average_nodal_connectivity_cast`. This module is defined in its corresponding :code:`.pyx` file. Although the :code:`.pyx` may vary depending on the module, they have a few things in common. Namely, in these files, a cython extension type which holds a C++ instance as an attribute is created. The cython extension type is called :code:`PyCast` and its C++ instance is called :code:`c_cast`. Finally, the C++ instance holds the graph's pointer as an attribute, called :code:`G_ptr`. This pointer may be accessed from a C++ script, via :code:`c_cast`. Note that the pointer must be cast to a void pointer using `cython's` :code:`PyLong_AsVoidPtr` funtion; using `python's` :code:`PyLong_AsVoidPtr` function will allocate memory incorrectly. 

C++ Script
==========

A copy of the graph may be made in your C++ script with

.. code-block:: c++

    igraph_t* g = (igraph_t*)this->G_ptr

Results from subsequent computations may be passed back to python via attributes of the :code:`c_cast` instance. These steps follow conventional cython usage and are documented in the `cython <https://cython.org/>`__ documentation. This includes creating the necessary header files and adding the module to :code:`setup.py`. Details for the use of **igraph** in your C++ script can be found at the `igraph C <https://igraph.org/c/pdf/latest/igraph-docs.pdf>`__ documentation.

