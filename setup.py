from Cython.Build import cythonize
from setuptools import find_packages, setup, Extension

import numpy as np


setup(
    name='StructuralGTEdits',
    packages = find_packages(),
    install_requires=[
        'numpy',
        'scipy',
#        'scikit-image',
        'matplotlib',
        'networkx',
        'opencv-python',
        'Pillow',
        'pandas',
        'Cython',
        'gsd',
        'python-igraph',
        'pytest',
        'cmake'
    ],
    setup_requires = ["cython"],
    ext_modules=cythonize([
                              Extension(name="StructuralGTEdits._bounded_betweenness_cast",
                              sources=["_bounded_betweenness_cast.pyx"],
                              language="c++",
                              include_dirs=[np.get_include(),
                                            "/usr/local/include/igraph",],
                                            #"/Users/alaink/miniconda3/bin/../include/c++/v1",],
                              library_dirs=["/usr/local/lib",],
                                            #"/Users/alaink/miniconda3/bin/../include/c++/v1",],
                              extra_objects=["-ligraph"]
                                        ),

                              Extension(name="StructuralGTEdits._random_betweenness_cast",
                              sources=["_random_betweenness_cast.pyx"],
                              language="c++",
                              include_dirs=[np.get_include(),
                                            "/usr/local/include/igraph",
                                            "/usr/local/include/eigen3"],
                                            #"/Users/alaink/miniconda3/bin/../include/c++/v1",],
                              library_dirs=["/usr/local/lib",],
                                            #"/Users/alaink/miniconda3/bin/../include/c++/v1",],
                              extra_objects=["-ligraph"]
                                        ),

                              Extension(name="StructuralGTEdits.convert",
                              sources=["convert.pyx"]),

                            ]
                          ),
    zip_safe=False,
    package_data={'StructuralGTEdits':['pytest/data/*/*',]}#'_bounded_betweenness_cast.pyx'],}
                  #'StructuralGTEdits._boundndess_betweenness_cast':['_bounded_betweenneess_cast.pyx']},
)
