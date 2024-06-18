from Cython.Build import cythonize
import os
from setuptools import find_packages, setup, Extension
import platform

if platform.system() == 'Windows':
    PREFIX=os.path.join(os.getenv("CONDA_PREFIX"), 'Library')
    extra_obj=os.path.join(PREFIX, 'lib', 'igraph.lib')
    freud='freud-analysis'
else:
    PREFIX=os.getenv("CONDA_PREFIX")
    #PREFIX="/Users/alaink/miniconda3/envs/SGTE-dev/"
    extra_obj="-ligraph"
    freud='freud'

include_dirs = [os.path.join(PREFIX, 'include', 'igraph'),
                os.path.join(PREFIX, 'include', 'eigen3'),]

setup(
    name='StructuralGT',
    packages = find_packages(),
    setup_requires = ["cython"],
    ext_modules=cythonize([
                              Extension(name="StructuralGT._bounded_betweenness_cast",
                              sources=["_bounded_betweenness_cast.pyx"],
                              include_dirs=include_dirs,
                              language="c++",
                              extra_objects=[extra_obj]
                                        ),

                              Extension(name="StructuralGT._random_betweenness_cast",
                              sources=["_random_betweenness_cast.pyx"],
                              include_dirs=include_dirs,
                              language="c++",
                              extra_objects=[extra_obj]
                                        ),

                              Extension(name="StructuralGT._nonlinear_random_betweenness_cast",
                              sources=["_nonlinear_random_betweenness_cast.pyx"],
                              include_dirs=include_dirs,
                              language="c++",
                              extra_objects=[extra_obj]
                                        ),

                              Extension(name="StructuralGT._average_nodal_connectivity_cast",
                              sources=["_average_nodal_connectivity_cast.pyx"],
                              include_dirs=include_dirs,
                              language="c++",
                              extra_objects=[extra_obj]
                                        ),

                              Extension(name="StructuralGT.convert",
                              sources=["convert.pyx"]),

                            ]
                          ),
    zip_safe=False,
    package_data={'StructuralGT':['pytest/data/*/*',]}#'_bounded_betweenness_cast.pyx'],}
                  #'StructuralGT._boundndess_betweenness_cast':['_bounded_betweenneess_cast.pyx']},
)
