# Copyright (c) 2023-2024 The Regents of the University of Michigan.
# This file is from the StructuralGT project, released under the BSD 3-Clause
# License.

import json
import os
import platform

from Cython.Build import cythonize
from setuptools import Extension, find_packages, setup

metadata = {}
if os.environ.get("C_FLAG") is None or os.environ.get("C_FLAG") == "TRUE":
    metadata['C_FLAG'] = True
elif os.environ.get("C_FLAG") == "FALSE":
    metadata['C_FLAG'] = False
else:
    raise ValueError("Environment variable, C_FLAG, has an invalid value.")
with open('StructuralGT/metadata.json', 'w') as json_file:
    json.dump(metadata, json_file)

if metadata['C_FLAG']:
    if os.getenv("CONDA_PREFIX") is None:
        PRE_PREFIX = os.getenv("MAMBA_ROOT_PREFIX")
    else:
        PRE_PREFIX = os.getenv("CONDA_PREFIX")
    if os.getenv("CONDA_ENVS_PATH") is not None:
        PRE_PREFIX = os.getenv("CONDA_ENVS_PATH")

    if platform.system() == "Windows":
        PREFIX = os.path.join(PRE_PREFIX, "Library")
        extra_obj = os.path.join(PREFIX, "lib", "igraph.lib")
        freud = "freud-analysis"
    else:
        PREFIX = PRE_PREFIX
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
                "metadata.json",
            ]
        },
    )
elif not metadata['C_FLAG']: 
    setup(
        name="StructuralGT",
        packages=find_packages(),
        zip_safe=False,
        package_data={
            "StructuralGT": [
                "pytest/data/*/*",
                "metadata.json",
            ]
        },
    )
