# Copyright (c) 2023-2024 The Regents of the University of Michigan.
# This file is from the StructuralGT project, released under the BSD 3-Clause
# License.

#
# This file is from the StructuralGT project, released under the BSD 3-Clause
# License.

#
# This file is from the StructuralGT project, released under the BSD 3-Clause
# License.

#
# This file is from the StructuralGT project, released under the BSD 3-Clause
# License.

import os
import platform

from Cython.Build import cythonize
from setuptools import Extension, find_packages, setup

if platform.system() == "Windows":
    PREFIX = os.path.join(os.getenv("CONDA_PREFIX"), "Library")
    extra_obj = os.path.join(PREFIX, "lib", "igraph.lib")
    freud = "freud-analysis"
else:
    PREFIX = os.getenv("CONDA_PREFIX")
    # PREFIX="/Users/alaink/miniconda3/envs/SGTE-dev/"
    extra_obj = "-ligraph"
    freud = "freud"

include_dirs = [
    os.path.join(PREFIX, "include", "igraph"),
    os.path.join(PREFIX, "include", "eigen3"),
]

setup(
    name="StructuralGT",
    packages=find_packages(),
    setup_requires=["cython"],
    ext_modules=cythonize(
        [
            Extension(
                name="StructuralGT._boundary_betweenness_cast",
                sources=["_boundary_betweenness_cast.pyx"],
                include_dirs=include_dirs,
                language="c++",
                extra_objects=[extra_obj],
            ),
            Extension(
                name="StructuralGT._vertex_boundary_betweenness_cast",
                sources=["_vertex_boundary_betweenness_cast.pyx"],
                include_dirs=include_dirs,
                language="c++",
                extra_objects=[extra_obj],
            ),
            Extension(
                name="StructuralGT._random_boundary_betweenness_cast",
                sources=["_random_boundary_betweenness_cast.pyx"],
                include_dirs=include_dirs,
                language="c++",
                extra_objects=[extra_obj],
            ),
            Extension(
                name="StructuralGT._average_nodal_connectivity_cast",
                sources=["_average_nodal_connectivity_cast.pyx"],
                include_dirs=include_dirs,
                language="c++",
                extra_objects=[extra_obj],
            ),
        ]
    ),
    zip_safe=False,
    package_data={
        "StructuralGT": [
            "pytest/data/*/*",
        ]
    },
)
