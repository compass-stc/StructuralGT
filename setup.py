from Cython.Build import cythonize
from setuptools import find_packages, setup, Extension

ext=cythonize(Extension(name="StructuralGTEdits._bounded_betweenness_cast",
                        sources=["_bounded_betweenness_cast.pyx"],
                        language="c++",
                        include_dirs=["/usr/local/include/igraph",
                                      "/usr/local/include",
                                      "/Users/alaink/miniconda3/bin/../include/c++/v1",
                                      "/Users/alaink/miniconda3/pkgs/numpy-1.24.1-py310h5d7c261_0/lib/python3.10/site-packages/numpy/core/include"],
                        library_dirs=["/usr/local/lib",
                                      "/Users/alaink/miniconda3/bin/../include/c++/v1",
                                      "/Users/alaink/miniconda3/pkgs"],
                        extra_objects=["-ligraph","-ligraph-scg"],
                                libraries=['m'],
                        )
              )

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
        'pytest',
        'cmake'
    ],
    ext_modules=cythonize(ext),
    zip_safe=False,
    package_data={'StructuralGTEdits':['pytest/data/*/*']},
)
