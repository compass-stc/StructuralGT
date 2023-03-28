from Cython.Build import cythonize
import os
from setuptools import find_packages, setup, Extension
import platform

if platform.system() == 'Windows':
    PREFIX=os.path.join(os.getenv("CONDA_PREFIX"), 'Library')
else:
    PREFIX=os.getenv("CONDA_PREFIX")
include_dirs = [os.path.join(PREFIX, 'include', 'igraph'),
                os.path.join(PREFIX, 'include', 'eigen3'),]

setup(
    name='StructuralGTEdits',
    packages = find_packages(),
    install_requires=[
        'numpy',
        'scipy',
        'scikit-image',
        'matplotlib',
        'networkx',
        'opencv-python',
        'Pillow',
        'pandas',
        'Cython',
        'gsd',
        'python-igraph',
        'igraph',
        'eigen',
        'pytest',
        'cmake'
    ],
    setup_requires = ["cython"],
#    ext_modules=cythonize('convert.pyx'))
    ext_modules=cythonize([
                              Extension(name="StructuralGTEdits._bounded_betweenness_cast",
                              sources=["_bounded_betweenness_cast.pyx"],
                              include_dirs=include_dirs,
                              language="c++",
                              extra_objects=["-ligraph"]
                                        ),

                              Extension(name="StructuralGTEdits._random_betweenness_cast",
                              sources=["_random_betweenness_cast.pyx"],
                              include_dirs=include_dirs,
                              language="c++",
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
